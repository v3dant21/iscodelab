"""Explicitly provision an outlet manager: python provision_manager.py EMAIL OUTLET_ID."""
import getpass
import sys
from argon2 import PasswordHasher
from sqlalchemy import select
from models import SessionLocal, User, Outlet
if __name__ == '__main__':
    email, outlet_id=sys.argv[1],int(sys.argv[2])
    password=getpass.getpass('New manager password (at least 12 characters): ')
    if len(password)<12: raise SystemExit('Password must have at least 12 characters.')
    with SessionLocal.begin() as db:
        if not db.get(Outlet,outlet_id): raise SystemExit('Outlet does not exist.')
        if db.scalar(select(User).where(User.email==email.lower())): raise SystemExit('Account exists; no changes made.')
        db.add(User(email=email.lower(),password=PasswordHasher().hash(password),role='manager',outlet_id=outlet_id,cod=False))
    print('Outlet manager created.')
