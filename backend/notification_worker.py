"""Independent delay monitor and bounded concurrent notification dispatcher."""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from models import SessionLocal
from notifications import overdue, dispatch

def drain():
    for _ in range(25):
        with SessionLocal.begin() as connection:
            if not dispatch(connection): break

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[]
        while True:
            try:
                with SessionLocal.begin() as connection: overdue(connection)
                if not jobs or all(job.done() for job in jobs):
                    for job in jobs:
                        try: job.result()
                        except Exception: logging.exception('Notification dispatcher batch failed; retrying next batch')
                    jobs=[pool.submit(drain) for _ in range(4)]
            except Exception: logging.exception('Notification worker cycle failed')
            time.sleep(5)
