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
import re
import urllib3
import monitorconnection as Monitor

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Perfdata:
    def __init__(self, monitor: Monitor, query_hostname: str):
        # Get Monitor configuration and build URL
        self.monitor = monitor
        self.query_hostname = query_hostname
        self.prefix = monitor.get_prefix()
        self.labels = monitor.get_labels()
        self.perfdatadict = {}

    def get_perfdata(self):
        # Use _get_data method to fetch performance data from Monitor
        data_json = self.monitor.get_perfdata(self.query_hostname)

        # Use prometheus_labels method to fetch extra labels
        new_labels = self.prometheus_labels()

        check_command_regex = re.compile(r'^.+?[^!\n]+')

        # Select items that has performance data and skip items that doesn't
        for item in data_json:
            if 'perf_data' in item and item['perf_data']:
                perfdata = item['perf_data']

                # Go over each perf_data item and construct prometheus metrics
                for key, value in perfdata.items():
                    for nested_key, nested_value in value.items():
                        # Use to_base_units method to convert millisecond to second etc
                        key = self.to_base_units(nested_key, nested_value, value, key)

                    # Create a new dictionary with prometheus metric names and values
                    # Using rem_illegal_chars method to remove illegal characters
                    for nested_key, nested_value in value.items():
                        if nested_key == 'value':
                            check_command = check_command_regex.search(item['check_command'])
                            prometheus_key = self.prefix + check_command.group() + '_' + key.lower()
                            prometheus_key = self.rem_illegal_chars(prometheus_key)
                            prometheus_key = self.add_labels(new_labels, prometheus_key, item)
                            self.perfdatadict.update({prometheus_key: str(nested_value)})

        return self.perfdatadict

    def add_labels(self, new_labels, prometheus_key, item):
        # Build metric labels

        # If host does not have any custom_vars add only default labels, i.e. hostname and service
        if not new_labels:
            prometheus_key = prometheus_key + '{hostname="' + item['host']['name'] + '"' + ', service="' + item[
                'description'] + '"}'

        # Else if host has custom_vars loop through and select custom_vars based on config.yml,
        # skip custom_vars that are not defined in config.yml
        # Rename custom_vars according to config.yml
        else:
            labelstring = ''
            for label_key, label_value in new_labels.items():
                labelstring += ', ' + label_key + '="' + label_value + '"'
            prometheus_key = prometheus_key + '{hostname="' + item['host']['name'] + '"' + ', service="' + item[
                'description'] + '"' + labelstring + '}'
        return prometheus_key

    def rem_illegal_chars(self, prometheus_key):
        # Replace illegal characters in metric name
        prometheus_key = prometheus_key.replace(' ', '_')
        prometheus_key = prometheus_key.replace('-', '_')
        prometheus_key = prometheus_key.replace('/', 'slash')
        prometheus_key = prometheus_key.replace('%', 'percent')
        return prometheus_key

    def to_base_units(self, nested_key, nested_value, value, key):
        # Convert metric value to base units, i.e from milliseconds to seconds etc and add unit to metric name 
        if nested_value == 'ms':
            value['value'] = value['value'] / 1000.0
            key += '_seconds'

        elif nested_value == 's':
            key += '_seconds'

        elif nested_value == '%':
            value['value'] = value['value'] / 100.0
            key += '_ratio'

        elif nested_value == 'B':
            key += '_bytes'
        return key

    def prometheus_labels(self):
        # Extract metric labels from custom_vars
        monitor_custom_vars = self.monitor.get_custom_vars(self.query_hostname)
        new_labels = {}

        if monitor_custom_vars:
            monitor_custom_vars = {k.lower(): v for k, v in monitor_custom_vars.items()}
            for i in self.labels.keys():
                if i in monitor_custom_vars.keys():
                    new_labels.update({self.labels[i]: monitor_custom_vars[i]})
        return new_labels

    def prometheus_format(self):
        # Build prometheus formatted data
        metrics = ''
        for key, value in self.perfdatadict.items():
            metrics += key + ' ' + value + '\n'
        return metrics
