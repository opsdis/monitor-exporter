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
import yaml

import exporterlog

class MonitorConfig:

    def __init__(self):
        with open("config.yml", 'r') as ymlfile:
            monitor = yaml.load(ymlfile)
        self.user = monitor['op5monitor']['user']
        self.passwd = monitor['op5monitor']['passwd']
        self.host = monitor['op5monitor']['host']
        self.headers = {'content-type': 'application/json'}
        self.verify = False
        self.retries = 5
        self.prefix = monitor['op5monitor']['metric_prefix'] + '_'
        self.labels = monitor['op5monitor']['custom_vars']

    def get_user(self):
        return self.user

    def get_passwd(self):
        return self.passwd

    def get_header(self):
        return self.headers

    def get_verify(self):
        return self.verify

    def get_host(self):
        return self.host

    def number_of_retries(self):
        return self.retries
    
    def get_prefix(self):
        return self.prefix
    
    def get_labels(self):
        labeldict = {}
        for label in self.labels:
            for custom_var, value in label.items():
                for key, prom_label in value.items():
                    labeldict.update({custom_var: prom_label})
        return labeldict
