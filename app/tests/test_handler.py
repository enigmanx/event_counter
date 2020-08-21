import time
import pytest
import triggers
from app.src import banhammer
from app.src import redis_wrapper
from utils import flush_db, flush_dbs


def get_handler(default_user_status="default"):
    return banhammer.BanHandler(redis_wrapper, triggers.Bans, triggers.Ratios, triggers.Rate_windows,
                                default_user_status=default_user_status)


def test_banhammer_init():
    flush_dbs()
    handler = get_handler()
    assert handler is not None


def test_default_incr():
    flush_dbs()
    handler = get_handler()
    key = "test_default_incr"
    event = "login_failed"
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 10):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    for i in range(0, 100):
        handler.incr(key, event)
        assert handler.status(key) == "blocked"
    for i in range(0, 1000):
        handler.incr(key, event)
        assert handler.status(key) == "banned"
    handler.incr(key, event)
    assert handler.status(key) == "trolling_banned"
    time.sleep(2)
    assert handler.status(key) == handler.default_user_status


def test_ratio_check_event():
    flush_dbs()
    handler = get_handler()
    key = "test_ratio_check_event"
    event = "ratio_check_event"
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 9):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    handler.incr(key, event)
    assert handler.status(key) == "ratio_check_event_not_passed"


def test_mitigation():
    flush_dbs()
    handler = get_handler()
    key = "test_mitigation"
    event = "login_failed"
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 10):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    handler.incr(key, "login_successful")
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 10):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    handler.incr(key, event)
    assert handler.status(key) == "blocked"


def test_reset():
    flush_dbs()
    handler = get_handler()
    key = "test_reset"
    event = "login_failed"
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 10):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    handler.incr(key, event)
    assert handler.status(key) == "blocked"
    handler.reset(key, event)
    assert handler.status(key) == handler.default_user_status


def test_reset_all():
    flush_dbs()
    handler = get_handler()
    key = "test_reset"
    event = "login_failed"
    assert handler.status(key) == handler.default_user_status
    for i in range(0, 10):
        handler.incr(key, event)
        assert handler.status(key) == handler.default_user_status
    handler.incr(key, event)
    assert handler.status(key) == "blocked"
    handler.reset_all(key)
    assert handler.status(key) == handler.default_user_status


def test_get_key_event_rates():
    flush_dbs()
    handler = get_handler()
    key = "test_get_rates"
    event = "login_failed"
    empty_rates = handler.get_key_event_rates(key, event)
    for r in empty_rates:
        assert empty_rates[r] == 0
    for i in range(0, 10):
        handler.incr(key, event)
    rates = handler.get_key_event_rates(key, event)
    for r in rates:
        assert rates[r] == 10
    handler.reset(key, event)
    empty_rates = handler.get_key_event_rates(key, event)
    for r in empty_rates:
        assert empty_rates[r] == 0


def test_get_event_rates():
    flush_dbs()
    handler = get_handler()
    key = "test_get_key_rates"
    event = "login_failed"
    empty_rates = handler.get_event_rates(event)
    for r in empty_rates:
        assert empty_rates[r] == 0
    for i in range(0, 3):
        handler.incr(key, event)
    rates = handler.get_event_rates(event)
    for r in rates:
        assert rates[r] == 3
    key = "test_get_key_rates_2"
    for i in range(0, 3):
        handler.incr(key, event)
    rates = handler.get_event_rates(event)
    for r in rates:
        assert rates[r] == 6


def test_get_key_rates():
    flush_dbs()
    handler = get_handler()
    key = "test_get_key_rates"
    event_1 = "login_failed"
    for i in range(0, 3):
        handler.incr(key, event_1)
    rates = handler.get_key_rates(key)
    for r in rates[event_1]:
        assert rates[event_1][r] == 3
    event_2 = "login_successful"
    for i in range(0, 3):
        handler.incr(key, event_2)
    rates = handler.get_key_rates(key)
    for r in rates[event_1]:
        assert rates[event_1][r] == 3
    for r in rates[event_2]:
        assert rates[event_1][r] == 3
