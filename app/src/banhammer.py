import uuid
from datetime import timedelta
from triggers import Bans, Ratios, Rate_windows


class BanHandler:
    def __init__(self, redis_wrapper, bans=Bans, ratios=Ratios, rate_windows=Rate_windows,
                 default_user_status="default", events_db_key="events", key_status_db_key="key_status"):
        self.bans = bans
        self.ratios = ratios
        self.events_db_key = events_db_key
        self.key_status_db_key = key_status_db_key
        self.default_user_status = default_user_status
        db_keys = list(bans.keys())
        db_keys.append(self.events_db_key)
        db_keys.append(self.key_status_db_key)
        self.redis_dbs = {k: v for v, k in enumerate(db_keys, start=0)}
        self.rate_windows = rate_windows
        self.redis = redis_wrapper

    def __save_event(self, key, event):
        db_index = self.redis_dbs[self.events_db_key]
        for rate in self.rate_windows:
            k = f'{event}.{rate}.{key}.{str(uuid.uuid1().hex)}'
            self.redis.set_key_value(k, '', db_index, timedelta(seconds=self.rate_windows[rate]))

    def __call_actions(self, key, actions):
        for a in actions:
            a(key)

    def __update_threshold_index(self, db_index, event, key, threshold_index):
        threshold = event['thresholds'][threshold_index]
        _ = self.redis.set_event_counter(key, threshold['limit'], timedelta(seconds=threshold['window']),
                                         db_index, threshold_index)

    def __apply_mitigates(self, event, key):
        mitigates = event['mitigates']
        for k in mitigates:
            print(f"mitigates: {mitigates[k]}")
            self.__mitigate(key, k, mitigates[k])

    def __mitigate(self, key, target_event, threshold_index):
        db_index = self.redis_dbs[target_event]
        exists, data, ttl = self.redis.get_event_status(key, db_index)
        if exists and data['threshold_index'] <= threshold_index:
            self.redis.remove_key(key, db_index)

    def __set_status(self, key, status, duration):
        self.redis.set_key_value(key, status, self.redis_dbs[self.key_status_db_key],
                                 timedelta(seconds=duration))

    def __get_rate_by_pattern(self, k, db_index):
        return len(self.redis.get_keys_by_pattern(k, db_index))

    def __get_event_rate(self, db_index, event_key, key, rate):
        return self.__get_rate_by_pattern(f'{event_key}.{rate}.{key}*', db_index)

    def __calculate_ratios(self, event, key):
        ratios = event['ratios']
        for r in ratios:
            self.__calculate_ratio(key, r)

    def __calculate_ratio(self, key, ratio_key):
        curr_status = self.status(key)
        ratio = self.ratios[ratio_key]
        if "not_calculate_status" not in ratio or curr_status not in ratio["not_calculate_status"]:
            top = self.__get_event_rate(self.redis_dbs[self.events_db_key], ratio["top"], key, ratio["window"])
            if top >= ratio["top_minimum"]:
                bottom = self.__get_event_rate(self.redis_dbs[self.events_db_key], ratio["bottom"], key, ratio["window"])
                if bottom == 0:
                    bottom = 1
                if top / bottom >= ratio["ratio_max"]:
                    if "action" in ratio:
                        self.__call_actions(key, ratio["action"])
                    self.__set_status(key, ratio['status'], ratio['action_duration'])

    def get_event_rates(self, event_key):
        db_index = self.redis_dbs[self.events_db_key]
        out = {}
        for r in self.rate_windows:
            out[r] = self.__get_rate_by_pattern(f'{event_key}.{r}*', db_index)
        return out

    def get_key_rates(self, key):
        out = {}
        events = self.bans.keys()
        for event_key in events:
            out[event_key] = self.get_key_event_rates(key, event_key)
        print(out)
        return out

    def get_key_event_rates(self, key, event_key):
        db_index = self.redis_dbs[self.events_db_key]
        out = {}
        for rate in self.rate_windows:
            out[rate] = self.__get_rate_by_pattern(f'{event_key}.{rate}.{key}*', db_index)
        return out

    def reset(self, key, event_key):
        self.redis.remove_key(key, self.redis_dbs[self.key_status_db_key])

        db_index = self.redis_dbs[event_key]
        exists, data, ttl = self.redis.get_event_status(key, db_index)
        if exists:
            self.redis.remove_key(key, db_index)

        db_index = self.redis_dbs[self.events_db_key]
        keys = self.redis.get_keys_by_pattern(f'{event_key}.*.{key}*', db_index)
        for k in keys:
            self.redis.remove_key(k, db_index)

    def reset_all(self, key):
        events = self.bans.keys()
        for event_key in events:
            self.reset(key, event_key)

    def status(self, key):
        db_index = self.redis_dbs[self.key_status_db_key]
        exists, status = self.redis.get_key_value(key, db_index)
        if exists:
            return status
        return self.default_user_status

    def incr(self, key, event_key):
        self.__save_event(key, event_key)
        event = self.bans[event_key]
        if 'thresholds' in event:
            db_index = self.redis_dbs[event_key]
            exists, data, ttl = self.redis.get_event_status(key, db_index)
            if not exists:
                threshold_index = 0
                threshold = event['thresholds'][threshold_index]
                _ = self.redis.set_event_counter(key, threshold['limit'], timedelta(seconds=threshold['window']),
                                                 db_index, threshold_index)
            else:
                threshold_index = data['threshold_index']
                thresholds = event['thresholds']
                threshold = thresholds[threshold_index]
                ok = self.redis.decrease_event_counter(key, db_index, ttl)
                if not ok:
                    if 'action' in threshold:
                        self.__call_actions(key, threshold['action'])
                    if 'status' in threshold:
                        self.__set_status(key, threshold['status'], threshold['action_duration'])
                    if len(thresholds) > threshold_index + 1:
                        self.__update_threshold_index(db_index, event, key, threshold_index + 1)
        if 'mitigates' in event:
            self.__apply_mitigates(event, key)
        if 'ratios' in event:
            self.__calculate_ratios(event, key)
        return self.get_key_event_rates(key, event_key)
