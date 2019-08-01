import time
import argparse
from flask import Flask, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Gauge, CollectorRegistry, Metric
from perfdata import Perfdata
from exporterlog import ExporterLog

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route("/metrics", methods=['GET'])
def get_metrics():
    ExporterLog.info(request)
    target = request.args.get('target')
    
    ExporterLog.info('Getting metrics for: ' + target)

    monitor_data = Perfdata(target)

    # Fetch performance data from Monitor
    monitor_data.get_perfdata()

    target_metrics = monitor_data.prometheus_format()
    
    resp = app.make_response(target_metrics)

    resp.headers['Content-Type'] = CONTENT_TYPE_LATEST
    # resp.status = 200
    ExporterLog.info(resp)
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
    ExporterLog.info('Starting web app on port: ' + str(port))
    app.run(host='0.0.0.0', port=port)