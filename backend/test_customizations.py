import io
from pypdf import PdfReader
from sqlalchemy import select
from test_app import clients, payload, pay
from curated_menu import SELECTED
from models import Dish
from customizations import customization_groups


def test_entire_curated_menu_has_relevant_choices(clients):
    with clients['database']() as db:
        dishes = [d for d in db.scalars(select(Dish)) if d.name in SELECTED]
        assert len(dishes) == 70
        for dish in dishes:
            groups = customization_groups(dish)
            assert groups, dish.name
            assert all(len(g['choices']) >= 2 for g in groups)
            assert all(g['default'] in [c['id'] for c in g['choices']] for g in groups)
        lassi = next(d for d in dishes if d.name == 'Lassi')
        assert {c['id'] for c in customization_groups(lassi)[0]['choices']} == {'sweet','salted','unsweetened'}
        assert not any(g['id']=='spice' for g in customization_groups(lassi))


def test_choices_reach_kitchen_history_and_both_invoice_formats(clients):
    c=clients['customer']
    body=payload(lines=[{'dish_id':1,'quantity':2,'portion':'regular','addon':True,'selections':{'masala':'less','fried_onion':'none'}}])
    quote=c.post('/checkout/quote',json=body); assert quote.status_code==200
    assert quote.json()['total']==65800
    order=c.post('/orders',json=body).json(); assert pay(clients,order).status_code==200
    own=c.get('/orders').json()
    saved=next(o for o in own if o['id']==order['id'])['lines'][0]
    assert saved['selections']=={'masala':'less','fried_onion':'none'}
    assert 'Biryani masala: Less masala' in saved['customization_labels']
    kitchen=clients['kondapur'].get('/kitchen/orders').json()
    assert next(o for o in kitchen if o['id']==order['id'])['lines'][0]['customization_labels']==saved['customization_labels']
    html=c.get(f"/orders/{order['id']}/invoice").text
    assert 'Less masala' in html and 'No added fried onion' in html
    pdf=c.get(f"/orders/{order['id']}/invoice?format=pdf")
    text=' '.join(' '.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages).split())
    assert 'Less masala' in text and 'No added fried onion' in text


def test_reject_foreign_choices_and_client_price_and_keep_legacy_cart(clients):
    c=clients['customer']
    for selections in [{'flavour':'salted'},{'masala':'made-up'},{'masala':'less','price':'0'}]:
        body=payload(lines=[{'dish_id':1,'quantity':1,'selections':selections}])
        assert c.post('/checkout/quote',json=body).status_code==400
    legacy=c.post('/checkout/quote',json=payload()).json()
    assert legacy['lines'][0]['selections']['masala']=='usual'
    assert legacy['total']==29900


def test_family_pack_raita_and_dish_specific_defaults(clients):
    menu=clients['guest'].get('/outlets/1/menu').json()
    family=next(d for d in menu if d['name']=='Chicken Biryani Family Pack')
    assert family['raita_available']
    body=payload(lines=[{'dish_id':family['id'],'quantity':1,'portion':next(iter(family['options'])),'addon':True,'selections':{'masala':'extra'}}])
    quote=clients['customer'].post('/checkout/quote',json=body)
    assert quote.status_code==200 and quote.json()['total']==family['price']+3000
    lassi=next(d for d in menu if d['name']=='Lassi')
    body['lines']=[{'dish_id':lassi['id'],'quantity':1,'selections':{'flavour':'salted'},'addon':True}]
    assert clients['customer'].post('/checkout/quote',json=body).status_code==400
    body['lines'][0]['addon']=False
    result=clients['customer'].post('/checkout/quote',json=body).json()
    assert result['lines'][0]['selections']=={'flavour':'salted','ice':'none'}
