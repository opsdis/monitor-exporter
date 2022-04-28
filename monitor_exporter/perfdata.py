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
import monitor_exporter.log as log

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOSTNAME = 'hostname'
SERVICE = 'service'
NAN = 'NaN'

check_command_regex = re.compile(r'^.+?[^!\n]+')


class Perfdata:

    def __init__(self, monitor: Monitor, query_hostname: str):
        # Get Monitor configuration and build URL
        self.monitor = monitor
        self.query_hostname = query_hostname
        self.prefix = monitor.get_prefix()
        self.allow_nan = monitor.is_allow_nan()
        self.configured_labels = monitor.get_configured_labels()
        self.perfname_to_label = monitor.get_perfname_to_label()
        self.perfdatadict = {}

    async def get_perfdata(self):

        # Use prometheus_labels method to fetch extra labels
        host_data = await self.monitor.get_host_data(self.query_hostname)

        custom_vars = {}
        host_state = None
        host_check_command = None
        host_perf_data = None

        if 'custom_variables' in host_data:
            custom_vars = host_data['custom_variables']
        if 'state' in host_data:
            host_state = host_data['state']
        if 'perf_data' in host_data:
            host_perf_data = host_data['perf_data']
        if 'check_command' in host_data:
            host_check_command = check_command_regex.search(host_data['check_command']).group()

        host_custom_vars_labels = self.prometheus_labels(custom_vars)

        # Host state
        labels = {HOSTNAME: self.query_hostname}
        labels.update(host_custom_vars_labels)

        # Additional labels for downtime,
        if 'downtime' in host_data:
            labels['downtime'] = str(host_data['downtime']).lower()
        if 'is_flapping' in host_data:
            labels['flapping'] = str(host_data['is_flapping'])
        if 'address' in host_data:
            labels['address'] = host_data['address']
        if 'acknowledged' in host_data:
            labels['acknowledged'] = str(host_data['acknowledged'])

        if host_state is not None:
            normalized_value, prometheus_key_with_labels = self.create_metric('host', labels,
                                                                              'state',
                                                                              {'value': int(host_state)})
            self.perfdatadict.update({prometheus_key_with_labels: str(normalized_value)})

        if host_check_command and host_perf_data:
            labels.update({SERVICE: 'isalive'})
            for perf_data_key, perf_data_value in host_perf_data.items():
                normalized_value, prometheus_key_with_labels = self.create_metric(host_check_command, labels,
                                                                                  perf_data_key, perf_data_value)

                if normalized_value != NAN or self.allow_nan:
                    self.perfdatadict.update({prometheus_key_with_labels: str(normalized_value)})
                else:
                    log.warn("Missing value - dropping",
                             {'host': self.query_hostname, 'check_command': host_check_command})

        service_state_histo = {
            'bucket': {'0': 0, '1': 0, '2': 0, '+Inf': 0},
            '_count': 0,
            '_sum': 0
        }

        service_data = []
        if 'services' in host_data:
            service_data = host_data['services']

        for item in service_data:
            check_command = check_command_regex.search(item['check_command']).group()
            labels = {HOSTNAME: item['host']['name'], SERVICE: item['description']}
            # Add the host custom variables
            labels.update(host_custom_vars_labels)

            if 'downtime' in host_data and bool(host_data['downtime']):
                labels['downtime'] = str(host_data['downtime']).lower()
            elif 'downtime' in item:
                labels['downtime'] = str(item['downtime']).lower()
            if 'address' in host_data:
                labels['address'] = host_data['address']
            if 'is_flapping' in item:
                labels['flapping'] = str(item['is_flapping'])
            if 'acknowledged' in item:
                labels['acknowledged'] = str(item['acknowledged'])

            # For state if exists 0 OK, 1 Warning and 2 Critical
            if 'state' in item:
                normalized_value, prometheus_key_with_labels = self.create_metric_state(labels,
                                                                                        {'value': int(item['state'])})
                self.perfdatadict.update({prometheus_key_with_labels: str(normalized_value)})

                if int(item['state']) == 0:
                    service_state_histo['bucket']['0'] += 1
                elif int(item['state']) == 1:
                    service_state_histo['bucket']['1'] += 1
                elif int(item['state']) == 2:
                    service_state_histo['bucket']['2'] += 1
                else:
                    service_state_histo['bucket']['+Inf'] += 1
                service_state_histo['_count'] += 1
                service_state_histo['_sum'] += int(item['state'])

            if 'perf_data' in item and item['perf_data']:

                perfdata = item['perf_data']

                # For each perfname in perfdata
                for perf_data_key, perf_data_value in perfdata.items():
                    # get the value and unit

                    normalized_value, prometheus_key_with_labels = self.create_metric(check_command, labels,
                                                                                      perf_data_key,
                                                                                      perf_data_value)

                    if normalized_value != NAN or self.allow_nan:
                        self.perfdatadict.update({prometheus_key_with_labels: str(normalized_value)})
                    else:
                        log.warn("Missing value - dropping",
                                 {'host': self.query_hostname, 'service': item['description'],
                                  'check_command': check_command})
        # self.create_service_state_histogram(service_state_histo, labels={HOSTNAME: self.query_hostname})

        return self.perfdatadict

    def create_service_state_histogram(self, histo: dict, labels: dict):
        name = 'service_state_by_host_bucket'
        for bucket, count in histo['bucket'].items():
            bucket_label = labels
            bucket_label['le'] = f"{bucket}"
            mertic_name = self.prefix + name + '{' + Perfdata.labels_string(labels) + '}'
            self.perfdatadict.update({mertic_name: str(count)})

        labels.pop('le')
        mertic_name = self.prefix + name + '_count{' + Perfdata.labels_string(labels) + '}'
        self.perfdatadict.update({mertic_name: str(histo['_count'])})
        mertic_name = self.prefix + name + '_sum{' + Perfdata.labels_string(labels) + '}'
        self.perfdatadict.update({mertic_name: str(histo['_sum'])})

    def create_metric(self, check_command, labels, perf_data_key, perf_data_value):

        perf_unit, perf_value, perf_warn, perf_crit = Perfdata.get_perfdata_value_unit(perf_data_value)

        normilized_value, unit = Perfdata.normalize_to_unit(perf_value, perf_unit)
        prometheus_key = self.get_metrics_name(check_command, perf_data_key, unit)
        if check_command in self.perfname_to_label:
            labels.update(
                Perfdata.add_labels_by_items(self.perfname_to_label[check_command]['label_name'],
                                             perf_data_key))
        prometheus_key_with_labels = Perfdata.concat_metrics_name_and_labels(labels, prometheus_key)
        return normilized_value, prometheus_key_with_labels

    def create_metric_state(self, labels, state_value):

        perf_unit, perf_value, perf_warn, perf_crit = Perfdata.get_perfdata_value_unit(state_value)

        normalized_value, unit = Perfdata.normalize_to_unit(perf_value, perf_unit)
        prometheus_key = self.prefix + 'service_state'

        prometheus_key_with_labels = Perfdata.concat_metrics_name_and_labels(labels, prometheus_key)
        return normalized_value, prometheus_key_with_labels

    @staticmethod
    def get_perfdata_value_unit(value: dict) -> tuple:
        perf_value = ''
        perf_unit = ''
        perf_warn = ''
        perf_crit = ''
        if 'value' in value:
            perf_value = value['value']
        if 'unit' in value:
            perf_unit = value['unit']
        if 'warn' in value:
            perf_warn = value['warn']
        if 'crit' in value:
            perf_crit = value['crit']

        return perf_unit, perf_value, perf_warn, perf_crit

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

    def prometheus_labels(self, monitor_custom_vars):
        """
        Extract metric labels from custom_vars.
        Only defined custom vars are selected - see config.yml

        :return:
        custom_vars = {}
        for var in custom_vars_json:
            custom_vars = var['custom_variables']

        """

        new_labels = {}

        if monitor_custom_vars:
            # Make all variables to lower
            monitor_custom_vars = {k.lower(): v for k, v in monitor_custom_vars.items()}

            # Translate if configured
            for key, value in monitor_custom_vars.items():
                if key in self.configured_labels:
                    new_labels.update({self.configured_labels[key]: value})
                elif self.monitor.is_all_custom_vars():
                    new_labels.update({key: value})

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
        if isinstance(value, str):
            return NAN, ''
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
