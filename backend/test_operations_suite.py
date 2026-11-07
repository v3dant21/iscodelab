import io,time,uuid
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,text
from pypdf import PdfReader
from test_app import clients,create,pay,payload
from models import User,Order
from menu_rules import scheduled_now
import main


def login_staff(clients,role,outlet=1):
    email=f'{uuid.uuid4()}@example.test'
    with clients['database'].begin() as db: db.add(User(email=email,password=main.hasher.hash('StaffPassword123!'),role=role,outlet_id=outlet))
    client=TestClient(main.app)
    assert client.post('/auth/login',json={'email':email,'password':'StaffPassword123!'}).status_code==200
    client.headers['x-csrf-token']=client.cookies['csrf'];return client


def handoff(clients,order,cash=False):
    for stage in ['PREPARING','READY','HANDED_OFF']:
        r=clients['kondapur'].patch(f"/kitchen/orders/{order['id']}/status",json={'status':stage,'version':order['version'],'cash_collected':cash,'rider_reference':'RIDER-TEST'})
        assert r.status_code==200,r.text
        order=r.json()
    return order


def test_city_schedule_spice_photo(clients):
    admin=clients['admin'];dish=admin.get('/admin/menu-items').json()[0]
    edit={k:dish[k] for k in main.DishInput.model_fields}
    edit.update(city_prices={'HYDERABAD':34900},spice_level='hot',photo_url='https://images.example.com/biryani.jpg',photo_credit='Restaurant photo')
    r=admin.patch('/admin/menu-items/1',json=edit);assert r.status_code==200,r.text
    item=next(x for x in clients['guest'].get('/outlets/1/menu').json() if x['id']==1)
    assert item['price']==34900 and item['spice_level']=='hot' and item['photo_url'].endswith('biryani.jpg')
    assert clients['customer'].post('/checkout/quote',json=payload()).json()['total']==34900
    assert admin.patch('/admin/outlets/1/menu/1',json={'enabled':True,'price':35900}).status_code==200
    assert clients['customer'].post('/checkout/quote',json=payload()).json()['total']==35900
    edit['schedule']=[{'days':[(datetime.now(timezone(timedelta(hours=5,minutes=30))).weekday()+2)%7],'start':'12:00','end':'14:00'}]
    assert admin.patch('/admin/menu-items/1',json=edit).status_code==200
    assert not any(x['id']==1 for x in clients['guest'].get('/outlets/1/menu').json())
    assert clients['customer'].post('/checkout/quote',json=payload()).status_code==409
    assert clients['customer'].post('/checkout/quote',json=payload(routing='auto')).status_code==409
    assert clients['customer'].patch('/admin/menu-items/1',json=edit).status_code==403
    edit['photo_url']='http://localhost/private'
    assert admin.patch('/admin/menu-items/1',json=edit).status_code==422
    edit['photo_url']='';edit['schedule']=[{'days':[0],'start':'12:00','end':'12:00'}]
    assert admin.patch('/admin/menu-items/1',json=edit).status_code==422


def test_overnight_schedule():
    from types import SimpleNamespace
    dish=SimpleNamespace(schedule=[{'days':[4],'start':'19:00','end':'02:00'}]);ist=timezone(timedelta(hours=5,minutes=30))
    assert scheduled_now(dish,datetime(2026,11,6,19,0,tzinfo=ist))
    assert scheduled_now(dish,datetime(2026,11,7,1,59,tzinfo=ist))
    assert not scheduled_now(dish,datetime(2026,11,7,2,0,tzinfo=ist))
    assert not scheduled_now(dish,datetime(2026,11,6,18,59,tzinfo=ist))


def test_loyalty_reserve_refund_invoice(clients):
    c=clients['customer'];first=pay(clients,create(clients)).json()
    assert c.get('/account/loyalty').json()['balance']==0
    done=handoff(clients,first)
    assert done['earned_points']==2 and c.get('/account/loyalty').json()['balance']==2
    assert clients['kondapur'].patch(f"/kitchen/orders/{done['id']}/status",json={'status':'HANDED_OFF','version':done['version']}).status_code==409
    body=payload(redeem_points=2);q=c.post('/checkout/quote',json=body).json()
    assert (q['total'],q['loyalty_credit'],q['payable_total'])==(29900,200,29700)
    reserved=c.post('/orders',json=body).json()
    assert reserved['due']==29700 and c.get('/account/loyalty').json()['balance']==0
    assert c.post('/orders',json=body).json()['id']==reserved['id']
    assert c.post('/orders',json=payload(redeem_points=1)).status_code==409
    url=f"/orders/{reserved['id']}/cancel";reason={'version':reserved['version'],'reason':'Changed my mind'}
    assert c.post(url,json=reason).json()['status']=='CANCELLED'
    assert c.post(url,json=reason).status_code==200
    assert c.get('/account/loyalty').json()['balance']==2
    new=pay(clients,create(clients,redeem_points=2)).json()
    pdf=c.get(f"/orders/{new['id']}/invoice?format=pdf")
    contents=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert 'Loyalty payment credit' in contents and '297.00' in contents
    assert handoff(clients,new)['earned_points']==2
    assert c.get('/account/loyalty').json()['balance']==2
    with clients['database']() as db:
        assert db.get(Order,new['id']).handoff['rider_reference']=='RIDER-TEST'
        assert 'RIDER-TEST' not in str(db.execute(text('SELECT handoff FROM orders WHERE id=:id'),{'id':new['id']}).scalar())


def test_cash_cancellation_reporting(clients):
    c=clients['customer'];order=create(clients,method='cod');staff=clients['kondapur']
    for stage in ['PREPARING','READY']:order=staff.patch(f"/kitchen/orders/{order['id']}/status",json={'status':stage,'version':order['version']}).json()
    assert staff.patch(f"/kitchen/orders/{order['id']}/status",json={'status':'HANDED_OFF','version':order['version']}).status_code==400
    assert c.get('/account/loyalty').json()['balance']==0
    assert staff.patch(f"/kitchen/orders/{order['id']}/status",json={'status':'HANDED_OFF','version':order['version'],'cash_collected':True}).json()['earned_points']==2
    manager=login_staff(clients,'manager');second=pay(clients,create(clients,redeem_points=1)).json()
    body={'version':second['version'],'reason':'Kitchen cannot fulfil'}
    assert c.post(f"/orders/{second['id']}/cancel",json=body).status_code==409
    assert manager.post(f"/manager/orders/{second['id']}/cancel",json=body).json()['payment']=='REFUNDED_TEST'
    assert c.get('/account/loyalty').json()['balance']==2
    report=manager.get('/manager/dashboard?days=30').json();assert len(report['outlets'])==1
    result=report['outlets'][0]
    assert result['cancellations']==1 and result['handoffs']==1 and result['prep_samples']==1
    assert result['average_prep_minutes'] is not None
    assert c.get('/manager/dashboard').status_code==403
    assert len(clients['admin'].get('/manager/dashboard').json()['outlets'])==3


def test_party_notice_privacy_idempotency_and_scope(clients):
    c=clients['customer'];manager=login_staff(clients,'catering_manager');wrong=login_staff(clients,'catering_manager',2)
    body={'key':str(uuid.uuid4()),'outlet_id':1,'event_at':(datetime.now(timezone.utc)+timedelta(hours=49)).isoformat(),'guests':20,'venue':'Private test venue','menu_request':'Vegetarian biryani and starters','dietary_notes':'Please discuss allergens'}
    assert c.post('/party/requests',json=body|{'event_at':(datetime.now(timezone.utc)+timedelta(hours=47)).isoformat()}).status_code==400
    r=c.post('/party/requests',json=body);assert r.status_code==200,r.text
    party=r.json();assert party['status']=='REQUESTED'
    assert c.post('/party/requests',json=body).json()['id']==party['id']
    assert c.post('/party/requests',json=body|{'guests':21}).status_code==409
    assert wrong.get('/catering/requests').json()==[] and c.get('/catering/requests').status_code==403
    decision={'status':'CONFIRMED','note':'Menu and arrival time confirmed by phone','version':0}
    url=f"/catering/requests/{party['id']}"
    assert wrong.patch(url,json=decision).status_code==404
    assert manager.patch(url,json=decision).status_code==200
    assert manager.patch(url,json=decision).status_code==409
    assert c.get('/party/requests').json()[0]['status']=='CONFIRMED'
    with clients['database']() as db:
        raw=db.execute(text('SELECT details,manager_note FROM party_requests')).one()
        assert 'Private test venue' not in str(raw) and 'confirmed by phone' not in str(raw)


def test_concurrent_redemption(clients):
    with clients['database']() as db:
        if db.bind.dialect.name!='postgresql':pytest.skip('Row-lock concurrency requires PostgreSQL')
    c=clients['customer'];handoff(clients,pay(clients,create(clients)).json())
    def redeem(_):
        client=TestClient(main.app);client.cookies.update(c.cookies);client.headers.update(c.headers)
        return client.post('/orders',json=payload(redeem_points=2)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(redeem,[1,2]))
    assert sorted(results)==[200,409] and c.get('/account/loyalty').json()['balance']==0


def test_all_points_order_has_no_cash_charge_or_extra_earnings(clients):
    handoff(clients,pay(clients,create(clients)).json())
    with clients['database'].begin() as db:
        from models import Dish
        db.get(Dish,1).price=100
    c=clients['customer']
    assert c.post('/orders',json=payload(redeem_points=2)).status_code==400
    order=create(clients,redeem_points=1)
    assert order['total']==100 and order['due']==0 and order['payment']=='PAID' and order['status']=='NEW'
    assert handoff(clients,order)['earned_points']==0
    assert c.get('/account/loyalty').json()['balance']==1


def test_repeat_customer_metric_and_blank_catering_reply(clients):
    for _ in range(2): handoff(clients,pay(clients,create(clients)).json())
    data=clients['admin'].get('/manager/dashboard?days=7').json()['outlets'][0]
    assert data['repeat_customers']==1 and data['customers']==1 and data['prep_samples']==2
    assert clients['admin'].patch('/catering/requests/1',json={'status':'CONFIRMED','note':'     ','version':0}).status_code==422
