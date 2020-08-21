import json
import triggers
import banhammer
import redis_wrapper as redis
from flask import Flask, redirect, Response


app = Flask(__name__)
handler = banhammer.BanHandler(redis, triggers.Bans, triggers.Ratios, triggers.Rate_windows,
                               default_user_status="default")


@app.route('/get_event_rates/<event_key>')
def get_event_rates(event_key):
    return Response(json.dumps(handler.get_event_rates(event_key)), status=200)


@app.route('/get_key_rates/<key>')
def get_key_rates(key):
    return Response(json.dumps(handler.get_key_rates(key)), status=200)


@app.route('/get_key_event_rates/<key>/<event_key>')
def get_key_event_rates(key, event_key):
    return Response(json.dumps(handler.get_key_event_rates(key, event_key)), status=200)


@app.route('/reset/<key>/<event_key>')
def reset(key, event_key):
    handler.reset(key, event_key)
    return Response("Ok", status=200)


@app.route('/reset_all/<key>')
def reset_all(key):
    handler.reset_all(key)
    return Response("Ok", status=200)


@app.route('/status/<key>')
def status(key):
    return Response(json.dumps(handler.status(key)), status=200)


@app.route('/incr/<key>/<event_key>')
def incr(key, event_key):
    return Response(json.dumps(handler.incr(key, event_key)), status=200)


@app.route('/health_check')
def health_check():
    return Response("Ok", status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
