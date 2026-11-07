"""Provision persistent, outlet-assigned sample identities. Never reset existing accounts.

Run with the target DATABASE_URL and PII keys set. The password handover file must
be outside tracked source (the default .env.* path is gitignored).
"""
import json
import os
import secrets
from pathlib import Path
from argon2 import PasswordHasher
from sqlalchemy import select
from models import SessionLocal, User, Outlet
from personal_data import lookup

STAFF = [
    ('Ayaan Khan','ayaan@dastan.local','Kondapur','kitchen'),
    ('Meera Rao','meera@dastan.local','Kondapur','manager'),
    ('Kabir Ali','kabir@dastan.local','Gachibowli','kitchen'),
    ('Nisha Reddy','nisha@dastan.local','Gachibowli','manager'),
    ('Arjun Naidu','arjun@dastan.local','Madhapur','kitchen'),
    ('Sana Ahmed','sana@dastan.local','Madhapur','manager'),
]

def provision(credentials_path):
    credentials_path=Path(credentials_path)
    # Exclusive creation prevents overwriting the only password handover copy.
    fd=os.open(credentials_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    created=[];existing=[]
    try:
        with os.fdopen(fd,'w') as handover:
            with SessionLocal.begin() as db:
                outlets={o.name:o.id for o in db.scalars(select(Outlet))}
                for name,email,outlet,role in STAFF:
                    if outlet not in outlets:raise ValueError(f'Missing outlet: {outlet}')
                    account=db.scalar(select(User).where(User.email_hash==lookup(email)))
                    if account:
                        if account.role!=role or account.outlet_id!=outlets[outlet]:
                            raise ValueError(f'Existing account assignment differs: {email}')
                        existing.append(email);continue
                    password=secrets.token_urlsafe(18)
                    db.add(User(email=email,name=name,password=PasswordHasher().hash(password),
                        role=role,outlet_id=outlets[outlet],cod=False))
                    created.append({'name':name,'email':email,'password':password,'role':role,'outlet':outlet})
                db.flush()
                json.dump({'staff_url':'https://iscodelab.vercel.app/staff','accounts':created,
                    'existing_accounts_unchanged':existing},handover,indent=2)
                handover.flush();os.fsync(handover.fileno())
    except BaseException:
        credentials_path.unlink(missing_ok=True)
        raise
    return {'created':len(created),'existing_unchanged':len(existing),'credentials_file':str(credentials_path)}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--credentials-file',required=True)
    args=parser.parse_args();print(provision(args.credentials_file))
