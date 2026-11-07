import hashlib
import json
import math
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from billing import snapshot, render_bill, render_pdf, tax_breakdown
from personal_data import lookup, cipher
from email_delivery import verification, order_email, configured as email_configured
from notifications import enqueue
from models import EmailDelivery, EmailVerification, Notification, EstimateChange, ConsentRecord, Invoice, GoogleIdentity, Assignment, Dish, Order, Outlet, Payment, Session, SessionLocal, User
from prediction import predict

@asynccontextmanager
async def lifespan(app):
    cipher()
    lookup('configuration-check')
    yield

app = FastAPI(title='DumHouse API', lifespan=lifespan)
origin = os.environ.get('APP_ORIGIN', 'http://localhost:3000')
app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_credentials=True, allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type', 'X-CSRF-Token'])
hasher = PasswordHasher()

@app.middleware('http')
async def private_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(('/auth/', '/account/', '/orders', '/kitchen/', '/manager/')):
        response.headers['Cache-Control'] = 'private, no-store'
    return response



def fail(detail, code=400):
    raise HTTPException(code, detail)


def database():
    with SessionLocal() as connection:
        yield connection


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def current_user(request: Request, connection=Depends(database)):
    token = request.cookies.get('session', '')
    session = connection.get(Session, digest(token))
    if not session or session.expires < time.time():
        fail('Please sign in.', 401)
    if request.method != 'GET':
        csrf = request.headers.get('x-csrf-token', '')
        if not csrf or not secrets.compare_digest(csrf, session.csrf) or csrf != request.cookies.get('csrf'):
            fail('Session verification failed. Refresh and try again.', 403)
        if request.headers.get('origin') not in (None, origin):
            fail('Origin not allowed.', 403)
    return connection.get(User, session.user_id)


def role(user, expected):
    if user.role != expected:
        fail('This action is not available for your role.', 403)


def profile(user):
    return {'id': user.id, 'email': user.email, 'role': user.role, 'outlet_id': user.outlet_id, 'cod': user.cod, 'marketing_opt_in': user.marketing_opt_in, 'name': user.name or '', 'phone': user.phone or '', 'profile_complete': bool(user.name and user.phone), 'email_verified': user.email_verified, 'email_delivery_configured': email_configured()}


class Credentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=5, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=10, max_length=128)


class ContactDetails(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r'^\+[1-9][0-9]{7,14}$', max_length=16)

    @field_validator('name')
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if len(value) < 2 or any(ord(c)<32 for c in value): raise ValueError('Enter your name')
        return value

class Registration(Credentials, ContactDetails):
    pass


def login_session(user, response, connection):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    connection.add(Session(token=digest(token), csrf=csrf, user_id=user.id, expires=time.time() + 86400))
    connection.commit()
    secure = os.environ.get('SECURE_COOKIES', 'false') == 'true'
    response.set_cookie('session', token, httponly=True, secure=secure, samesite='lax', max_age=86400)
    response.set_cookie('csrf', csrf, secure=secure, samesite='lax', max_age=86400)
    return profile(user)


@app.post('/auth/register')
def register(body: Registration, request: Request, response: Response, connection=Depends(database)):
    if request.headers.get('origin') not in (None, origin):
        fail('Origin not allowed.', 403)
    user = User(email=body.email.lower(), password=hasher.hash(body.password), role='customer', name=body.name, phone=body.phone)
    connection.add(user)
    try:
        connection.flush()
    except IntegrityError:
        connection.rollback()
        fail('This email is already registered.', 409)
    verification(connection, user)
    return login_session(user, response, connection)


@app.post('/auth/login')
def login(body: Credentials, request: Request, response: Response, connection=Depends(database)):
    if request.headers.get('origin') not in (None, origin):
        fail('Origin not allowed.', 403)
    user = connection.scalar(select(User).where(User.email_hash == lookup(body.email)))
    try:
        if not user or not hasher.verify(user.password, body.password):
            fail('Email or password is incorrect.', 401)
    except VerificationError:
        fail('Email or password is incorrect.', 401)
    return login_session(user, response, connection)


class GoogleCredentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    credential: str = Field(min_length=1, max_length=10000)
    nonce: str = Field(min_length=20, max_length=128)


@app.get('/auth/google/config')
def google_config(response: Response):
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    nonce = secrets.token_urlsafe(32) if client_id else ''
    response.headers['Cache-Control'] = 'no-store'
    if client_id:
        response.set_cookie('google_nonce', nonce, httponly=True,
                            secure=os.environ.get('SECURE_COOKIES', 'false') == 'true',
                            samesite='strict', max_age=600)
    return {'client_id': client_id, 'nonce': nonce}


def verify_google_token(credential, client_id):
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    return id_token.verify_oauth2_token(credential, GoogleRequest(), client_id)


@app.post('/auth/google')
def google_login(body: GoogleCredentials, request: Request, response: Response, connection=Depends(database)):
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    if not client_id:
        fail('Google sign-in is not configured. Please use email.', 503)
    if request.headers.get('origin') != origin:
        fail('Origin not allowed.', 403)
    nonce = request.cookies.get('google_nonce', '')
    if not nonce or not secrets.compare_digest(nonce, body.nonce):
        fail('Sign-in expired. Refresh and try again.', 403)
    try:
        claims = verify_google_token(body.credential, client_id)
    except ValueError:
        fail('Google could not verify this sign-in.', 401)
    except Exception:
        fail('Google is temporarily unavailable. Please use email.', 503)
    if not isinstance(claims.get('nonce'), str) or not secrets.compare_digest(claims['nonce'], nonce):
        fail('Sign-in verification failed. Refresh and try again.', 401)
    if not claims.get('sub') or claims.get('email_verified') is not True or not claims.get('email'):
        fail('A verified Google email is required.', 401)
    identity = connection.get(GoogleIdentity, claims['sub'])
    user = connection.get(User, identity.user_id) if identity else None
    if not user:
        email = claims['email'].lower()
        if connection.scalar(select(User).where(User.email_hash == lookup(email))):
            fail('This email already has an account. Sign in with your existing password.', 409)
        user = User(email=email, password=hasher.hash(secrets.token_urlsafe(48)), role='customer', cod=False, email_verified=True, name=str(claims.get('name',''))[:100])
        connection.add(user)
        try:
            connection.flush()
            connection.add(GoogleIdentity(subject=claims['sub'], user_id=user.id))
            connection.flush()
        except IntegrityError:
            connection.rollback()
            fail('Account setup changed. Please try signing in again.', 409)
    role(user, 'customer')
    response.delete_cookie('google_nonce')
    return login_session(user, response, connection)


@app.get('/auth/me')
def me(user=Depends(current_user)):
    return profile(user)


@app.patch('/account/profile')
def update_profile(body: ContactDetails, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    user.name, user.phone = body.name, body.phone
    connection.commit()
    return profile(user)

@app.post('/auth/email/request-verification')
def request_verification(user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    connection.execute(select(User.id).where(User.id==user.id).with_for_update())
    if not user.email_verified: verification(connection,user)
    connection.commit()
    return {'configured':email_configured(), 'verified':user.email_verified}

class VerifyEmail(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=32, max_length=100)

@app.post('/auth/email/verify')
def verify_email(body: VerifyEmail, request: Request, connection=Depends(database)):
    if request.headers.get('origin') != origin: fail('Origin not allowed.',403)
    record=connection.get(EmailVerification,digest(body.token),with_for_update=True)
    if not record or record.used or record.expires < time.time(): fail('This verification link expired or was already used. Request another from your account.',400)
    user=connection.get(User,record.user_id)
    user.email_verified=True
    record.used=True
    connection.execute(update(EmailDelivery).where(EmailDelivery.user_id==user.id,EmailDelivery.state=='awaiting_verification').values(state='pending'))
    connection.commit()
    return {'verified':True}

@app.get('/account/email-status')
def email_status(user=Depends(current_user), connection=Depends(database)):
    role(user,'customer')
    rows=connection.scalars(select(EmailDelivery).where(EmailDelivery.user_id==user.id,EmailDelivery.kind=='order').order_by(EmailDelivery.id.desc()).limit(100))
    return {'configured':email_configured(),'verified':user.email_verified,'items':[{'order_id':r.order_id,'state':r.state} for r in rows]}


@app.post('/auth/logout')
def logout(request: Request, response: Response, user=Depends(current_user), connection=Depends(database)):
    connection.delete(connection.get(Session, digest(request.cookies['session'])))
    connection.commit()
    response.delete_cookie('session')
    response.delete_cookie('csrf')
    return {'ok': True}


def distance(lat, lng, outlet):
    latitude = math.radians(outlet.lat - lat)
    longitude = math.radians(outlet.lng - lng)
    value = math.sin(latitude / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(outlet.lat)) * math.sin(longitude / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(value)))


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)


@app.get('/health')
def health(connection=Depends(database)):
    connection.execute(select(1))
    return {'status': 'ok'}


@app.get('/outlets')
def outlets(location: Location = Depends(), connection=Depends(database)):
    result = []
    for outlet in connection.scalars(select(Outlet)):
        kilometers = distance(location.lat, location.lng, outlet)
        if outlet.opened and kilometers <= outlet.radius:
            result.append({'id': outlet.id, 'name': outlet.name, 'distance': round(kilometers, 2), 'minimum': outlet.minimum, 'fssai': outlet.fssai})
    return sorted(result, key=lambda outlet: outlet['distance'])


def menu_data(dish, assignment=None):
    return {'id': dish.id, 'name': dish.name, 'description': dish.description, 'category': dish.category, 'price': assignment.price if assignment and assignment.price is not None else dish.price, 'veg': dish.veg, 'allergens': dish.allergens, 'options': dish.options, 'weight': dish.weight, 'enabled': assignment.enabled if assignment else True, 'available': assignment.available if assignment else True, 'override': assignment.price if assignment else None}


def menu(connection, outlet_id, public=True):
    query = select(Dish, Assignment).join(Assignment, Assignment.dish_id == Dish.id).where(Assignment.outlet_id == outlet_id)
    if public:
        query = query.where(Assignment.enabled.is_(True), Assignment.available.is_(True))
    return [menu_data(dish, assignment) for dish, assignment in connection.execute(query.order_by(Dish.id))]


@app.get('/catalog')
def public_catalog(connection=Depends(database)):
    # Catalog identity remains stable when a kitchen temporarily sells out.
    query = select(Dish).where(select(Assignment.dish_id).where(Assignment.dish_id == Dish.id, Assignment.enabled.is_(True)).exists()).order_by(Dish.id)
    return [menu_data(dish) for dish in connection.scalars(query)]


@app.get('/outlets/{outlet_id}/menu')
def public_menu(outlet_id: int, connection=Depends(database)):
    outlet = connection.get(Outlet, outlet_id)
    if not outlet or not outlet.opened:
        fail('Outlet is closed or unavailable.', 404)
    return menu(connection, outlet_id)


class Line(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dish_id: int
    quantity: int = Field(ge=1, le=20)
    portion: str = 'regular'
    addon: bool = False


class UpdatePreference(BaseModel):
    channel: Literal['in_app', 'sms', 'whatsapp'] = 'in_app'
    phone: str = Field(default='', max_length=16, pattern=r'^$|^\+[1-9][0-9]{7,14}$')
    consent: bool = False


class Checkout(Location):
    model_config = ConfigDict(extra='forbid')
    outlet_id: int
    routing: Literal['auto', 'selected'] = 'selected'
    expected_total: int | None = Field(default=None, ge=0)
    expected_outlet: int | None = None
    updates: UpdatePreference = Field(default_factory=UpdatePreference)
    address: str = Field(min_length=5, max_length=500)
    lines: list[Line] = Field(min_length=1, max_length=30)
    method: Literal['upi', 'card', 'cod'] = 'upi'
    key: str = Field(min_length=10, max_length=100)


def quote(body, connection):
    if body.updates.channel != 'in_app' and (not body.updates.consent or not body.updates.phone):
        fail('Choose in-app updates or provide a phone number and consent for order messages.')
    outlet_id = body.outlet_id
    if body.routing == 'auto':
        candidates = sorted((o for o in connection.scalars(select(Outlet)) if o.opened and distance(body.lat, body.lng, o) <= o.radius), key=lambda o: (distance(body.lat, body.lng,o),o.id))
        outlet_id = 0
        for candidate in candidates:
            assigned = {a.dish_id:a for a in connection.scalars(select(Assignment).where(Assignment.outlet_id==candidate.id, Assignment.enabled.is_(True), Assignment.available.is_(True)))}
            if all(line.dish_id in assigned for line in body.lines):
                outlet_id=candidate.id; break
        if not outlet_id: fail('No nearby open kitchen can fulfil every item. Please edit your bag.',409)
    outlet = connection.get(Outlet, outlet_id, with_for_update=True)
    if not outlet or not outlet.opened or distance(body.lat, body.lng, outlet) > outlet.radius:
        fail('This outlet cannot deliver to your location. Choose an eligible outlet.', 409)
    lines = []
    for line in sorted(body.lines, key=lambda item: item.dish_id):
        dish = connection.get(Dish, line.dish_id, with_for_update=True)
        assignment = connection.get(Assignment, (outlet_id, line.dish_id), with_for_update=True)
        if not dish or not assignment or not assignment.enabled or not assignment.available:
            fail('An item is sold out or no longer assigned. Refresh your menu and cart.', 409)
        if line.portion not in dish.options:
            fail('Invalid portion.')
        if line.addon and dish.category != 'Biryani':
            fail('Extra raita is only available with biryani.')
        price = (assignment.price if assignment.price is not None else dish.price) + dish.options[line.portion] + (3000 if line.addon else 0)
        lines.append({'dish_id': dish.id, 'name': dish.name, 'portion': line.portion, 'addon': line.addon, 'quantity': line.quantity, 'price': price, 'weight': dish.weight})
    return {'lines': lines, 'total': sum(line['price'] * line['quantity'] for line in lines), 'outlet_id': outlet.id, 'outlet_name': outlet.name}


@app.post('/checkout/quote')
def checkout_quote(body: Checkout, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    result = quote(body, connection)
    return {**result, 'billing': tax_breakdown(result['lines'])}


def accept(order, connection):
    outlet = connection.get(Outlet, order.outlet_id)
    queue = len(list(connection.scalars(select(Order.id).where(Order.outlet_id == order.outlet_id, Order.status.in_(['NEW', 'PREPARING'])))))
    hour = datetime.now(ZoneInfo('Asia/Kolkata')).hour
    order.minutes, order.prediction = predict(order.lines, queue, outlet.minimum, hour in (12, 13, 19, 20, 21))
    order.ai_minutes = order.minutes
    order.status, order.accepted = 'NEW', time.time()
    order.original_promise = order.accepted + order.minutes * 60
    order.version += 1
    connection.flush()
    enqueue(connection, order, 'confirmed', f'Order #{order.id} is confirmed. Preparation promise: {order.minutes} minutes from confirmation.')
    customer = connection.get(User, order.user_id)
    connection.add(Invoice(order_id=order.id, document=snapshot(order, customer, outlet)))
    order_email(connection, order, customer)


def order_data(order):
    return {field: getattr(order, field) for field in ('id', 'outlet_id', 'lines', 'total', 'due', 'payment', 'status', 'version', 'created', 'accepted', 'minutes', 'prediction', 'ai_minutes', 'original_promise', 'estimate_reason')} | {'address': order.request['address'], 'contact': order.contact or {}, 'late': bool(order.late_alerted or (order.original_promise and order.status in ('NEW','PREPARING') and time.time() >= order.original_promise + 600))}


@app.post('/orders')
def create_order(body: Checkout, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    connection.execute(select(User.id).where(User.id == user.id).with_for_update())
    if not user.name or not user.phone: fail('Complete your name and contact phone number before ordering.',409)
    payload = body.model_dump()
    fingerprint = lookup(json.dumps(payload, sort_keys=True), 'checkout')
    existing = connection.scalar(select(Order).where(Order.user_id == user.id, Order.key == body.key))
    if existing:
        if existing.digest != fingerprint:
            fail('Checkout key was already used for a different cart.', 409)
        return order_data(existing)
    if body.method == 'cod' and not user.cod:
        fail('This account is prepaid-only.', 403)
    quoted = quote(body, connection)
    if (body.expected_total is not None and body.expected_total != quoted['total']) or (body.expected_outlet is not None and body.expected_outlet != quoted['outlet_id']):
        fail('Price or kitchen changed. Review your order again before confirming.',409)
    order = Order(user_id=user.id, outlet_id=quoted['outlet_id'], key=body.key, digest=fingerprint, request={**payload, 'outlet_id': quoted['outlet_id'], 'routing':'selected'}, contact={'name':user.name,'phone':user.phone,'email':user.email}, lines=quoted['lines'], total=quoted['total'], due=quoted['total'], created=time.time())
    connection.add(order)
    if body.method == 'cod':
        if order.total <= 150000:
            order.payment = 'COD_DUE'
            accept(order, connection)
        else:
            order.due = math.ceil(order.total * 0.2)
    try:
        connection.commit()
    except IntegrityError:
        connection.rollback()
        existing = connection.scalar(select(Order).where(Order.user_id == user.id, Order.key == body.key))
        if not existing or existing.digest != fingerprint:
            fail('Conflicting checkout. Refresh and try again.', 409)
        return order_data(existing)
    return order_data(order)


class MockPayment(BaseModel):
    event: str = Field(min_length=10, max_length=100)
    success: bool


@app.post('/payments/mock/{order_id}/complete')
def pay(order_id: int, body: MockPayment, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    if os.environ.get('ALLOW_MOCK_PAYMENTS', 'false') != 'true':
        fail('Test payments are disabled.', 403)
    order = connection.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id).with_for_update())
    if not order:
        fail('Order not found.', 404)
    previous = connection.get(Payment, body.event)
    if previous:
        if previous.order_id != order_id or previous.success != body.success:
            fail('Payment event already used.', 409)
        return order_data(order)
    if order.status != 'PENDING_PAYMENT':
        fail('This order has already been accepted.', 409)
    if body.success:
        current = quote(Checkout(**order.request), connection)
        if current['total'] != order.total or current['lines'] != order.lines:
            fail('Menu changed since checkout. Place a fresh order.', 409)
        order.payment = 'DEPOSIT_PAID' if order.request['method'] == 'cod' else 'PAID'
        accept(order, connection)
    connection.add(Payment(event=body.event, order_id=order.id, success=body.success, amount=order.due))
    try:
        connection.commit()
    except IntegrityError:
        connection.rollback()
        fail('Payment event already used.', 409)
    return order_data(order)


@app.get('/orders')
def my_orders(user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    return [order_data(order) for order in connection.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()))]


@app.get('/orders/{order_id}')
def my_order(order_id: int, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    order = connection.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id))
    if not order:
        fail('Order not found.', 404)
    return order_data(order)


@app.get('/kitchen/orders')
def kitchen_orders(user=Depends(current_user), connection=Depends(database)):
    if user.role not in ('kitchen','manager'): fail('Outlet staff access required.',403)
    return [order_data(order) for order in connection.scalars(select(Order).where(Order.outlet_id == user.outlet_id, Order.status.in_(['NEW', 'PREPARING', 'READY'])).order_by(Order.created))]


class Transition(BaseModel):
    status: Literal['PREPARING', 'READY', 'HANDED_OFF']
    version: int


@app.patch('/kitchen/orders/{order_id}/status')
def transition(order_id: int, body: Transition, user=Depends(current_user), connection=Depends(database)):
    if user.role not in ('kitchen','manager'): fail('Outlet staff access required.',403)
    previous = {'PREPARING': 'NEW', 'READY': 'PREPARING', 'HANDED_OFF': 'READY'}[body.status]
    result = connection.execute(update(Order).where(Order.id == order_id, Order.outlet_id == user.outlet_id, Order.status == previous, Order.version == body.version).values(status=body.status, version=body.version + 1))
    if result.rowcount != 1:
        fail('Order changed or is unavailable. Refresh the board.', 409)
    order = connection.get(Order, order_id)
    enqueue(connection,order, f'status-{body.status}', f'Order #{order.id}: {body.status.replace("_"," ").lower()}.')
    connection.commit()
    return order_data(order)


@app.get('/kitchen/menu')
def kitchen_menu(user=Depends(current_user), connection=Depends(database)):
    if user.role not in ('kitchen','manager'): fail('Outlet staff access required.',403)
    return menu(connection, user.outlet_id, False)


class Availability(BaseModel):
    available: bool


@app.patch('/kitchen/menu/{dish_id}')
def availability(dish_id: int, body: Availability, user=Depends(current_user), connection=Depends(database)):
    if user.role not in ('kitchen','manager'): fail('Outlet staff access required.',403)
    assignment = connection.get(Assignment, (user.outlet_id, dish_id))
    if not assignment or not assignment.enabled:
        fail('Dish not assigned.', 404)
    assignment.available = body.available
    connection.commit()
    return {'ok': True}


class DishInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    category: str = Field(min_length=2, max_length=50)
    price: int = Field(ge=100, le=1000000)
    veg: bool
    allergens: str = Field(max_length=200)
    weight: int = Field(ge=1, le=60)
    options: dict[str, int] = Field(min_length=1, max_length=10)


@app.get('/admin/menu-items')
def admin_menu(user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    return [menu_data(dish) for dish in connection.scalars(select(Dish).order_by(Dish.id))]


def save_dish(body, dish, connection):
    if any(not name or len(name) > 50 or price < 0 or price > 100000 for name, price in body.options.items()):
        fail('Invalid portion options.')
    for key, value in body.model_dump().items():
        setattr(dish, key, value)
    connection.add(dish)
    connection.commit()
    return menu_data(dish)


@app.post('/admin/menu-items')
def add_dish(body: DishInput, user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    return save_dish(body, Dish(), connection)


@app.patch('/admin/menu-items/{dish_id}')
def edit_dish(dish_id: int, body: DishInput, user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    dish = connection.get(Dish, dish_id)
    if not dish:
        fail('Dish not found.', 404)
    return save_dish(body, dish, connection)


@app.get('/admin/outlets')
def admin_outlets(user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    return [{'id': outlet.id, 'name': outlet.name, 'fssai':outlet.fssai} for outlet in connection.scalars(select(Outlet))]


@app.get('/admin/outlets/{outlet_id}/menu')
def assignments(outlet_id: int, user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    return menu(connection, outlet_id, False)


class Override(BaseModel):
    enabled: bool
    price: int | None = Field(default=None, ge=100, le=1000000)


@app.patch('/admin/outlets/{outlet_id}/menu/{dish_id}')
def assign(outlet_id: int, dish_id: int, body: Override, user=Depends(current_user), connection=Depends(database)):
    role(user, 'admin')
    if not connection.get(Outlet, outlet_id) or not connection.get(Dish, dish_id):
        fail('Outlet or dish not found.', 404)
    assignment = connection.get(Assignment, (outlet_id, dish_id)) or Assignment(outlet_id=outlet_id, dish_id=dish_id)
    assignment.enabled, assignment.price = body.enabled, body.price
    connection.add(assignment)
    connection.commit()
    return {'ok': True}


@app.post('/orders/{order_id}/invoice')
def prepare_invoice(order_id: int, user=Depends(current_user), connection=Depends(database)):
    order = connection.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id).with_for_update())
    if not order:
        fail('Order not found.', 404)
    if not order.accepted:
        fail('The order must be confirmed before a bill is available.', 409)
    if not connection.get(Invoice, order_id):
        connection.add(Invoice(order_id=order.id, document=snapshot(order, user, connection.get(Outlet, order.outlet_id))))
        connection.commit()
    return {'url': f'/api/orders/{order_id}/invoice'}


@app.get('/orders/{order_id}/invoice')
def view_invoice(order_id: int, download: bool = False, format: Literal['html','pdf'] = 'html', user=Depends(current_user), connection=Depends(database)):
    order = connection.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id))
    if not order:
        fail('Order not found.', 404)
    invoice = connection.get(Invoice, order_id)
    if not invoice:
        fail('Bill is not available yet.', 404)
    headers = {'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'}
    if format == 'pdf':
        headers['Content-Disposition'] = f'attachment; filename="{invoice.document["number"]}.pdf"'
        return Response(render_pdf(invoice.document), media_type='application/pdf', headers=headers)
    if download:
        headers['Content-Disposition'] = f'attachment; filename="{invoice.document["number"]}.html"'
    return Response(render_bill(invoice.document), media_type='text/html', headers=headers)


@app.get('/recommendations')
def recommendations(outlet_id: int, user=Depends(current_user), connection=Depends(database)):
    role(user,'customer')
    counts = {}
    recent = connection.scalars(select(Order).where(Order.user_id==user.id, Order.accepted.is_not(None)).order_by(Order.id.desc()).limit(100))
    for position, order in enumerate(recent):
        for line in order.lines:
            counts[line['dish_id']] = counts.get(line['dish_id'],0) + line['quantity'] / (1 + position / 10)
    available = {dish['id']:dish for dish in menu(connection,outlet_id)}
    return [{**available[key], 'reason':'Based on your previous orders'} for key in sorted(counts,key=lambda k:(-counts[k],k)) if key in available][:4]


@app.get('/notifications')
def notifications(user=Depends(current_user), connection=Depends(database)):
    query = select(Notification)
    if user.role == 'customer': query=query.where(Notification.user_id==user.id)
    elif user.role == 'manager': query=query.where(Notification.outlet_id==user.outlet_id,Notification.audience=='manager')
    elif user.role == 'admin': query=query.where(Notification.audience=='manager')
    else: fail('Not available for this role.',403)
    return [{'id':n.id,'order_id':n.order_id,'message':n.message,'channel':n.channel,'state':n.state,'created':n.created} for n in connection.scalars(query.order_by(Notification.id.desc()).limit(100))]


class EstimateInput(BaseModel):
    minutes: int = Field(ge=1,le=1440)
    reason: str = Field(min_length=5,max_length=300)
    version: int


@app.patch('/manager/orders/{order_id}/estimate')
def override_estimate(order_id:int, body:EstimateInput, user=Depends(current_user), connection=Depends(database)):
    if user.role not in ('manager','admin'): fail('Manager access required.',403)
    order=connection.scalar(select(Order).where(Order.id==order_id).with_for_update())
    if not order or (user.role=='manager' and order.outlet_id!=user.outlet_id): fail('Order not found.',404)
    if order.status not in ('NEW','PREPARING') or order.version!=body.version: fail('Order changed or preparation is complete. Refresh the board.',409)
    outlet=connection.get(Outlet,order.outlet_id)
    floor=max(order.ai_minutes or 0,outlet.minimum)
    if body.minutes<floor: fail(f'Promise must be at least {floor} minutes (AI estimate or kitchen minimum).')
    connection.add(EstimateChange(order_id=order.id,actor_id=user.id,before=order.minutes,after=body.minutes,reason=body.reason,created=time.time()))
    order.minutes=body.minutes; order.estimate_reason=body.reason; order.version+=1
    enqueue(connection,order,f'estimate-{order.version}',f'Order #{order.id}: preparation promise updated to {order.minutes} minutes from confirmation. {body.reason}')
    connection.commit()
    return order_data(order)


@app.get('/admin/outlets/{outlet_id}/orders')
def manager_queue(outlet_id:int,user=Depends(current_user),connection=Depends(database)):
    role(user,'admin')
    return [order_data(o) for o in connection.scalars(select(Order).where(Order.outlet_id==outlet_id,Order.status.in_(['NEW','PREPARING','READY'])).order_by(Order.created))]


class OutletLicence(BaseModel):
    fssai: str = Field(pattern=r'^\d{14}$')


@app.patch('/admin/outlets/{outlet_id}/licence')
def outlet_licence(outlet_id:int,body:OutletLicence,user=Depends(current_user),connection=Depends(database)):
    role(user,'admin')
    outlet=connection.get(Outlet,outlet_id)
    if not outlet: fail('Outlet not found.',404)
    outlet.fssai=body.fssai
    connection.commit()
    return {'ok':True}


class MarketingConsent(BaseModel):
    granted: bool


@app.patch('/account/marketing-consent')
def marketing_consent(body:MarketingConsent,user=Depends(current_user),connection=Depends(database)):
    role(user,'customer')
    user.marketing_opt_in=body.granted; user.marketing_updated=time.time()
    connection.add(ConsentRecord(user_id=user.id,purpose='marketing',granted=body.granted,notice_version='2026-11-06',created=user.marketing_updated))
    connection.commit()
    return profile(user)
