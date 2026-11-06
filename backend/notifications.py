"""Durable in-app notices and provider-neutral outbound integration queue."""
import hashlib
import hmac
import json
import os
import time
import urllib.request
from sqlalchemy import select
from models import Notification, Order


def enqueue(connection, order, kind, message, audience='customer'):
    key = f'{order.id}:{kind}:{audience}'
    if connection.scalar(select(Notification.id).where(Notification.event_key == key)): return
    preferences = order.request.get('updates') or {}
    channel = preferences.get('channel', 'in_app') if audience == 'customer' else 'in_app'
    recipient = preferences.get('phone') if channel != 'in_app' else None
    connection.add(Notification(event_key=key, order_id=order.id, user_id=order.user_id if audience=='customer' else None,
        outlet_id=order.outlet_id, audience=audience, message=message, channel=channel, recipient=recipient,
        state='in_app' if channel=='in_app' else 'pending', created=time.time(), attempts=0, next_attempt=0))


def overdue(connection, now=None):
    now = time.time() if now is None else now
    orders = connection.scalars(select(Order).where(Order.status.in_(['NEW','PREPARING']), Order.original_promise <= now-600,
        Order.late_alerted.is_(None)).with_for_update(skip_locked=True))
    for order in orders:
        order.late_alerted = now
        enqueue(connection, order, 'late', f'Order #{order.id} is more than 10 minutes past its original preparation promise. The kitchen manager has been alerted. We will update your estimate.')
        enqueue(connection, order, 'late', f'Order #{order.id} is overdue by at least 10 minutes. Please review preparation and update the customer estimate.', 'manager')


def dispatch(connection, now=None):
    """The configured HTTPS bridge must honor Idempotency-Key and report real delivery separately.

    HTTP acceptance is recorded as submitted, never delivered. Retries stop visibly at failed.
    No provider configured means notices remain pending, still visible inside the app.
    """
    url, secret = os.getenv('NOTIFICATION_WEBHOOK_URL',''), os.getenv('NOTIFICATION_WEBHOOK_SECRET','')
    if not url or not secret: return
    if not url.startswith('https://'): raise ValueError('Notification bridge must use HTTPS')
    now = time.time() if now is None else now
    notice = connection.scalar(select(Notification).where(Notification.state=='pending', Notification.next_attempt<=now)
        .order_by(Notification.id).with_for_update(skip_locked=True).limit(1))
    if not notice: return
    payload = json.dumps({'id':notice.event_key,'channel':notice.channel,'to':notice.recipient,'text':notice.message},sort_keys=True).encode()
    signature = hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest()
    notice.attempts += 1
    try:
        request = urllib.request.Request(url,data=payload,headers={'Content-Type':'application/json','Idempotency-Key':notice.event_key,'X-Signature-SHA256':signature},method='POST')
        # Do not follow redirects with recipient data or signatures.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs): return None
        with urllib.request.build_opener(NoRedirect).open(request,timeout=5) as response:
            if not 200 <= response.status < 300: raise ValueError('Provider bridge rejected notification')
        notice.state='submitted'
    except Exception:
        notice.state='failed' if notice.attempts >= 8 else 'pending'
        notice.next_attempt=now+min(3600,30*2**notice.attempts)
    return True
