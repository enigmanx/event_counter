import json
from redis import Redis
from datetime import timedelta


def get_redis(db):
    return Redis(host='redis', port=6379, db=db, decode_responses=True)


def get_event_status(key: str, db_index: int):
    r = get_redis(db_index)
    if r.exists(key):
        return True, json.loads(r.get(key)), r.ttl(key)
    return False, None, None


def set_event_counter(key: str, limit: int, period: timedelta, db_index: int, threshold_index: int = 0):
    r = get_redis(db_index)
    r.set(key, json.dumps({'limit': limit - 1, 'threshold_index': threshold_index}))
    r.expire(key, int(period.total_seconds()))
    return True if limit > 0 else False


def decrease_event_counter(key: str, db_index: int, ttl: int):
    r = get_redis(db_index)
    val = json.loads(r.get(key))
    if val:
        limit = val['limit']
        if limit > 0:
            r.set(key, json.dumps({'limit': limit - 1, 'threshold_index': val['threshold_index']}))
            r.expire(key, ttl)
            return True
        elif limit == 0:
            return False
    return True


def remove_key(key: str, db_index: int):
    r = get_redis(db_index)
    if r.exists(key):
        r.delete(key)


def set_key_value(key: str, value: str, db_index: int, duration: timedelta):
    r = get_redis(db_index)
    r.set(key, value)
    r.expire(key, int(duration.total_seconds()))


def get_key_value(key: str, db_index: int):
    r = get_redis(db_index)
    if r.exists(key):
        return True, str(r.get(key))
    return False, None


def get_keys_by_pattern(key: str, db_index: int):
    r = get_redis(db_index)
    return r.keys(f"{key}")
