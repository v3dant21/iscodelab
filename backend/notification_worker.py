"""Independent delay monitor and bounded concurrent notification dispatcher."""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from models import SessionLocal
from email_delivery import dispatch_email
from notifications import overdue, dispatch

def drain():
    for _ in range(25):
        with SessionLocal.begin() as connection:
            if not dispatch(connection): break

def drain_email():
    for _ in range(5):
        with SessionLocal.begin() as connection:
            if not dispatch_email(connection): break
        time.sleep(0.6)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs=[]
        while True:
            try:
                with SessionLocal.begin() as connection: overdue(connection)
                if not jobs or all(job.done() for job in jobs):
                    for job in jobs:
                        try: job.result()
                        except Exception: logging.exception('Notification dispatcher batch failed; retrying next batch')
                    jobs=[pool.submit(drain) for _ in range(4)] + [pool.submit(drain_email)]
            except Exception: logging.exception('Notification worker cycle failed')
            time.sleep(5)
