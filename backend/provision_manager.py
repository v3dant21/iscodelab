"""Explicitly provision an outlet manager: python provision_manager.py EMAIL OUTLET_ID."""
import getpass
import sys
from argon2 import PasswordHasher
from sqlalchemy import select
from personal_data import lookup
from models import SessionLocal, User, Outlet
if __name__ == '__main__':
    email, outlet_id=sys.argv[1],int(sys.argv[2])
    manager_role=sys.argv[3] if len(sys.argv)>3 else 'manager'
    if manager_role not in ('manager','catering_manager'): raise SystemExit('Role must be manager or catering_manager.')
    password=getpass.getpass('New manager password (at least 12 characters): ')
    if len(password)<12: raise SystemExit('Password must have at least 12 characters.')
    with SessionLocal.begin() as db:
        if not db.get(Outlet,outlet_id): raise SystemExit('Outlet does not exist.')
        if db.scalar(select(User).where(User.email_hash==lookup(email))): raise SystemExit('Account exists; no changes made.')
        db.add(User(email=email.lower(),password=PasswordHasher().hash(password),role=manager_role,outlet_id=outlet_id,cod=False))
    print('Outlet manager created.')
