import json
import time
import uuid
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from test_app import clients, create, pay, payload
from models import Order, Notification, EstimateChange, ConsentRecord, Assignment, Outlet
import main
import prediction
from notifications import overdue, dispatch


def test_auto_routing_stock_and_history_suggestions(clients):
    c=clients['customer']
    clients['kondapur'].patch('/kitchen/menu/1',json={'available':False})
    body=payload(routing='auto', method='cod')
    quote=c.post('/checkout/quote',json=body).json()
    assert quote['outlet_id'] != 1
    order=c.post('/orders',json=body).json()
    assert order['outlet_id']==quote['outlet_id']
    assert order['status']=='NEW'
    assert c.get('/recommendations?outlet_id=1').json()==[]
    suggested=c.get(f"/recommendations?outlet_id={order['outlet_id']}").json()
    assert suggested[0]['id']==1
    assert len(c.get('/orders').json())==1
    assert c.post('/orders',json=payload(outlet_id=1,method='cod')).status_code==409


def test_uncapped_promise_and_manager_audit_alert_dedup(clients,tmp_path,monkeypatch):
    p=tmp_path/'model.json';p.write_text(json.dumps({'intercept':240,'coefficients':[0]*6}))
    monkeypatch.setattr(prediction,'MODEL_PATH',p)
    order=create(clients,method='cod')
    assert order['minutes']==240
    path=f"/manager/orders/{order['id']}/estimate"
    body={'minutes':260,'reason':'Kitchen needs more time','version':order['version']}
    assert clients['kondapur'].patch(path,json=body).status_code==403
    assert clients['admin'].patch(path,json={**body,'minutes':239}).status_code==400
    updated=clients['admin'].patch(path,json=body).json()
    assert updated['minutes']==260
    assert updated['original_promise']==order['original_promise']
    assert clients['admin'].patch(path,json=body).status_code==409
    now=time.time()
    with clients['database'].begin() as db:
        saved=db.get(Order,order['id']);saved.original_promise=now-601
    with clients['database'].begin() as db: overdue(db,now)
    with clients['database'].begin() as db: overdue(db,now+5)
    with clients['database']() as db:
        assert db.scalar(select(func.count()).select_from(EstimateChange))==1
        assert db.scalar(select(func.count()).select_from(Notification).where(Notification.event_key.like('%:late:%')))==2
    notices=clients['customer'].get('/notifications').json()
    assert any('manager has been alerted' in n['message'] for n in notices)
    assert len(clients['admin'].get('/notifications').json())==1


def test_ready_order_does_not_raise_prep_delay(clients):
    order=create(clients,method='cod')
    with clients['database'].begin() as db:
        saved=db.get(Order,order['id']);saved.status='READY';saved.original_promise=time.time()-1000
    with clients['database'].begin() as db: overdue(db)
    assert clients['admin'].get('/notifications').json()==[]


def test_service_consent_marketing_and_licence(clients):
    c=clients['customer']
    assert c.get('/auth/me').json()['marketing_opt_in'] is False
    updates={'channel':'sms','phone':'+919876543210','consent':False}
    assert c.post('/orders',json=payload(updates=updates)).status_code==400
    order=create(clients,method='cod',updates={**updates,'consent':True})
    assert c.get('/auth/me').json()['marketing_opt_in'] is False
    n=c.get('/notifications').json()[0]
    assert n['channel']=='sms' and n['state']=='pending'
    assert 'recipient' not in n
    assert c.patch('/account/marketing-consent',json={'granted':True}).json()['marketing_opt_in'] is True
    assert c.patch('/account/marketing-consent',json={'granted':False}).json()['marketing_opt_in'] is False
    with clients['database']() as db: assert db.scalar(select(func.count()).select_from(ConsentRecord))==2
    assert c.patch('/admin/outlets/1/licence',json={'fssai':'12345678901234'}).status_code==403
    assert clients['admin'].patch('/admin/outlets/1/licence',json={'fssai':'short'}).status_code==422
    assert clients['admin'].patch('/admin/outlets/1/licence',json={'fssai':'12345678901234'}).status_code==200
    assert clients['guest'].get('/outlets?lat=17.462&lng=78.357').json()[0]['fssai']=='12345678901234'


def test_bridge_not_delivered_and_failure_is_retryable(clients,monkeypatch):
    order=create(clients,method='cod',updates={'channel':'whatsapp','phone':'+919876543210','consent':True})
    monkeypatch.delenv('NOTIFICATION_WEBHOOK_URL',raising=False)
    with clients['database'].begin() as db: dispatch(db)
    assert clients['customer'].get('/notifications').json()[0]['state']=='pending'
    monkeypatch.setenv('NOTIFICATION_WEBHOOK_URL','https://provider-bridge.example.test/order-events')
    monkeypatch.setenv('NOTIFICATION_WEBHOOK_SECRET','test-secret')
    captured=[]
    class Reply:
        status=202
        def __enter__(self):return self
        def __exit__(self,*a):pass
    def send(request,timeout):
        captured.append(request)
        return Reply()
    monkeypatch.setattr('urllib.request.build_opener',lambda *args:SimpleNamespace(open=send))
    with clients['database'].begin() as db: dispatch(db)
    with clients['database'].begin() as db: dispatch(db)
    assert len(captured)==1
    assert captured[0].get_header('Idempotency-key')
    assert captured[0].get_header('X-signature-sha256')
    assert clients['customer'].get('/notifications').json()[0]['state']=='submitted'


@pytest.mark.skipif(not __import__('os').environ.get('TEST_DATABASE_URL'),reason='PostgreSQL load smoke check')
def test_peak_order_intake_smoke(clients):
    durations=[]
    def place(i):
        start=time.monotonic()
        result=clients['customer'].post('/orders',json=payload(method='cod',outlet_id=i%3+1))
        durations.append(time.monotonic()-start)
        assert result.status_code==200,result.text
        return result.json()['id']
    start=time.monotonic()
    with ThreadPoolExecutor(max_workers=8) as pool: ids=list(pool.map(place,range(120)))
    elapsed=time.monotonic()-start
    assert len(set(ids))==120
    p95=sorted(durations)[int(len(durations)*.95)-1]
    print(f'\nLOCAL SMOKE: 120 confirmed orders / {elapsed:.2f}s; p95 {p95:.3f}s; no failures. Not a production capacity certification.')


def test_changed_quote_requires_new_confirmation(clients):
    body=payload(method='cod',expected_total=1,expected_outlet=1)
    assert clients['customer'].post('/orders',json=body).status_code==409
    assert clients['customer'].get('/orders').json()==[]


def test_failed_bridge_retains_notice_and_backoff(clients,monkeypatch):
    create(clients,method='cod',updates={'channel':'sms','phone':'+919876543210','consent':True})
    monkeypatch.setenv('NOTIFICATION_WEBHOOK_URL','https://provider-bridge.example.test/order-events')
    monkeypatch.setenv('NOTIFICATION_WEBHOOK_SECRET','test-secret')
    def fail_send(*args,**kwargs): raise TimeoutError()
    monkeypatch.setattr('urllib.request.build_opener',lambda *args:SimpleNamespace(open=fail_send))
    with clients['database'].begin() as db: dispatch(db,now=1000)
    with clients['database']() as db:
        n=db.scalar(select(Notification));assert n.state=='pending' and n.attempts==1 and n.next_attempt>1000
    with clients['database'].begin() as db: dispatch(db,now=1001)
    with clients['database']() as db: assert db.scalar(select(Notification)).attempts==1
