import hashlib
import json
import math
import os
import secrets
import time
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from models import Assignment, Dish, Order, Outlet, Payment, Session, SessionLocal, User
from prediction import predict

app = FastAPI(title='DumHouse API')
origin = os.environ.get('APP_ORIGIN', 'http://localhost:3000')
app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_credentials=True, allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type', 'X-CSRF-Token'])
hasher = PasswordHasher()


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
    return {'id': user.id, 'email': user.email, 'role': user.role, 'outlet_id': user.outlet_id, 'cod': user.cod}


class Credentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=5, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=10, max_length=128)


def login_session(user, response, connection):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    connection.add(Session(token=digest(token), csrf=csrf, user_id=user.id, expires=time.time() + 86400))
    connection.commit()
    secure = os.environ.get('SECURE_COOKIES', 'false') == 'true'
    response.set_cookie('session', token, httponly=True, secure=secure, samesite='lax', max_age=86400)
    response.set_cookie('csrf', csrf, secure=secure, samesite='lax', max_age=86400)
    return profile(user)


@app.post('/auth/register')
def register(body: Credentials, request: Request, response: Response, connection=Depends(database)):
    if request.headers.get('origin') not in (None, origin):
        fail('Origin not allowed.', 403)
    user = User(email=body.email.lower(), password=hasher.hash(body.password), role='customer')
    connection.add(user)
    try:
        connection.flush()
    except IntegrityError:
        connection.rollback()
        fail('This email is already registered.', 409)
    return login_session(user, response, connection)


@app.post('/auth/login')
def login(body: Credentials, request: Request, response: Response, connection=Depends(database)):
    if request.headers.get('origin') not in (None, origin):
        fail('Origin not allowed.', 403)
    user = connection.scalar(select(User).where(User.email == body.email.lower()))
    try:
        if not user or not hasher.verify(user.password, body.password):
            fail('Email or password is incorrect.', 401)
    except VerificationError:
        fail('Email or password is incorrect.', 401)
    return login_session(user, response, connection)


@app.get('/auth/me')
def me(user=Depends(current_user)):
    return profile(user)


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
            result.append({'id': outlet.id, 'name': outlet.name, 'distance': round(kilometers, 2), 'minimum': outlet.minimum})
    return sorted(result, key=lambda outlet: outlet['distance'])


def menu_data(dish, assignment=None):
    return {'id': dish.id, 'name': dish.name, 'description': dish.description, 'category': dish.category, 'price': assignment.price if assignment and assignment.price is not None else dish.price, 'veg': dish.veg, 'allergens': dish.allergens, 'options': dish.options, 'weight': dish.weight, 'enabled': assignment.enabled if assignment else True, 'available': assignment.available if assignment else True, 'override': assignment.price if assignment else None}


def menu(connection, outlet_id, public=True):
    query = select(Dish, Assignment).join(Assignment, Assignment.dish_id == Dish.id).where(Assignment.outlet_id == outlet_id)
    if public:
        query = query.where(Assignment.enabled.is_(True), Assignment.available.is_(True))
    return [menu_data(dish, assignment) for dish, assignment in connection.execute(query)]


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


class Checkout(Location):
    model_config = ConfigDict(extra='forbid')
    outlet_id: int
    address: str = Field(min_length=5, max_length=500)
    lines: list[Line] = Field(min_length=1, max_length=30)
    method: Literal['upi', 'card', 'cod'] = 'upi'
    key: str = Field(min_length=10, max_length=100)


def quote(body, connection):
    outlet = connection.get(Outlet, body.outlet_id, with_for_update=True)
    if not outlet or not outlet.opened or distance(body.lat, body.lng, outlet) > outlet.radius:
        fail('This outlet cannot deliver to your location. Choose an eligible outlet.', 409)
    lines = []
    for line in sorted(body.lines, key=lambda item: item.dish_id):
        dish = connection.get(Dish, line.dish_id, with_for_update=True)
        assignment = connection.get(Assignment, (body.outlet_id, line.dish_id), with_for_update=True)
        if not dish or not assignment or not assignment.enabled or not assignment.available:
            fail('An item is sold out or no longer assigned. Refresh your menu and cart.', 409)
        if line.portion not in dish.options:
            fail('Invalid portion.')
        price = (assignment.price if assignment.price is not None else dish.price) + dish.options[line.portion] + (3000 if line.addon else 0)
        lines.append({'dish_id': dish.id, 'name': dish.name, 'portion': line.portion, 'addon': line.addon, 'quantity': line.quantity, 'price': price, 'weight': dish.weight})
    return {'lines': lines, 'total': sum(line['price'] * line['quantity'] for line in lines)}


@app.post('/checkout/quote')
def checkout_quote(body: Checkout, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    return quote(body, connection)


def accept(order, connection):
    outlet = connection.get(Outlet, order.outlet_id)
    queue = len(list(connection.scalars(select(Order.id).where(Order.outlet_id == order.outlet_id, Order.status.in_(['NEW', 'PREPARING'])))))
    hour = datetime.now(ZoneInfo('Asia/Kolkata')).hour
    order.minutes, order.prediction = predict(order.lines, queue, outlet.minimum, hour in (12, 13, 19, 20, 21))
    order.status, order.accepted = 'NEW', time.time()
    order.version += 1


def order_data(order):
    return {field: getattr(order, field) for field in ('id', 'outlet_id', 'lines', 'total', 'due', 'payment', 'status', 'version', 'created', 'accepted', 'minutes', 'prediction')} | {'address': order.request['address'], 'late': bool(order.accepted and order.minutes and order.status not in ('HANDED_OFF', 'PENDING_PAYMENT') and time.time() > order.accepted + (order.minutes + 10) * 60)}


@app.post('/orders')
def create_order(body: Checkout, user=Depends(current_user), connection=Depends(database)):
    role(user, 'customer')
    connection.execute(select(User.id).where(User.id == user.id).with_for_update())
    payload = body.model_dump()
    fingerprint = digest(json.dumps(payload, sort_keys=True))
    existing = connection.scalar(select(Order).where(Order.user_id == user.id, Order.key == body.key))
    if existing:
        if existing.digest != fingerprint:
            fail('Checkout key was already used for a different cart.', 409)
        return order_data(existing)
    if body.method == 'cod' and not user.cod:
        fail('This account is prepaid-only.', 403)
    quoted = quote(body, connection)
    order = Order(user_id=user.id, outlet_id=body.outlet_id, key=body.key, digest=fingerprint, request=payload, lines=quoted['lines'], total=quoted['total'], due=quoted['total'], created=time.time())
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
    role(user, 'kitchen')
    return [order_data(order) for order in connection.scalars(select(Order).where(Order.outlet_id == user.outlet_id, Order.status.in_(['NEW', 'PREPARING', 'READY'])).order_by(Order.created))]


class Transition(BaseModel):
    status: Literal['PREPARING', 'READY', 'HANDED_OFF']
    version: int


@app.patch('/kitchen/orders/{order_id}/status')
def transition(order_id: int, body: Transition, user=Depends(current_user), connection=Depends(database)):
    role(user, 'kitchen')
    previous = {'PREPARING': 'NEW', 'READY': 'PREPARING', 'HANDED_OFF': 'READY'}[body.status]
    result = connection.execute(update(Order).where(Order.id == order_id, Order.outlet_id == user.outlet_id, Order.status == previous, Order.version == body.version).values(status=body.status, version=body.version + 1))
    if result.rowcount != 1:
        fail('Order changed or is unavailable. Refresh the board.', 409)
    connection.commit()
    return order_data(connection.get(Order, order_id))


@app.get('/kitchen/menu')
def kitchen_menu(user=Depends(current_user), connection=Depends(database)):
    role(user, 'kitchen')
    return menu(connection, user.outlet_id, False)


class Availability(BaseModel):
    available: bool


@app.patch('/kitchen/menu/{dish_id}')
def availability(dish_id: int, body: Availability, user=Depends(current_user), connection=Depends(database)):
    role(user, 'kitchen')
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
    return [{'id': outlet.id, 'name': outlet.name} for outlet in connection.scalars(select(Outlet))]


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
