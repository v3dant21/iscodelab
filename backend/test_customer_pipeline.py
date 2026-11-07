import base64, hashlib, io
from urllib.parse import urlparse, parse_qs
from sqlalchemy import text, select
from pypdf import PdfReader
from test_app import clients, create, pay, payload
from models import User, Order, Invoice, EmailDelivery, EmailVerification
import email_delivery
import main

def register(clients, email='person@example.test'):
    c=clients['guest']
    r=c.post('/auth/register',json={'email':email,'password':'SomeLongPassword123!','name':'Asha Kumar','phone':'+919876543210'})
    assert r.status_code==200,r.text
    c.headers['x-csrf-token']=c.cookies['csrf']
    return c,r.json()

def test_private_fields_and_login_matching(clients):
    c,profile=register(clients,'Person@Example.test')
    assert profile['email']=='person@example.test' and profile['profile_complete']
    with clients['database']() as db:
        row=db.execute(text('SELECT email,name,phone,email_hash,phone_hash,password FROM users WHERE id=:id'),{'id':profile['id']}).mappings().one()
        assert all(row[k].startswith('enc:v1:') for k in ('email','name','phone'))
        assert len(row['email_hash'])==len(row['phone_hash'])==64
        assert row['password'].startswith('$argon2')
        assert all(v not in str(row) for v in ['person@example.test','Asha','+919876543210','SomeLongPassword123!'])
        outbox=db.scalar(select(EmailDelivery).where(EmailDelivery.user_id==profile['id']))
        raw=db.execute(text('SELECT recipient,payload FROM email_deliveries WHERE id=:id'),{'id':outbox.id}).one()
        assert 'person@example.test' not in str(raw) and 'token=' not in str(raw)
    assert c.post('/auth/login',json={'email':'PERSON@example.test','password':'SomeLongPassword123!'}).status_code==200
    assert c.post('/auth/register',json={'email':'PERSON@example.test','password':'SomeLongPassword123!','name':'Another','phone':'+919876543210'}).status_code==409

def test_order_requires_profile_snapshot_and_pdf_owner(clients):
    with clients['database'].begin() as db:
        db.scalar(select(User).where(User.role=='customer')).name=None
    assert clients['customer'].post('/orders',json=payload()).status_code==409
    c=clients['customer']
    assert c.patch('/account/profile',json={'name':'  ','phone':'+919876543210'}).status_code==422
    assert c.patch('/account/profile',json={'name':'Asha Kumar','phone':'+919876543210'}).status_code==200
    o=create(clients);assert pay(clients,o).status_code==200
    c.patch('/account/profile',json={'name':'New Name','phone':'+919876543211'})
    with clients['database']() as db:
        assert db.get(Order,o['id']).contact['name']=='Asha Kumar'
        raw=db.execute(text('SELECT request,contact FROM orders WHERE id=:id'),{'id':o['id']}).one()
        assert 'Test flat' not in str(raw) and 'Asha' not in str(raw)
        assert 'Asha' not in str(db.execute(text('SELECT document FROM invoices WHERE order_id=:id'),{'id':o['id']}).one())
        assert db.scalar(select(EmailDelivery).where(EmailDelivery.order_id==o['id'])).state=='awaiting_verification'
    url=f"/orders/{o['id']}/invoice?format=pdf"
    response=c.get(url);assert response.status_code==200 and response.content.startswith(b'%PDF-')
    assert response.headers['content-type']=='application/pdf' and 'private' in response.headers['cache-control']
    assert c.get(url).content == response.content
    assert 'Asha Kumar' in PdfReader(io.BytesIO(response.content)).pages[0].extract_text()
    other,_=register(clients)
    assert other.get(url).status_code==404 and other.get(f"/orders/{o['id']}").status_code==404
    assert other.get('/account/email-status').json()['items']==[]

def test_verification_single_use_and_releases_mail(clients):
    c,user=register(clients)
    o=c.post('/orders',json=payload()).json()
    assert c.post(f"/payments/mock/{o['id']}/complete",json={'event':'verification-test-1234','success':True}).status_code==200
    with clients['database']() as db:
        job=db.scalar(select(EmailDelivery).where(EmailDelivery.user_id==user['id'],EmailDelivery.kind=='verify'))
        token=parse_qs(urlparse(job.payload['link']).fragment)['token'][0]
        assert db.get(EmailVerification,hashlib.sha256(token.encode()).hexdigest())
    assert c.post('/auth/email/verify',json={'token':token},headers={'origin':'https://evil.example'}).status_code==403
    assert c.post('/auth/email/verify',json={'token':token},headers={'origin':main.origin}).status_code==200
    assert c.post('/auth/email/verify',json={'token':token},headers={'origin':main.origin}).status_code==400
    assert c.get('/auth/me').json()['email_verified']
    with clients['database']() as db:assert db.scalar(select(EmailDelivery).where(EmailDelivery.order_id==o['id'])).state=='pending'

def test_email_disabled_then_retry_and_pdf_attachment(clients,monkeypatch):
    with clients['database'].begin() as db:db.scalar(select(User).where(User.role=='customer')).email_verified=True
    o=create(clients);assert pay(clients,o).status_code==200
    monkeypatch.delenv('RESEND_API_KEY',raising=False)
    with clients['database'].begin() as db:assert email_delivery.dispatch_email(db) is False
    monkeypatch.setenv('RESEND_API_KEY','test-key');monkeypatch.setenv('EMAIL_FROM','orders@example.test')
    def fail(*args):raise TimeoutError()
    monkeypatch.setattr(email_delivery,'send',fail)
    with clients['database'].begin() as db:assert email_delivery.dispatch_email(db,now=1000)
    with clients['database']() as db:
        job=db.scalar(select(EmailDelivery).where(EmailDelivery.order_id==o['id']))
        assert job.state=='pending' and job.attempts==1 and job.next_attempt==1060
    received=[]
    def send(body,key):received.append((body,key));return 'provider-123'
    monkeypatch.setattr(email_delivery,'send',send)
    with clients['database'].begin() as db:assert email_delivery.dispatch_email(db,now=1061)
    with clients['database'].begin() as db:assert not email_delivery.dispatch_email(db,now=1062)
    assert len(received)==1 and received[0][1]==f"order:{o['id']}:confirmed"
    assert f"/orders/{o['id']}" in received[0][0]['text']
    assert base64.b64decode(received[0][0]['attachments'][0]['content']).startswith(b'%PDF-')
    with clients['database']() as db:
        job=db.scalar(select(EmailDelivery).where(EmailDelivery.order_id==o['id']))
        assert job.state=='submitted' and job.provider_id=='provider-123'
    assert pay(clients,o,event='different-payment-event').status_code==409

def test_verification_expiry_and_resend_cooldown(clients):
    c,user=register(clients)
    for _ in range(4):assert c.post('/auth/email/request-verification').status_code==200
    with clients['database'].begin() as db:
        jobs=list(db.scalars(select(EmailDelivery).where(EmailDelivery.user_id==user['id'])))
        assert len(jobs)==1
        token=parse_qs(urlparse(jobs[0].payload['link']).fragment)['token'][0]
        db.get(EmailVerification,hashlib.sha256(token.encode()).hexdigest()).expires=1
    assert c.post('/auth/email/verify',json={'token':token},headers={'origin':main.origin}).status_code==400
