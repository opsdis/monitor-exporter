import requests, urllib3, json, re
from requests.auth import HTTPBasicAuth

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Perfdata:
    def __init__(self, monitor_address, user, password, query_hostname):
        self.url = 'https://' + monitor_address + '/api/filter/query?query=[services]%20host.name="' + query_hostname + '"&columns=host.name,description,perf_data,check_command'
        self.user = user
        self.password = password

    def _get_data(self):
        data_from_monitor = requests.get(self.url, auth=HTTPBasicAuth(self.user, self.password), verify=False, headers={'Content-Type' : 'application/json'})
        self.data_json = json.loads(data_from_monitor.content)
        return self.data_json

    def get_perfdata(self):
        self._get_data()

        self.perfdatadict = {}

        check_command_regex = re.compile(r'^.+?[^!\n]+')
       
        for item in self.data_json:
            if 'perf_data' in item and item['perf_data'] != []:
                perfdata = item['perf_data']
            for key, value in perfdata.items():
                for nested_key, nested_value in value.items():
                    if nested_key == 'value':
                        check_command = check_command_regex.search(item['check_command'])
                        prometheus_key = 'monitor_' + check_command.group() + '_' + key.lower()
                        prometheus_key = prometheus_key.replace(' ', '_')
                        prometheus_key = prometheus_key + '{hostname="' + item['host']['name'] + '"' + ', service="' + item['description'] + '"}'
                        self.perfdatadict.update({prometheus_key: str(nested_value)})
        return self.perfdatadict

    def prometheus_format(self):
        for key, value in self.perfdatadict.items():
            print(key + ' ' + value)