## Overview
System that enables generic, hierarchical, metrics-driven action triggers. Designed it to efficiently operate on many millions of 
unique actors and thousands of unique metrics and action triggers per day.
https://dev.to/astagi/rate-limiting-using-python-and-redis-58gk

#### Requirements
It is a library that runs fast, scales, and is designed for execution safety.

## Usage example

Goal: 
 - block any IP that fails to login 10 times in a row within 1 hour.
 - report IP that continues to fail 100x in a day for global ban.
 - track rates per minute, 10m, and 60m for each metric.

### Server API:

```
route('/get_event_rates/<event_key>')
route('/get_key_rates/<key>')
route('/get_key_event_rates/<key>/<event_key>')
route('/reset/<key>/<event_key>')
route('/reset_all/<key>')
route('/status/<key>')
route('/incr/<key>/<event_key>')
```
