import time
from urllib.parse import urlparse,parse_qs
from sqlalchemy import select
from test_app import clients
from models import PasswordReset,User
import email_delivery

def test_reset_single_use_revokes_sessions(clients,monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY','test');monkeypatch.setenv('EMAIL_FROM','test@example.test')
    captured=[];monkeypatch.setattr(email_delivery,'send',lambda payload,key:captured.append(payload))
    guest=clients['guest'];body={'email':'customer@demo.test'}
    response=guest.post('/auth/password/forgot',json=body)
    assert response.status_code==200
    assert guest.post('/auth/password/forgot',json=body).json()==response.json()
    assert len(captured)==1
    assert guest.post('/auth/password/forgot',json={'email':'absent@example.test'}).json()==response.json()
    link=captured[0]['text'].split('\n\n')[-1];token=parse_qs(urlparse(link).fragment)['token'][0]
    with clients['database']() as db:
        assert db.scalar(select(PasswordReset)).token_hash!=token
    assert guest.post('/auth/password/reset',json={'token':token,'password':'short'}).status_code==422
    reset={'token':token,'password':'NewUniquePassword456!'}
    assert guest.post('/auth/password/reset',json=reset).status_code==200
    assert clients['customer'].get('/auth/me').status_code==401
    assert guest.post('/auth/password/reset',json=reset).status_code==400
    assert guest.post('/auth/login',json={**body,'password':'DemoPass123!'}).status_code==401
    assert guest.post('/auth/login',json={**body,'password':reset['password']}).status_code==200

def test_reset_unconfigured_expired_and_origin(clients,monkeypatch):
    monkeypatch.delenv('RESEND_API_KEY',raising=False)
    guest=clients['guest']
    assert guest.post('/auth/password/forgot',json={'email':'customer@demo.test'}).status_code==503
    assert guest.post('/auth/password/forgot',json={'email':'customer@demo.test'},headers={'origin':'https://evil.example'}).status_code==403
    import hashlib
    token='x'*43
    with clients['database'].begin() as db:
        user=db.scalar(select(User).where(User.role=='customer'))
        db.add(PasswordReset(token_hash=hashlib.sha256(token.encode()).hexdigest(),user_id=user.id,created=time.time()-3600,expires=time.time()-1))
    assert guest.post('/auth/password/reset',json={'token':token,'password':'NewPassword123!'}).status_code==400
