import requests, urllib3, json, re
from requests.auth import HTTPBasicAuth

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Perfdata:
    def __init__(self, monitor_address, user, password, query_hostname):
        self.url = 'https://' + monitor_address + '/api/filter/query?query=[services]%20host.name="' + query_hostname + '"&columns=host.name,description,perf_data'
        self.user = user
        self.password = password

    def _get_data(self):
        data_from_monitor = requests.get(self.url, auth=HTTPBasicAuth(self.user, self.password), verify=False, headers={'Content-Type' : 'application/json'})
        self.data_json = json.loads(data_from_monitor.content)
        return self.data_json

    def get_perfdata(self):
        self._get_data()

        self.perfdatadict = {}
       
        for item in self.data_json:
            if 'perf_data' in item and item['perf_data'] != []:
                perfdata = item['perf_data']
            for key, value in perfdata.items():
                for nested_key, nested_value in value.items():
                    if nested_key == 'value':
                        prometheus_key = item['description'] + '_' + key
                        prometheus_key = prometheus_key.replace(' ', '_')
                        prometheus_key = prometheus_key.lower()
                        self.perfdatadict.update({prometheus_key: str(nested_value)})
        return self.perfdatadict

    def prometheus_format(self):
        #perfdata = self.perfdatadict
        for key, value in self.perfdatadict.items():
            print(key + ' ' + value)