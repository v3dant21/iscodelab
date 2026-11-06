import os
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

database_url = os.environ.get('DATABASE_URL', 'postgresql+psycopg://dumhouse:local-demo-only@localhost:55432/dumhouse')
# Hosted providers return standard PostgreSQL URLs; this app uses psycopg 3.
if database_url.startswith(('postgres://', 'postgresql://')):
    database_url = 'postgresql+psycopg://' + database_url.split('://', 1)[1]
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='customer')
    outlet_id = Column(Integer, ForeignKey('outlets.id'))
    cod = Column(Boolean, nullable=False, default=False)
    marketing_opt_in = Column(Boolean, nullable=False, default=False)
    marketing_updated = Column(Float)


class Session(Base):
    __tablename__ = 'sessions'
    token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    csrf = Column(String, nullable=False)
    expires = Column(Float, nullable=False)


class Outlet(Base):
    __tablename__ = 'outlets'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius = Column(Float, nullable=False, default=8)
    opened = Column(Boolean, nullable=False, default=True)
    minimum = Column(Integer, nullable=False, default=20)
    fssai = Column(String(14))


class Dish(Base):
    __tablename__ = 'dishes'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    veg = Column(Boolean, nullable=False)
    allergens = Column(String, nullable=False, default='')
    weight = Column(Integer, nullable=False, default=10)
    options = Column(JSON, nullable=False, default=dict)


class Assignment(Base):
    __tablename__ = 'assignments'
    outlet_id = Column(Integer, ForeignKey('outlets.id'), primary_key=True)
    dish_id = Column(Integer, ForeignKey('dishes.id'), primary_key=True)
    enabled = Column(Boolean, nullable=False, default=True)
    available = Column(Boolean, nullable=False, default=True)
    price = Column(Integer)


class Order(Base):
    __tablename__ = 'orders'
    __table_args__ = (UniqueConstraint('user_id', 'key'),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    outlet_id = Column(Integer, ForeignKey('outlets.id'), nullable=False, index=True)
    key = Column(String, nullable=False)
    digest = Column(String, nullable=False)
    request = Column(JSON, nullable=False)
    lines = Column(JSON, nullable=False)
    total = Column(Integer, nullable=False)
    due = Column(Integer, nullable=False)
    payment = Column(String, nullable=False, default='PENDING')
    status = Column(String, nullable=False, default='PENDING_PAYMENT', index=True)
    version = Column(Integer, nullable=False, default=0)
    created = Column(Float, nullable=False)
    accepted = Column(Float)
    minutes = Column(Integer)
    prediction = Column(String)
    ai_minutes = Column(Integer)
    original_promise = Column(Float)
    late_alerted = Column(Float)
    estimate_reason = Column(String)


class Payment(Base):
    __tablename__ = 'payments'
    event = Column(String, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    success = Column(Boolean, nullable=False)
    amount = Column(Integer, nullable=False)


class GoogleIdentity(Base):
    __tablename__ = 'google_identities'
    subject = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)


class Invoice(Base):
    __tablename__ = 'invoices'
    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    document = Column(JSON, nullable=False)


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    event_key = Column(String, unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    outlet_id = Column(Integer, ForeignKey('outlets.id'), nullable=False)
    audience = Column(String, nullable=False)
    message = Column(String, nullable=False)
    channel = Column(String, nullable=False, default='in_app')
    recipient = Column(String)
    state = Column(String, nullable=False, default='pending')
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt = Column(Float, nullable=False, default=0)
    created = Column(Float, nullable=False)


class EstimateChange(Base):
    __tablename__ = 'estimate_changes'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    before = Column(Integer, nullable=False)
    after = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    created = Column(Float, nullable=False)


class ConsentRecord(Base):
    __tablename__ = 'consent_records'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    purpose = Column(String, nullable=False)
    granted = Column(Boolean, nullable=False)
    notice_version = Column(String, nullable=False)
    created = Column(Float, nullable=False)
