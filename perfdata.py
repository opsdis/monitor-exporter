import requests, urllib3, json
from requests.auth import HTTPBasicAuth

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Perfdata:
    def __init__(self, url, user, password, query):
        self.url = url
        self.user = user
        self.password = password
        self.query = query

    def get_data(self):
        data_from_monitor = requests.get('https://' + self.url + '/api/filter/query?query=' + self.query, auth=HTTPBasicAuth(self.user, self.password), verify=False, headers={'Content-Type' : 'application/json'})
        self.data_json = json.loads(data_from_monitor.content)
        return self.data_json

    def get_perfdata(self):
        self.get_data()

        perfdatadict = {}
        
        data_length = len(self.data_json)
        for i in range(data_length):
            perfdata_length = len(self.data_json[i]['perf_data'])
            perfdata = self.data_json[i]['perf_data']
            if perfdata_length != 0:
                for key, value in perfdata.items():
                    for nested_key, nested_value in value.items():
                        newkey = self.data_json[i]['description'] + '_' + key + '_' + nested_key
                        newkey = newkey.replace(' ', '_')
                        newkey = newkey.lower()
                        perfdatadict.update({newkey: nested_value})
        return perfdatadict