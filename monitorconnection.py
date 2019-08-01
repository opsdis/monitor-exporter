# -*- coding: utf-8 -*-
"""
    Copyright (C) 2018  Opsdis AB

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

class MonitorConnection:

    def __init__(self):
        with open("config.yml", 'r') as ymlfile:
            monitor = yaml.load(ymlfile)
        self.user = monitor['op5monitor']['user']
        self.passwd = monitor['op5monitor']['passwd']
        self.host = monitor['op5monitor']['host']
        self.headers = {'content-type': 'application/json'}
        self.verify = False
        self.retries = 5
        
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