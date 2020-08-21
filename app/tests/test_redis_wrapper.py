import uuid
import time
import pytest
from utils import flush_db
from datetime import timedelta
from app.src import redis_wrapper as redis


def test_redis_init():
    db_index = 0
    flush_db(db_index)
    r = redis.get_redis(db_index)
    assert r is not None


def test_get_event_status():
    db_index = 0
    flush_db(db_index)
    key = "test_get_event_status"
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert not exists
    assert data is None
    assert ttl is None


def test_set_event_counter():
    key = "test_set_event_counter"
    db_index = 0
    flush_db(db_index)
    limit = 5
    period = timedelta(seconds=30)
    threshold_index = 0
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert not exists
    assert data is None
    assert ttl is None
    assert redis.set_event_counter(key, limit, period, db_index, threshold_index) is True
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert exists
    assert data is not None
    assert data['limit'] == limit - 1
    assert data['threshold_index'] == 0
    assert ttl is not None
    assert ttl > 0


def test_decrease_event_counter():
    key = "test_decrease_event_counter"
    db_index = 0
    flush_db(db_index)
    limit = 5
    period = timedelta(seconds=30)
    threshold_index = 0
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert not exists
    assert data is None
    assert ttl is None
    redis.set_event_counter(key, limit, period, db_index, threshold_index)
    for l in range(0, limit-1):
        exists, data, ttl = redis.get_event_status(key, db_index)
        assert redis.decrease_event_counter(key, db_index, ttl) is True
    assert redis.decrease_event_counter(key, db_index, ttl) is False


def test_remove_remove_key():
    db_index = 0
    flush_db(db_index)
    key = "test_remove_key"
    limit = 5
    period = timedelta(seconds=30)
    threshold_index = 0
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert not exists
    assert data is None
    assert ttl is None
    redis.set_event_counter(key, limit, period, db_index, threshold_index)
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert exists
    assert data is not None
    assert ttl is not None
    redis.remove_key(key, db_index)
    exists, data, ttl = redis.get_event_status(key, db_index)
    assert not exists
    assert data is None
    assert ttl is None


def test_get_set_key_value():
    db_index = 0
    flush_db(db_index)
    key = "test_set_key_value"
    db_index = 0
    status = 'status'
    period = timedelta(seconds=2)
    redis.set_key_value(key, status, db_index, period)
    exists, value = redis.get_key_value(key, db_index)
    assert exists
    assert value == status
    time.sleep(2)
    exists, value = redis.get_key_value(key, db_index)
    assert not exists
    assert value is None


def test_get_keys_by_pattern():
    db_index = 0
    flush_db(db_index)
    key = "test_get_keys_by_pattern"
    db_index = 0
    status = 'status'
    period = timedelta(seconds=3)
    for i in range(0, 10):
        hex = uuid.uuid1().hex
        redis.set_key_value(key + str(hex), status, db_index, period)
    keys = redis.get_keys_by_pattern(f"{key}*", db_index)
    assert len(keys) == 10
