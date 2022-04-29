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
import json
import time

import aiohttp
import redis
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict

import monitor_exporter.log as log


class Singleton(type):
    """
    Provide singleton pattern to MonitorConfig. A new instance is only created if:
     - instance do not exists
     - config is provided in constructor call, __init__
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances or args:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MonitorConfig(object, metaclass=Singleton):
    config_entry = 'op5monitor'
    # high number so all services is fetched
    default_limit = '10000'

    def __init__(self, config=None):
        """
        The constructor takes on single argument that is a config dict
        :param config:
        """
        self.is_cache = False
        if config:
            self.is_cache = False if 'cache' not in config else True

        if self.is_cache:
            self.redis_host = 'localhost' if config.get('cache').get('redis').get('host') is None else config.get(
                'cache').get('redis').get('host')
            self.redis_port = '6379' if config.get('cache').get('redis').get('port') is None else config.get(
                'cache').get('redis').get('port')
            self.redis_db = '0' if config.get('cache').get('redis').get('db') is None else config.get(
                'cache').get('redis').get('db')
            self.redis_auth = None if config.get('cache').get('redis').get('auth') is None else config.get(
                'cache').get('redis').get('auth')

        self.user = ''
        self.passwd = ''
        self.host = ''
        self.headers = {'content-type': 'application/json'}
        self.verify = False
        self.retries = 5
        self.timeout = 5
        self.prefix = ''
        self.labels = []
        self.url_query_service_data = ''
        self.perfname_to_label = []
        self.allow_all_custom_vars = False
        self.allow_nan = False

        if config:
            self.user = config[MonitorConfig.config_entry]['user']
            self.passwd = config[MonitorConfig.config_entry]['passwd']
            self.host = config[MonitorConfig.config_entry]['url']
            if 'metric_prefix' in config[MonitorConfig.config_entry]:
                self.prefix = config['op5monitor']['metric_prefix'] + '_'
            if 'host_custom_vars' in config[MonitorConfig.config_entry]:
                self.labels = config['op5monitor']['host_custom_vars']
            if 'perfnametolabel' in config[MonitorConfig.config_entry]:
                self.perfname_to_label = config[MonitorConfig.config_entry]['perfnametolabel']
            if 'timeout' in config[MonitorConfig.config_entry]:
                self.timeout = int(config[MonitorConfig.config_entry]['timeout'])
            if 'verify' in config[MonitorConfig.config_entry]:
                self.verify = bool(config[MonitorConfig.config_entry]['verify'])
            if 'all_custom_vars' in config[MonitorConfig.config_entry]:
                self.allow_all_custom_vars = bool(config[MonitorConfig.config_entry]['all_custom_vars'])
            if 'allow_nan' in config[MonitorConfig.config_entry]:
                self.allow_nan = bool(config[MonitorConfig.config_entry]['allow_nan'])

            # Collect service data for a single host
            self.url_query_service_data = self.host + \
                                          '/api/filter/query?query=[services]%20host.name="{}' \
                                          '"&columns=host.name,description,perf_data,check_command,state,' \
                                          'downtimes,acknowledged,is_flapping' \
                                          '&limit=' + self.default_limit

            # Collect host data for a single host
            self.url_get_host = self.host + \
                                '/api/filter/query?query=[hosts]%20name="{}' \
                                '"&columns=address,custom_variables,perf_data,check_command,state,' \
                                'downtimes,acknowledged,is_flapping'

            # Collect service data for all services - used in cache mode
            self.url_query_all_service_data = self.host + \
                                              '/api/filter/{}?query=[services]%20all' \
                                              '&columns=host.name,description,perf_data,check_command,state,' \
                                              'downtimes,acknowledged,is_flapping'

            # # Collect host data for all hosts - used in cache mode
            self.url_query_all_host = self.host + \
                                      '/api/filter/{}?query=[hosts]%20all' \
                                      '&columns=name,address,custom_variables,perf_data,check_command,state,' \
                                      'downtimes,acknowledged,is_flapping'

            self.url_downtime = self.host + \
                                '/api/filter/{}?query=[downtimes]%20all' \
                                '&columns=id,start_time,end_time,fixed'

    def get_user(self) -> str:
        return self.user

    def get_passwd(self) -> str:
        return self.passwd

    def get_header(self) -> Dict[str, str]:
        return self.headers

    def get_verify(self) -> bool:
        return self.verify

    def get_timeout(self) -> int:
        return self.timeout

    def get_url(self) -> str:
        return self.host

    def number_of_retries(self) -> int:
        return self.retries

    def get_prefix(self) -> str:
        return self.prefix

    def is_all_custom_vars(self) -> bool:
        return self.allow_all_custom_vars

    def is_allow_nan(self) -> bool:
        return self.allow_nan

    def get_configured_labels(self):
        labeldict = {}

        for label in self.labels:
            for custom_var, value in label.items():
                for key, prom_label in value.items():
                    labeldict.update({custom_var: prom_label})
        return labeldict

    def get_perfname_to_label(self):
        return self.perfname_to_label

    async def get_host_data(self, hostname):
        """
        Build new URL and get custom_vars from Monitor
        :param hostname:
        :return:
        """

        if self.is_cache:
            host_data = await self.get_cache_host_data(hostname)
        else:
            host_data_list = await self.get(self.url_get_host.format(hostname))
            service_data = await self.get(self.url_query_service_data.format(hostname))
            if host_data_list:
                host_data = host_data_list[0]
                host_data['services'] = service_data
            else:
                host_data = list()

        return host_data

    def get_sync(self, url):
        data_json = {}

        try:
            data_from_monitor = requests.get(url, auth=HTTPBasicAuth(self.user, self.passwd),
                                             verify=self.get_verify(), headers=self.get_header(),
                                             timeout=self.get_timeout())
            data_from_monitor.raise_for_status()

            log.debug('API call: ' + data_from_monitor.url)
            if data_from_monitor.status_code != 200:
                log.info("Response", {'status': data_from_monitor.status_code, 'error': data_json['error'],
                                      'full_error': data_json['full_error']})
            else:
                data_json = json.loads(data_from_monitor.content)
                log.info("call api {}".format(url), {'status': data_from_monitor.status_code,
                                                     'response_time': data_from_monitor.elapsed.total_seconds()})
        except requests.exceptions.RequestException as err:
            log.error("{}".format(str(err)))
            raise err

        return data_json

    async def get(self, url):

        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=aiohttp.BasicAuth(self.user, self.passwd),
                                   verify_ssl=False,
                                   headers=self.get_header()) as response:
                re = await response.text()
                return json.loads(re)

    async def get_cache_service_data(self, hostname):
        r = self.get_cache_connection()

        data = r.get(self.key_services(hostname))
        if data:
            return json.loads(data)
        else:
            return []

    async def get_cache_host_data(self, host_name):
        r = self.get_cache_connection()

        data = r.get(self.key_hosts(host_name))
        if data:
            return json.loads(data)
        else:
            return {}

    def collect_cache(self, ttl: int = 300):
        """
        Collect Monitor data for all objects and store in cache
        :param ttl:
        :return:
        """
        try:
            # Get downtime
            now = int(time.time())
            ongoing_downtime = set()
            # Get the count to know how many to query
            count_downtimes = self.get_sync(self.url_downtime.format('count'))
            if 'count' in count_downtimes and int(count_downtimes['count']) > 0:
                count = count_downtimes['count']

                downtimes = self.get_sync(self.url_downtime.format('query') + '&limit=' + str(count))

                for downtime in downtimes:

                    if downtime['start_time'] <= now <= downtime['end_time']:
                        # downtime['id'] is an int -> make it to a str to compare in set
                        ongoing_downtime.add(downtime['id'])

            # Get the service data from Monitor
            start_time = time.time()
            count_services = self.get_sync(self.url_query_all_service_data.format('count'))

            hosts_to_services = {}

            services_flat = []
            if 'count' in count_services:
                count = count_services['count']
                services_flat = self.get_sync(self.url_query_all_service_data.format('query') + '&limit=' + str(count))
                for service_item in services_flat:
                    if service_item['host']['name'] not in hosts_to_services:
                        hosts_to_services[service_item['host']['name']] = []
                    host_name = service_item['host']['name']
                    downtime = set(service_item.pop('downtimes'))
                    if downtime & ongoing_downtime:
                        service_item['downtime'] = True
                    else:
                        service_item['downtime'] = False

                    hosts_to_services[host_name].append(service_item)

            # Get the host data from Monitor
            count_hosts = self.get_sync(self.url_query_all_host.format('count'))
            hosts = []
            if 'count' in count_hosts:
                count = count_hosts['count']
                hosts = self.get_sync(self.url_query_all_host.format('query') + '&limit=' + str(count))

            start_redis_time = time.time()
            # Save host objects
            hosts_set = set()
            r = self.get_cache_connection()
            p = r.pipeline()
            for host in hosts:
                host_name = host['name']
                downtime = set(host.pop('downtimes'))
                if downtime & ongoing_downtime:
                    host['downtime'] = True
                else:
                    host['downtime'] = False

                hosts_set.add(host_name)
                if host_name in hosts_to_services:
                    host['services'] = hosts_to_services[host_name]
                p.set(self.key_hosts(host_name), json.dumps(host))
                p.expire(self.key_hosts(host_name), ttl)
            p.execute()

            # Build host index
            r = self.get_cache_connection()
            existing_hosts = r.smembers(self.key_host_index())
            log.info(f"Existing hosts {len(existing_hosts)}")
            log.info(f"Monitor hosts {len(hosts_set)}")

            del_hosts = existing_hosts - hosts_set
            add_hosts = hosts_set - existing_hosts
            log.info(f"Delete hosts {len(del_hosts)}")
            log.info(f"Add hosts {len(add_hosts)}")

            existing_downtimes = set(map(int, r.smembers(self.key_downtime_index())))
            log.info(f"Existing downtimes {len(existing_downtimes)}")
            log.info(f"Monitor downtimes {len(ongoing_downtime)}")
            del_downtimes = existing_downtimes - ongoing_downtime
            add_downtimes = ongoing_downtime - existing_downtimes
            log.info(f"Delete downtimes {len(del_downtimes)}")
            log.info(f"Add downtimes {len(add_downtimes)}")

            p = r.pipeline()
            for host in add_hosts:
                p.sadd(self.key_host_index(), host)
            for host in del_hosts:
                p.srem(self.key_host_index(), host)

            for downtime in add_downtimes:
                p.sadd(self.key_downtime_index(), downtime)
            for downtime in del_downtimes:
                p.srem(self.key_downtime_index(), downtime)

            p.expire(self.key_host_index(), ttl)
            p.expire(self.key_downtime_index(), ttl)
            p.execute()

            end_time = time.time()

            log.info(
                f"Monitor collector exec time total {(end_time - start_time)} "
                f"redis write {len(services_flat) + len(hosts)} objects in {end_time - start_redis_time}")
        except Exception as err:
            log.error(
                f"Monitor collector failed with {str(err)}")

    def key_services(self, host):
        return host + ':services'

    def key_hosts(self, host_name):
        return host_name + ":host"

    def key_host_index(self) -> str:
        return "hosts"

    def key_downtime_index(self) -> str:
        return "downtimes"

    def get_cache_connection(self):
        return redis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db, password=self.redis_auth,
                           decode_responses=True)
