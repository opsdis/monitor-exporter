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
import asyncio

from prometheus_client import (CONTENT_TYPE_LATEST, Counter)
from quart import request, Response, jsonify, Blueprint

import monitor_exporter.log as log
import monitor_exporter.monitorconnection as monitorconnection
from monitor_exporter.perfdata import Perfdata

app = Blueprint("prom", __name__)
total_requests = Counter('requests', 'Total requests to monitor-exporter endpoint')


@app.route('/', methods=['GET'])
def hello_world():
    return 'monitor-exporter alive'


@app.route("/metrics", methods=['GET'])
async def get_metrics():
    before_request_func(request)
    target = request.args.get('target')

    log.info('Collect metrics', {'target': target})

    monitor_data = Perfdata(monitorconnection.MonitorConfig(), target)

    # Fetch performance data from Monitor
    await asyncio.get_event_loop().create_task(monitor_data.get_perfdata())

    target_metrics = monitor_data.prometheus_format()

    resp = Response(target_metrics)
    resp.headers['Content-Type'] = CONTENT_TYPE_LATEST

    return resp


@app.route("/health", methods=['GET'])
def get_health():
    return check_healthy()


def before_request_func(request):
    call_status = {'remote_addr': request.remote_addr, 'url': request.url}
    log.info('Access', call_status)


@app.after_request
def after_request_func(response):
    total_requests.inc()

    call_status = {'content_length': response.content_length, 'status': response.status_code,
                   'count': total_requests._value.get()}
    log.info('Response', call_status)

    return response


def check_healthy() -> Response:
    resp = jsonify({'status': 'ok'})
    resp.status_code = 200
    return resp
