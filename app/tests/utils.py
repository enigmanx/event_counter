from app.src import redis_wrapper as redis

def flush_db(db_index):
    r = redis.get_redis(db_index)
    r.flushdb()

def flush_dbs(redis_dbs=5):
    for db_index in range(0, redis_dbs):
        flush_db(db_index)
