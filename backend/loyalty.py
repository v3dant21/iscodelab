"""Points are payment credit; taxable menu prices are unchanged.

All writers lock the customer row before locking an order. Ledger rows and order
state commit together. Unique (order,kind) prevents duplicate awards/refunds.
"""
import time
from sqlalchemy import select, func
from models import LoyaltyEntry, User


def balance(db, user_id):
    return db.scalar(select(func.coalesce(func.sum(LoyaltyEntry.points),0)).where(LoyaltyEntry.user_id==user_id))


def lock_customer(db, user_id):
    db.execute(select(User.id).where(User.id==user_id).with_for_update())


def add_entry(db, order, kind, points):
    if not points or db.scalar(select(LoyaltyEntry.id).where(LoyaltyEntry.order_id==order.id,LoyaltyEntry.kind==kind)): return
    db.add(LoyaltyEntry(user_id=order.user_id,order_id=order.id,kind=kind,points=points,created=time.time()))
    db.flush()


def reward_quote(db, user_id, total, points, fail):
    available = balance(db,user_id)
    if points > available: fail('Your points balance changed. Review your rewards and try again.',409)
    if points*100 > total: fail('Points cannot exceed the order total.')
    return {'redeemed_points':points,'loyalty_credit':points*100,'payable_total':total-points*100,'loyalty_balance':available,'points_to_earn':(total-points*100)//10000}


def award(db, order):
    if order.status != 'HANDED_OFF' or order.payment != 'PAID': return
    points = (order.total-order.redeemed_points*100)//10000
    add_entry(db,order,'earn',points)
    order.earned_points=points
