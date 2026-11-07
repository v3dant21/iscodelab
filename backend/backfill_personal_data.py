"""Run once after deploying v005 with keys configured. Never prints contact data."""
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from models import SessionLocal, User, Order, Invoice, Notification

def run():
    with SessionLocal.begin() as db:
        for user in db.scalars(select(User).with_for_update()):
            user.email = user.email
            flag_modified(user, 'email')
        for model, field in [(Order,'request'),(Invoice,'document'),(Notification,'recipient')]:
            for row in db.scalars(select(model).with_for_update()):
                if getattr(row,field) is not None: flag_modified(row,field)
    print('Personal-data backfill completed.')

if __name__ == '__main__': run()
