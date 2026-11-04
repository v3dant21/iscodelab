import os
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(os.environ.get('DATABASE_URL', 'postgresql+psycopg://dumhouse:local-demo-only@localhost:55432/dumhouse'), pool_pre_ping=True)
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


class Payment(Base):
    __tablename__ = 'payments'
    event = Column(String, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    success = Column(Boolean, nullable=False)
    amount = Column(Integer, nullable=False)
