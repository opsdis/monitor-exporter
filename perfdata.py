import requests, urllib3, json, re
from requests.auth import HTTPBasicAuth

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Perfdata:
    def __init__(self, url, user, password, query):
        self.url = url
        self.user = user
        self.password = password
        self.query = query

    def _get_data(self):
        data_from_monitor = requests.get('https://' + self.url + '/api/filter/query?query=' + self.query, auth=HTTPBasicAuth(self.user, self.password), verify=False, headers={'Content-Type' : 'application/json'})
        self.data_json = json.loads(data_from_monitor.content)
        return self.data_json

    def get_perfdata(self):
        self._get_data()

        perfdatadict = {}
       
        for item in self.data_json:
            if 'perf_data' in item and item['perf_data'] != []:
                perfdata = item['perf_data']
            for key, value in perfdata.items():
                for nested_key, nested_value in value.items():
                    if nested_key.endswith('value'):
                        prometheus_key = item['description'] + '_' + key
                        prometheus_key = prometheus_key.replace(' ', '_')
                        prometheus_key = prometheus_key.lower()
                        perfdatadict.update({prometheus_key: str(nested_value)})
        return perfdatadict