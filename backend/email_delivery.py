"""Transactional email outbox. No provider configured means no attempted delivery."""
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.request
from urllib.parse import quote
from sqlalchemy import select
from models import EmailDelivery, EmailVerification, Invoice, User
from billing import render_pdf


def configured():
    return bool(os.getenv('RESEND_API_KEY') and os.getenv('EMAIL_FROM'))


def website():
    url = os.environ.get('APP_ORIGIN', 'http://localhost:3000').rstrip('/')
    if not url.startswith('https://') and url != 'http://localhost:3000':
        raise ValueError('Email links require an HTTPS website origin')
    return url


def verification(connection, user):
    now = time.time()
    last = connection.scalar(select(EmailDelivery).where(EmailDelivery.user_id==user.id, EmailDelivery.kind=='verify').order_by(EmailDelivery.id.desc()))
    if last and last.created > now - 60:
        return
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    connection.add(EmailVerification(token_hash=token_hash, user_id=user.id, expires=now+86400))
    # Fragment keeps the secret out of web access logs and Referer headers.
    connection.add(EmailDelivery(event_key='verify:'+token_hash, user_id=user.id, kind='verify', recipient=user.email,
        payload={'link':website()+'/verify-email#token='+quote(token), 'expires':now+86400}, created=now))


def order_email(connection, order, user):
    key = f'order:{order.id}:confirmed'
    if not connection.scalar(select(EmailDelivery.id).where(EmailDelivery.event_key==key)):
        connection.add(EmailDelivery(event_key=key,user_id=user.id,order_id=order.id,kind='order',recipient=user.email,
            payload={'link':website()+f'/orders/{order.id}'},created=time.time(),state='pending' if user.email_verified else 'awaiting_verification'))


def send(payload, key):
    request = urllib.request.Request('https://api.resend.com/emails',data=json.dumps(payload).encode(),headers={
        'Authorization':'Bearer '+os.environ['RESEND_API_KEY'],'Content-Type':'application/json','Idempotency-Key':key},method='POST')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    with urllib.request.build_opener(NoRedirect).open(request,timeout=8) as response:
        if response.status not in (200,201,202): raise ValueError('Email provider rejected submission')
        identifier=json.loads(response.read()).get('id')
        if not identifier: raise ValueError('Email provider returned no message ID')
        return identifier


def dispatch_email(connection, now=None):
    if not configured(): return False
    now = time.time() if now is None else now
    item=connection.scalar(select(EmailDelivery).where(EmailDelivery.state=='pending',EmailDelivery.next_attempt<=now).order_by(EmailDelivery.id).with_for_update(skip_locked=True).limit(1))
    if not item: return False
    user=connection.get(User,item.user_id)
    if item.kind=='order' and not user.email_verified:
        item.state='awaiting_verification'; return True
    if item.kind=='verify' and (user.email_verified or item.payload['expires']<=now):
        item.state='expired'; return True
    payload={'from':os.environ['EMAIL_FROM'],'to':[item.recipient]}
    if item.kind=='verify':
        payload.update(subject='Verify your DumHouse email',text='Confirm your email to receive order updates and invoices. This link expires in 24 hours.\n\n'+item.payload['link']+'\n\nIf you did not create this account, ignore this email.')
    else:
        invoice=connection.get(Invoice,item.order_id)
        if not invoice:
            item.state='failed'; return True
        payload.update(subject=f'DumHouse order #{item.order_id} confirmed',text='Your order is confirmed. Sign in to your account to track preparation:\n'+item.payload['link']+'\n\nYour sample invoice PDF is attached. This order uses test payments; this is not a valid tax invoice.',attachments=[{'filename':invoice.document['number']+'.pdf','content':base64.b64encode(render_pdf(invoice.document)).decode()}])
    item.attempts+=1
    try:
        item.provider_id=send(payload,item.event_key)
        item.state='submitted'  # Acceptance is not proof of inbox delivery.
        item.payload={}  # Verification tokens no longer needed after submission.
    except Exception:
        item.state='failed' if item.attempts>=8 else 'pending'
        item.next_attempt=now+min(3600,30*2**item.attempts)
    return True
