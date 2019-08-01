import time
import argparse
from flask import Flask, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Gauge, CollectorRegistry, Metric
from perfdata import Perfdata

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route("/metrics", methods=['GET'])
def get_metrics():
    print(request)
    target = request.args.get('target')
    print(target)
    class_test = Perfdata(target)

    # Fetch performance data from Monitor
    class_test.get_perfdata()

    target_metrics = class_test.prometheus_format()
    
    resp = app.make_response(target_metrics)

    resp.headers['Content-Type'] = CONTENT_TYPE_LATEST
    # resp.status = 200
    return resp

def start():
    parser = argparse.ArgumentParser(
        description='monitor_exporter')

    parser.add_argument('-p', '--port',
                        dest="port", help="Server port")

    args = parser.parse_args()

    port = 5000
    if args.port:
        port = args.port

    app.run(host='0.0.0.0', port=port)