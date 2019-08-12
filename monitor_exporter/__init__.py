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
from flask import Flask
import monitor_exporter.log as log
import monitor_exporter.monitorconnection as monitorconnection
import monitor_exporter.proxy as proxy
import monitor_exporter.fileconfiguration as config


#app = Flask(__name__)

#config_file = 'config.yml'

#config = config.read_config(config_file)

#log.configure_logger(config)

#monitorconnection.MonitorConfig(config)

#app.register_blueprint(proxy.app, url_prefix='/')