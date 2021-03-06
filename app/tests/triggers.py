class Action:
    """ define actions to be executed """
    @staticmethod
    def block_local(key):
        print(f'{key} blocked')
        pass

    @staticmethod
    def report_central(key):
        print(f'{key} report_central')
        pass

    @staticmethod
    def record_local(key):
        print(f'{key} record_local')
        pass


Bans = {
    "login_failed": {
        "thresholds": [
            {
                "limit": 10,
                "window": 3600,
                "action": [Action.block_local],
                "action_duration": 3600,
                "status": "blocked"
            },
            {
                "limit": 100,
                "window": 3600,
                "action": [Action.report_central],
                "action_duration": 86400,
                "status": "banned"
            },
            {
                "limit": 1000,
                "window": 10,
                "action_duration": 2,
                "status": "trolling_banned"
            }
        ],
        "ratios": ["login_failed__to__login_successful"]
    },
    "login_successful": {
        "thresholds": [
            {
                "limit": 10,
                "window": 60,
                "actions": [Action.record_local],
                "action_duration": 3600,
                "status": "blocked"
            },
        ],
        "mitigates": {"login_failed": 0},
        "ratios": ["login_failed__to__login_successful"]
    },
    "ratio_check_event": {
        "ratios": ["ratio_check_event__to__event"]
    }
}

Ratios = {
    "login_failed__to__login_successful": {
        "top": "login_failed",
        "top_minimum": 30,
        "bottom": "login_successful",
        "ratio_max": 10,
        "action_duration": 3600,
        "window": "1m",
        "status": "login_failed__to__login_successful_not_passed",
        "not_calculate_status": ["blocked", "banned", "trolling_banned"],
        "action": [Action.block_local, Action.report_central],
    },
    "ratio_check_event__to__event": {
        "top": "ratio_check_event",
        "top_minimum": 10,
        "bottom": "login_successful",
        "ratio_max": 10,
        "action_duration": 3600,
        "window": "1m",
        "not_calculate_status": ["blocked", "banned", "trolling_banned"],
        "status": "ratio_check_event_not_passed",
    }
}

Rate_windows = {
    "1m": 60,
    "10m": 600,
    "60m": 3600
}
