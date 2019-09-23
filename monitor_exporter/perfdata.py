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
import monitor_exporter.monitorconnection as Monitor

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Perfdata:

    def __init__(self, monitor: Monitor, query_hostname: str):
        # Get Monitor configuration and build URL
        self.monitor = monitor
        self.query_hostname = query_hostname
        self.prefix = monitor.get_prefix()
        self.labels = monitor.get_labels()
        self.perfname_to_label = monitor.get_perfname_to_label()
        self.perfdatadict = {}

    async def get_perfdata(self):
        # Use _get_data method to fetch performance data from Monitor
        data_json = await self.monitor.get_perfdata(self.query_hostname)

        # Use prometheus_labels method to fetch extra labels
        host_custom_vars_labels = await self.prometheus_labels()

        check_command_regex = re.compile(r'^.+?[^!\n]+')

        # Select items that has performance data and skip items that doesn't
        for item in data_json:
            if 'perf_data' in item and item['perf_data']:
                check_command = check_command_regex.search(item['check_command']).group()

                perfdata = item['perf_data']
                labels = {'hostname': item['host']['name'], 'service': item['description']}
                # Add the host custom variables
                labels.update(host_custom_vars_labels)

                # For each perfname in perfdata
                for perf_data_key, perf_data_value in perfdata.items():
                    # get the value and unit
                    perf_unit, perf_value = Perfdata.get_perfdata_value_unit(perf_data_value)

                    normilized_value, unit = Perfdata.normalize_to_unit(perf_value, perf_unit)

                    prometheus_key = self.get_metrics_name(check_command, perf_data_key, unit)

                    if check_command in self.perfname_to_label:
                        labels.update(
                            Perfdata.add_labels_by_items(self.perfname_to_label[check_command]['label_name'],
                                                         perf_data_key))

                    prometheus_key_with_labels = Perfdata.concat_metrics_name_and_labels(labels, prometheus_key)

                    self.perfdatadict.update({prometheus_key_with_labels: str(normilized_value)})

        return self.perfdatadict

    @staticmethod
    def get_perfdata_value_unit(value: dict) -> tuple:
        perf_value = ''
        perf_unit = ''
        if 'value' in value:
            perf_value = value['value']
        if 'unit' in value:
            perf_unit = value['unit']
        return perf_unit, perf_value

    def get_metrics_name(self, check_command, key, unit):
        if unit:
            if check_command in self.perfname_to_label:
                prometheus_key = self.prefix + check_command + '_' + unit
            else:
                prometheus_key = self.prefix + check_command + '_' + key.lower() + '_' + unit
        else:
            if check_command in self.perfname_to_label:
                prometheus_key = self.prefix + check_command
            else:
                prometheus_key = self.prefix + check_command + '_' + key.lower()
        prometheus_key = Perfdata.rem_illegal_chars(prometheus_key)
        return prometheus_key

    async def prometheus_labels(self):
        # Extract metric labels from custom_vars
        monitor_custom_vars = await self.monitor.get_custom_vars(self.query_hostname)
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

    @staticmethod
    def rem_illegal_chars(prometheus_key):
        # Replace illegal characters in metric name
        prometheus_key = prometheus_key.replace(' ', '_')
        prometheus_key = prometheus_key.replace('-', '_')
        prometheus_key = prometheus_key.replace('/', 'slash')
        prometheus_key = prometheus_key.replace('%', 'percent')
        return prometheus_key

    @staticmethod
    def normalize_to_unit(value, unit):
        """Normalize the value to the unit returned.
        We use base-1000 for second-based units, and base-1024 for
        byte-based units. Sadly, the Nagios-Plugins specification doesn't
        disambiguate base-1000 (KB) and base-1024 (KiB).
        """
        if unit == '%':
            return value / 100, 'ratio'
        if unit == 's':
            return value, 'seconds'
        if unit == 'ms':
            return value / 1000.0, 'seconds'
        if unit == 'us':
            return value / 1000000.0, 'seconds'
        if unit == 'B':
            return value, 'bytes'
        if unit == 'KB':
            return value * 1024, 'bytes'
        if unit == 'MB':
            return value * 1024 * 1024, 'bytes'
        if unit == 'GB':
            return value * 1024 * 1024 * 1024, 'bytes'
        if unit == 'TB':
            return value * 1024 * 1024 * 1024 * 1024, 'bytes'

        return value, ''

    @staticmethod
    def concat_metrics_name_and_labels(labels: dict, prometheus_key: str) -> str:
        """
        Build metric name with labels like
        metrics_name{label1="value1, .... }
        :param labels:
        :param prometheus_key:
        :return:
        """

        labelstring = Perfdata.labels_string(labels)
        prometheus_key = prometheus_key + '{' + labelstring + '}'

        return prometheus_key

    @staticmethod
    def labels_string(labels: dict) -> str:
        """
        Create a comma separated string of
        labels1=value1, ....
        :param labels:
        :return:
        """
        labelstring = ''
        sep = ''
        for label_key, label_value in labels.items():
            # Can only add custom vars that are simple strings. In incinga these can be complex dict structures
            # if type(label_value) is str or type(label_value) is int:
            if type(label_value) is str:
                labelstring += sep + label_key + '="' + label_value + '"'
                sep = ', '
        return labelstring

    @staticmethod
    def add_labels_by_items(label: str, key: str) -> dict:
        item_label = {label.lower(): key}
        return item_label
