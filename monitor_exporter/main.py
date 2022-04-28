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
import asyncio
from quart import Quart
from apscheduler.schedulers.asyncio import AsyncIOScheduler


import monitor_exporter.fileconfiguration as config
import monitor_exporter.log as log
import monitor_exporter.monitorconnection as monitorconnection
import monitor_exporter.proxy as proxy

default_interval = 60
default_ttl = 300


def start():
    """
    Used from __main__ to start as simple flask app
    :return:
    """
    parser = argparse.ArgumentParser(description='monitor_exporter')

    parser.add_argument('-f', '--configfile',
                        dest="configfile", help="configuration file")

    parser.add_argument('-p', '--port',
                        dest="port", help="Server port")

    args = parser.parse_args()

    port = 9631

    config_file = 'config.yml'
    if args.configfile:
        config_file = args.configfile

    configuration = config.read_config(config_file)
    if 'port' in configuration:
        port = configuration['port']

    if args.port:
        port = args.port

    log.configure_logger(configuration)

    monitorconnection.MonitorConfig(configuration)
    # Need to create an event loop for apscheduler
    loop = asyncio.new_event_loop()
    # Set the event loop
    asyncio.set_event_loop(loop)

    start_scheduler(configuration)

    log.info(f"Starting web app on port {port}")

    app = Quart(__name__)

    app.register_blueprint(proxy.app, url_prefix='')

    # Use the existing event loop
    app.run(host='0.0.0.0', port=port, loop=loop)


def create_app(config_path=None):
    """
    Used typical from gunicorn if need to pass config file different from default, e.g.
    gunicorn -b localhost:5000 --access-logfile /dev/null -w 4 "wsgi:create_app('/tmp/config.yml')"
    :param config_path:
    :return:
    """
    config_file = 'config.yml'
    if config_path:
        config_file = config_path

    configuration = config.read_config(config_file)

    log.configure_logger(configuration)

    monitorconnection.MonitorConfig(configuration)

    start_scheduler(configuration)
    log.info('Starting web app')

    app = Quart(__name__)
    app.register_blueprint(proxy.app, url_prefix='')

    return app


def start_scheduler(configuration):
    if 'cache' in configuration:

        scheduler = AsyncIOScheduler()
        seconds = default_interval if configuration.get('cache').get('interval') is None \
            else configuration.get('cache').get('interval')
        ttl = default_ttl if configuration.get('cache').get('ttl') is None \
            else configuration.get('cache').get('ttl')
        log.info(f"Monitor collector will run every {seconds} sec")
        # Run once at start up
        monitorconnection.MonitorConfig().collect_cache(ttl)
        scheduler.add_job(monitorconnection.MonitorConfig().collect_cache, trigger='interval', args=[ttl],
                          seconds=seconds)
        scheduler.start()
