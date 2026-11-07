"""Catalogue validation, reward history, catering review and outlet reporting."""
import hashlib
import json
import time
import os
import ipaddress
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, func, case
from models import Dish, Outlet, Order, User, PartyRequest, LoyaltyEntry
from personal_data import lookup
from loyalty import balance, lock_customer, add_entry
from notifications import enqueue


class Window(BaseModel):
    model_config = ConfigDict(extra='forbid')
    days: list[int] = Field(min_length=1,max_length=7)
    start: str = Field(pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')
    end: str = Field(pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')

    @field_validator('days')
    @classmethod
    def weekdays(cls, value):
        if any(d<0 or d>6 for d in value) or len(set(value))!=len(value): raise ValueError('Choose distinct weekdays from Monday (0) to Sunday (6).')
        return value


class MenuFields(BaseModel):
    city_prices: dict[str,int] = Field(default_factory=dict,max_length=100)
    schedule: list[Window] = Field(default_factory=list,max_length=14)
    photo_url: str = Field(default='',max_length=1000)
    photo_credit: str = Field(default='',max_length=200)
    spice_level: Literal['not_set','mild','medium','hot','very_hot'] = 'not_set'

    @field_validator('city_prices')
    @classmethod
    def cities(cls, value):
        result={}
        for city,price in value.items():
            key=city.strip().lower()
            if not key or len(key)>80 or key in result or price<100 or price>1000000: raise ValueError('Each city needs a unique name and a price between ₹1 and ₹10,000.')
            result[key]=price
        return result

    @field_validator('schedule')
    @classmethod
    def windows(cls,value):
        if any(w.start==w.end for w in value): raise ValueError('Start and end must differ. Leave the schedule empty for all-day service.')
        return value

    @field_validator('photo_url')
    @classmethod
    def photo(cls,value):
        if not value: return value
        if value.startswith('/images/') and '..' not in value and '\\' not in value and '?' not in value and '#' not in value: return value
        url=urlparse(value)
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.port not in (None,443): raise ValueError('Use a public HTTPS photo URL or an existing /images/ path.')
        host=url.hostname.lower()
        if '.' not in host or host.endswith(('.localhost','.local','.internal')): raise ValueError('Use a public image host.')
        try:
            if not ipaddress.ip_address(host).is_global: raise ValueError('Private addresses cannot host menu photos.')
        except ValueError as error:
            if host.replace('.','').isdigit() or ':' in host: raise error
        return value


class CityInput(BaseModel):
    city: str = Field(min_length=2,max_length=80)


class PartyInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str = Field(min_length=10,max_length=100)
    outlet_id: int
    event_at: datetime
    guests: int = Field(ge=1,le=1000)
    venue: str = Field(min_length=5,max_length=500)
    menu_request: str = Field(min_length=5,max_length=2000)
    dietary_notes: str = Field(default='',max_length=1000)

    @field_validator('venue','menu_request','dietary_notes',mode='before')
    @classmethod
    def trim_details(cls,value):
        return value.strip() if isinstance(value,str) else value

    @field_validator('event_at')
    @classmethod
    def timezone_required(cls,value):
        if value.tzinfo is None: raise ValueError('Include a timezone for the event.')
        return value


class PartyDecision(BaseModel):
    @field_validator('note',mode='before')
    @classmethod
    def trim_note(cls,value):
        return value.strip() if isinstance(value,str) else value

    status: Literal['CONFIRMED','DECLINED']
    note: str = Field(min_length=5,max_length=1000)
    version: int = Field(ge=0)


class CancelInput(BaseModel):
    @field_validator('reason',mode='before')
    @classmethod
    def trim_reason(cls,value):
        return value.strip() if isinstance(value,str) else value

    reason: str = Field(min_length=5,max_length=500)
    version: int = Field(ge=0)


def party_data(row):
    return {key:getattr(row,key) for key in ('id','outlet_id','event_at','guests','status','manager_note','decided_at','created','version')} | {'details':row.details}


def register_operations(app, current_user, database, fail, order_data):
    @app.patch('/admin/outlets/{outlet_id}/city')
    def city(outlet_id:int, body:CityInput, user=Depends(current_user), db=Depends(database)):
        if user.role!='admin': fail('Administrator access required.',403)
        outlet=db.get(Outlet,outlet_id)
        if not outlet: fail('Outlet not found.',404)
        if len(body.city.strip())<2: fail('Enter a city name.')
        outlet.city=body.city.strip(); db.commit()
        return {'city':outlet.city}

    @app.get('/account/loyalty')
    def rewards(user=Depends(current_user),db=Depends(database)):
        if user.role!='customer': fail('Customer access required.',403)
        entries=db.scalars(select(LoyaltyEntry).where(LoyaltyEntry.user_id==user.id).order_by(LoyaltyEntry.id.desc()).limit(50))
        return {'balance':balance(db,user.id),'earn_every_paise':10000,'point_value_paise':100,'entries':[{key:getattr(e,key) for key in ('order_id','kind','points','created')} for e in entries]}

    @app.post('/orders/{order_id}/cancel')
    @app.post('/manager/orders/{order_id}/cancel')
    def cancel(order_id:int,body:CancelInput,user=Depends(current_user),db=Depends(database)):
        order=db.get(Order,order_id)
        if not order or not (user.role=='admin' or user.role=='manager' and order.outlet_id==user.outlet_id or user.role=='customer' and order.user_id==user.id): fail('Order not found.',404)
        lock_customer(db,order.user_id)
        order=db.scalar(select(Order).where(Order.id==order_id).with_for_update().execution_options(populate_existing=True))
        if order.status=='CANCELLED': return order_data(order)
        if order.status=='HANDED_OFF' or order.version!=body.version: fail('Order changed or has already been handed off.',409)
        if user.role=='customer' and order.status!='PENDING_PAYMENT': fail('Please contact your outlet to cancel an accepted order.',409)
        original_payment=order.payment
        order.status='CANCELLED';order.cancelled_at=time.time();order.cancellation_reason=body.reason.strip();order.version+=1
        if original_payment in ('PAID','DEPOSIT_PAID'):
            order.payment='REFUNDED_TEST' if os.getenv('ALLOW_MOCK_PAYMENTS')=='true' else 'REFUND_REQUIRED'
        else: order.payment='CANCELLED'
        add_entry(db,order,'refund',order.redeemed_points)
        enqueue(db,order,'cancelled',f'Order #{order.id} was cancelled. Reserved loyalty points have been returned.')
        db.commit();return order_data(order)

    @app.get('/party/outlets')
    def party_outlets(db=Depends(database)):
        return [{'id':o.id,'name':o.name,'city':o.city} for o in db.scalars(select(Outlet).where(Outlet.opened.is_(True)).order_by(Outlet.name))]

    @app.post('/party/requests')
    def request_party(body:PartyInput,user=Depends(current_user),db=Depends(database)):
        if user.role!='customer': fail('Customer access required.',403)
        if not user.name or not user.phone: fail('Complete your contact details in Account first.',409)
        lock_customer(db,user.id)
        fingerprint=lookup(json.dumps(body.model_dump(mode='json'),sort_keys=True),'party')
        existing=db.scalar(select(PartyRequest).where(PartyRequest.user_id==user.id,PartyRequest.key==body.key))
        if existing:
            if existing.digest!=fingerprint: fail('This request key has already been used.',409)
            return party_data(existing)
        event_at=body.event_at.timestamp(); now=time.time()
        if event_at < now+48*3600: fail('Party orders need at least 48 hours notice.')
        if event_at > now+366*86400: fail('Choose an event within the next year.')
        outlet=db.get(Outlet,body.outlet_id)
        if not outlet or not outlet.opened: fail('Choose an open catering outlet.',409)
        row=PartyRequest(user_id=user.id,outlet_id=body.outlet_id,key=body.key,digest=fingerprint,event_at=event_at,guests=body.guests,
            details={'name':user.name,'phone':user.phone,'email':user.email,'venue':body.venue,'menu_request':body.menu_request,'dietary_notes':body.dietary_notes},created=now)
        db.add(row);db.commit();return party_data(row)

    @app.get('/party/requests')
    def customer_parties(user=Depends(current_user),db=Depends(database)):
        if user.role!='customer': fail('Customer access required.',403)
        return [party_data(p) for p in db.scalars(select(PartyRequest).where(PartyRequest.user_id==user.id).order_by(PartyRequest.id.desc()).limit(100))]

    @app.get('/catering/requests')
    def catering_queue(user=Depends(current_user),db=Depends(database)):
        if user.role not in ('admin','catering_manager'): fail('Catering manager access required.',403)
        query=select(PartyRequest)
        if user.role=='catering_manager': query=query.where(PartyRequest.outlet_id==user.outlet_id)
        return [party_data(p) for p in db.scalars(query.order_by(PartyRequest.event_at.desc()).limit(200))]

    @app.patch('/catering/requests/{request_id}')
    def decision(request_id:int,body:PartyDecision,user=Depends(current_user),db=Depends(database)):
        if user.role not in ('admin','catering_manager'): fail('Catering manager access required.',403)
        query=select(PartyRequest).where(PartyRequest.id==request_id)
        if user.role=='catering_manager': query=query.where(PartyRequest.outlet_id==user.outlet_id)
        row=db.scalar(query.with_for_update())
        if not row: fail('Party request not found.',404)
        if row.status!='REQUESTED' or row.version!=body.version: fail('This request has already been reviewed. Refresh the list.',409)
        if body.status=='CONFIRMED' and row.event_at<=time.time(): fail('The event has already passed.',409)
        row.status=body.status;row.manager_note=body.note.strip();row.decided_by=user.id;row.decided_at=time.time();row.version+=1
        db.commit();return party_data(row)

    @app.get('/manager/dashboard')
    def dashboard(days:int=30,user=Depends(current_user),db=Depends(database)):
        if user.role not in ('admin','manager'): fail('Manager access required.',403)
        if days not in (7,30,90): fail('Choose 7, 30 or 90 days.')
        since=time.time()-days*86400
        outlets=db.scalars(select(Outlet).where(Outlet.id==user.outlet_id) if user.role=='manager' else select(Outlet).order_by(Outlet.id))
        result=[]
        for outlet in outlets:
            condition=(Order.outlet_id==outlet.id,Order.created>=since)
            aggregate=db.execute(select(func.count(Order.id),func.sum(case((Order.accepted.is_not(None),1),else_=0)),func.sum(case((Order.status=='CANCELLED',1),else_=0)),func.sum(case((Order.status=='HANDED_OFF',1),else_=0)),func.sum(case((Order.status.notin_(['CANCELLED','PENDING_PAYMENT']),Order.total),else_=0)),func.avg(case((Order.ready_at.is_not(None),(Order.ready_at-Order.accepted)/60),else_=None)),func.count(Order.ready_at)).where(*condition)).one()
            repeated=select(Order.user_id).where(*condition,Order.status=='HANDED_OFF').group_by(Order.user_id).having(func.count(Order.id)>=2).subquery()
            customers=db.scalar(select(func.count(func.distinct(Order.user_id))).where(*condition,Order.status=='HANDED_OFF'))
            result.append({'outlet_id':outlet.id,'outlet':outlet.name,'city':outlet.city,'orders':aggregate[0],'accepted':aggregate[1] or 0,'cancellations':aggregate[2] or 0,'handoffs':aggregate[3] or 0,'gross_sales':aggregate[4] or 0,'average_prep_minutes':round(aggregate[5],1) if aggregate[5] is not None else None,'prep_samples':aggregate[6],'repeat_customers':db.scalar(select(func.count()).select_from(repeated)),'customers':customers})
        return {'days':days,'since':since,'outlets':result,'definitions':'Prep time is confirmation to ready, only where timestamps were recorded. Repeat customers completed two or more handoffs at the same outlet during this period. Sales exclude cancelled and unpaid orders; amounts are test transactions.'}
