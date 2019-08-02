# -*- coding: utf-8 -*-
"""
    Copyright (C) 2019  Opsdis AB

    This file is part of monitor-exporter.

    monitor-exporter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    monitor-exporter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with monitor-exporter.  If not, see <http://www.gnu.org/licenses/>.

"""
import argparse
import time

from flask import Flask, request
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Gauge,
                               Metric, generate_latest)

from exporterlog import ExporterLog
from perfdata import Perfdata

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
