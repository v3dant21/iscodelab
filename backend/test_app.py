import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
import main
import prediction
import seed
from models import Base, Order, Outlet


@pytest.fixture()
def clients(tmp_path, monkeypatch):
    url = os.environ.get('TEST_DATABASE_URL', f'sqlite:///{tmp_path}/test.db')
    if not url.startswith('sqlite:') and not (make_url(url).database or '').endswith('_test'):
        raise ValueError('Integration tests require a database name ending in _test.')
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine)
    monkeypatch.setattr(seed, 'SessionLocal', sessions)
    monkeypatch.setenv('ALLOW_MOCK_PAYMENTS', 'true')
    seed.seed()
    def database():
        with sessions() as connection:
            yield connection
    main.app.dependency_overrides[main.database] = database
    accounts = {}
    for name in ('customer', 'kondapur', 'gachibowli', 'admin'):
        client = TestClient(main.app)
        response = client.post('/auth/login', json={'email': f'{name}@demo.test', 'password': 'DemoPass123!'})
        assert response.status_code == 200
        client.headers['x-csrf-token'] = client.cookies['csrf']
        accounts[name] = client
    accounts['guest'] = TestClient(main.app)
    accounts['database'] = sessions
    yield accounts
    main.app.dependency_overrides.clear()
    engine.dispose()


def payload(**changes):
    return {'lat': 17.462, 'lng': 78.357, 'address': 'Test flat in Kondapur', 'outlet_id': 1, 'method': 'upi', 'key': str(uuid.uuid4()), 'lines': [{'dish_id': 1, 'quantity': 1, 'portion': 'regular', 'addon': False}]} | changes


def create(clients, **changes):
    response = clients['customer'].post('/orders', json=payload(**changes))
    assert response.status_code == 200, response.text
    return response.json()


def pay(clients, order, success=True, event=None):
    return clients['customer'].post(f"/payments/mock/{order['id']}/complete", json={'success': success, 'event': event or str(uuid.uuid4())})


def test_nearest_and_manual_outlet(clients):
    outlets = clients['guest'].get('/outlets?lat=17.462&lng=78.357').json()
    assert outlets[0]['id'] == 1
    assert len(outlets) == 3
    assert create(clients, outlet_id=2)['outlet_id'] == 2
    assert clients['guest'].get('/outlets?lat=0&lng=0').json() == []
    assert clients['customer'].post('/orders', json=payload(lat=0, lng=0)).status_code == 409


def test_server_prices_and_options(clients):
    body = payload(lines=[{'dish_id': 1, 'quantity': 2, 'portion': 'large', 'addon': True}])
    quote = clients['customer'].post('/checkout/quote', json=body).json()
    assert quote['total'] == 89800
    body['lines'][0]['price'] = 1
    assert clients['customer'].post('/orders', json=body).status_code == 422
    body['lines'][0].pop('price')
    body['lines'][0]['portion'] = 'fake'
    assert clients['customer'].post('/orders', json=body).status_code == 400


def test_checkout_idempotency(clients):
    body = payload()
    first = clients['customer'].post('/orders', json=body).json()
    assert clients['customer'].post('/orders', json=body).json()['id'] == first['id']
    body['address'] = 'Changed delivery address'
    assert clients['customer'].post('/orders', json=body).status_code == 409


def test_failed_payment_retry_and_replays(clients):
    order = create(clients)
    event = str(uuid.uuid4())
    assert pay(clients, order, False, event).json()['status'] == 'PENDING_PAYMENT'
    assert clients['kondapur'].get('/kitchen/orders').json() == []
    assert pay(clients, order, True, event).status_code == 409
    success = str(uuid.uuid4())
    accepted = pay(clients, order, True, success).json()
    assert accepted['status'] == 'NEW' and accepted['minutes'] >= 20
    assert pay(clients, order, True, success).json()['version'] == accepted['version']
    assert pay(clients, create(clients), True, success).status_code == 409
    assert len(clients['kondapur'].get('/kitchen/orders').json()) == 1


def test_stockout_revalidation(clients):
    order = create(clients)
    assert clients['kondapur'].patch('/kitchen/menu/1', json={'available': False}).status_code == 200
    assert 1 not in [dish['id'] for dish in clients['guest'].get('/outlets/1/menu').json()]
    assert pay(clients, order).status_code == 409
    assert clients['customer'].post('/orders', json=payload()).status_code == 409
    assert 1 in [dish['id'] for dish in clients['guest'].get('/outlets/2/menu').json()]


def test_price_change_and_immutable_snapshot(clients):
    order = create(clients)
    assert clients['admin'].patch('/admin/outlets/1/menu/1', json={'enabled': True, 'price': 35000}).status_code == 200
    assert pay(clients, order).status_code == 409
    assert clients['customer'].get(f"/orders/{order['id']}").json()['total'] == 29900
    assert create(clients)['total'] == 35000


def test_outlet_closes_before_payment(clients):
    order = create(clients)
    with clients['database'].begin() as connection:
        connection.get(Outlet, 1).opened = False
    assert pay(clients, order).status_code == 409


def test_roles_csrf_and_registration(clients):
    assert clients['guest'].get('/orders').status_code == 401
    assert clients['customer'].get('/kitchen/orders').status_code == 403
    assert clients['admin'].get('/orders').status_code == 403
    client = clients['customer']
    client.headers.pop('x-csrf-token')
    assert client.post('/orders', json=payload()).status_code == 403
    guest = clients['guest']
    assert guest.post('/auth/register', json={'email': 'new@example.test', 'password': 'DemoPass123!', 'role': 'admin'}).status_code == 422
    response = guest.post('/auth/register', json={'email': 'new@example.test', 'password': 'DemoPass123!'})
    assert response.json()['role'] == 'customer'
    guest.headers['x-csrf-token'] = guest.cookies['csrf']
    assert guest.post('/orders', json=payload(method='cod')).status_code == 403
    assert guest.post('/auth/logout').status_code == 200
    assert guest.get('/auth/me').status_code == 401


def test_order_owner_and_kitchen_isolation(clients):
    order = pay(clients, create(clients)).json()
    guest = clients['guest']
    guest.post('/auth/register', json={'email': 'other@example.test', 'password': 'DemoPass123!'})
    guest.headers['x-csrf-token'] = guest.cookies['csrf']
    assert guest.get(f"/orders/{order['id']}").status_code == 404
    assert guest.post(f"/payments/mock/{order['id']}/complete", json={'event': str(uuid.uuid4()), 'success': True}).status_code == 404
    assert clients['gachibowli'].get('/kitchen/orders').json() == []
    assert clients['gachibowli'].patch(f"/kitchen/orders/{order['id']}/status", json={'status': 'PREPARING', 'version': order['version']}).status_code == 409


def test_transitions_and_stale_write(clients):
    order = pay(clients, create(clients)).json()
    path = f"/kitchen/orders/{order['id']}/status"
    staff = clients['kondapur']
    assert staff.patch(path, json={'status': 'READY', 'version': order['version']}).status_code == 409
    preparing = staff.patch(path, json={'status': 'PREPARING', 'version': order['version']}).json()
    assert staff.patch(path, json={'status': 'READY', 'version': order['version']}).status_code == 409
    ready = staff.patch(path, json={'status': 'READY', 'version': preparing['version']}).json()
    assert staff.patch(path, json={'status': 'HANDED_OFF', 'version': ready['version']}).json()['status'] == 'HANDED_OFF'
    assert staff.get('/kitchen/orders').json() == []


def test_cod_and_deposit(clients):
    assert create(clients, method='cod')['payment'] == 'COD_DUE'
    order = create(clients, method='cod', lines=[{'dish_id': 1, 'quantity': 6}])
    assert order['status'] == 'PENDING_PAYMENT' and order['due'] == 35880
    assert pay(clients, order).json()['payment'] == 'DEPOSIT_PAID'


def test_mock_gate(clients, monkeypatch):
    order = create(clients)
    monkeypatch.setenv('ALLOW_MOCK_PAYMENTS', 'false')
    assert pay(clients, order).status_code == 403


def test_admin_catalog_and_assignment(clients):
    body = {'name': 'New test dish', 'description': 'A test dish description', 'category': 'Sides', 'price': 10000, 'veg': True, 'allergens': '', 'weight': 5, 'options': {'regular': 0}}
    assert clients['kondapur'].post('/admin/menu-items', json=body).status_code == 403
    dish = clients['admin'].post('/admin/menu-items', json=body).json()
    assert clients['admin'].patch(f"/admin/outlets/1/menu/{dish['id']}", json={'enabled': True, 'price': None}).status_code == 200
    assert dish['id'] in [item['id'] for item in clients['guest'].get('/outlets/1/menu').json()]
    clients['admin'].patch(f"/admin/outlets/1/menu/{dish['id']}", json={'enabled': False, 'price': None})
    assert clients['kondapur'].patch(f"/kitchen/menu/{dish['id']}", json={'available': True}).status_code == 404


def test_prediction_fallback_and_distance(tmp_path, monkeypatch):
    monkeypatch.setattr(prediction, 'MODEL_PATH', tmp_path / 'missing.json')
    minutes, source = prediction.predict([{'quantity': 2, 'weight': 10}], 3, 20, False)
    assert minutes == 33 and source == 'queue fallback'
    assert main.distance(17.462, 78.357, Outlet(lat=17.462, lng=78.357)) == 0


@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'), reason='Requires PostgreSQL row locks')
def test_concurrent_checkout_and_payment(clients):
    body = payload(method='cod')
    def checkout(_):
        return clients['customer'].post('/orders', json=body)
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(checkout, range(2)))
    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json()['id'] == responses[1].json()['id']
    order = create(clients)
    event = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: pay(clients, order, event=event), range(2)))
    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json()['version'] == responses[1].json()['version'] == 1


def test_meal_specific_addons(clients):
    for dish_id in (4, 5, 6):
        response = clients['customer'].post('/checkout/quote', json=payload(lines=[{'dish_id': dish_id, 'quantity': 1, 'portion': 'regular', 'addon': True}]))
        assert response.status_code == 400


def test_google_setup_and_identity(clients, monkeypatch):
    guest = clients['guest']
    monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)
    assert guest.get('/auth/google/config').json()['client_id'] == ''
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client')
    config = guest.get('/auth/google/config').json()
    body = {'credential': 'signed-token', 'nonce': config['nonce']}
    claims = {'sub': 'google-123', 'email': 'new@gmail.com', 'email_verified': True, 'nonce': config['nonce']}
    monkeypatch.setattr(main, 'verify_google_token', lambda token, audience: claims)
    assert guest.post('/auth/google', json=body).status_code == 403
    headers = {'origin': main.origin}
    wrong = body | {'nonce': 'wrong-nonce-long-enough'}
    assert guest.post('/auth/google', json=wrong, headers=headers).status_code == 403
    response = guest.post('/auth/google', json=body, headers=headers)
    assert response.status_code == 200
    user_id = response.json()['id']
    assert response.json()['role'] == 'customer'
    assert response.json()['cod'] is False
    assert guest.get('/auth/me').json()['id'] == user_id
    assert guest.post('/auth/google', json=body, headers=headers).status_code == 403
    config = guest.get('/auth/google/config').json()
    claims['nonce'] = config['nonce']
    body['nonce'] = config['nonce']
    assert guest.post('/auth/google', json=body, headers=headers).json()['id'] == user_id


def test_google_rejects_unverified_and_existing_accounts(clients, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client')
    guest = clients['guest']
    nonce = guest.get('/auth/google/config').json()['nonce']
    body = {'credential': 'signed-token', 'nonce': nonce}
    claims = {'sub': 'another-sub', 'email': 'admin@demo.test', 'email_verified': True, 'nonce': nonce}
    monkeypatch.setattr(main, 'verify_google_token', lambda token, audience: claims)
    headers = {'origin': main.origin}
    assert guest.post('/auth/google', json=body, headers=headers).status_code == 409
    claims['email_verified'] = False
    assert guest.post('/auth/google', json=body, headers=headers).status_code == 401
    claims['nonce'] = 'incorrect'
    assert guest.post('/auth/google', json=body, headers=headers).status_code == 401


def test_reference_catalog_import_is_idempotent_and_preserves_stock(clients):
    from reference_menu import extend_menu
    from models import Assignment, Dish
    guest = clients['guest']
    catalog = guest.get('/catalog').json()
    assert len(catalog) == 70
    assert sum(dish['veg'] for dish in catalog) == 35
    assert len({dish['name'] for dish in catalog}) == 70
    naan = next(dish for dish in catalog if dish['name'] == 'Garlic Naan')
    assert naan['price'] == 7900 and naan['veg']
    handi = next(dish for dish in catalog if dish['name'] == 'Chicken Handi Biryani')
    assert handi['options'] == {'handi (2 people)': 0}
    with clients['database'].begin() as database:
        assignment = database.get(Assignment, (1, naan['id']))
        assignment.available = False
        assignment.price = 8500
    with clients['database'].begin() as database:
        assert extend_menu(database) == 0
        assignment = database.get(Assignment, (1, naan['id']))
        assert assignment.available is False and assignment.price == 8500
    assert any(item['id'] == naan['id'] for item in guest.get('/catalog').json())
    assert not any(item['id'] == naan['id'] for item in guest.get('/outlets/1/menu').json())


def test_demo_invoice_access_snapshot_and_totals(clients):
    from models import Invoice
    order = create(clients, address='<script>alert(1)</script> flat')
    path = f"/orders/{order['id']}/invoice"
    assert clients['customer'].post(path).status_code == 409
    assert pay(clients, order).status_code == 200
    response = clients['customer'].get(path)
    assert response.status_code == 200
    assert 'NOT VALID FOR TAX PURPOSES' in response.text
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;' in response.text
    assert response.headers['cache-control'] == 'private, no-store'
    assert clients['guest'].get(path).status_code == 401
    assert clients['kondapur'].get(path).status_code == 404
    assert clients['kondapur'].post(path).status_code == 404
    assert clients['customer'].post(path).status_code == 200
    assert clients['customer'].get(path).text == response.text
    assert 'attachment' in clients['customer'].get(path+'?download=true').headers['content-disposition']
    with clients['database']() as session:
        doc = session.get(Invoice, order['id']).document
        assert doc['total'] == doc['taxable'] + doc['cgst'] + doc['sgst'] + doc['rounding']
        assert doc['total'] == sum(x['gross'] for x in doc['lines'])
        assert doc['paid'] == doc['total']
        saved = session.get(Order, order['id'])
        saved.lines = []
        session.commit()
    assert clients['customer'].get(path).text == response.text


def test_demo_invoice_cod_deposit_and_rounding(clients):
    from models import Invoice
    from billing import snapshot
    from types import SimpleNamespace
    order = create(clients, method='cod', lines=[{'dish_id': 1, 'quantity': 6, 'portion': 'regular', 'addon': False}])
    assert pay(clients, order).status_code == 200
    with clients['database']() as session:
        doc = session.get(Invoice, order['id']).document
        assert doc['paid'] == order['due']
        assert doc['total'] - doc['paid'] > 0
    dummy = SimpleNamespace(id=1, accepted=1, request={'address':'Example'}, lines=[{'name':'Example', 'price':100, 'quantity':1, 'portion':'regular','addon':False}], total=100, payment='COD_DUE', due=100)
    doc = snapshot(dummy, SimpleNamespace(email='test@example.test'), SimpleNamespace(name='Test'))
    assert doc['taxable'] + doc['cgst'] + doc['sgst'] + doc['rounding'] == 100
    assert doc['paid'] == 0
