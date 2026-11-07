from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def scheduled_now(dish, now=None):
    if not dish.schedule:
        return True
    now = now or datetime.now(ZoneInfo('Asia/Kolkata'))
    local = now.astimezone(ZoneInfo('Asia/Kolkata'))
    minute = local.hour * 60 + local.minute
    for window in dish.schedule:
        start, end = [int(value[:2])*60 + int(value[3:]) for value in (window['start'],window['end'])]
        if start < end:
            if local.weekday() in window['days'] and start <= minute < end: return True
        else:
            if (local.weekday() in window['days'] and minute >= start) or ((local-timedelta(days=1)).weekday() in window['days'] and minute < end): return True
    return False


def dish_price(dish, assignment=None, city=None):
    if assignment and assignment.price is not None: return assignment.price
    return (dish.city_prices or {}).get((city or '').strip().lower(), dish.price)
