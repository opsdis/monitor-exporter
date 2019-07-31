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
        perfdata_from_monitor = requests.get('https://' + self.url + '/api/filter/query?query=' + self.query, auth=HTTPBasicAuth(self.user, self.password), verify=False, headers={'Content-Type' : 'application/json'})
        self.perfdata_json = json.loads(perfdata_from_monitor.content)
        return self.perfdata_json

    def get_perfdata(self):
        self.get_data()

        perfdict = {}
        
        length = len(self.perfdata_json)
        for i in range(length):
            length_perfdata = len(self.perfdata_json[i]['perf_data'])
            perfd = self.perfdata_json[i]['perf_data']
            if length_perfdata != 0:
                #print(perfd)
                for k, v in perfd.items():
                    #print(k)
                    for nestk, nestv in v.items():
                        newkey = self.perfdata_json[i]['description'] + '_' + k + '_' + nestk
                        newkey = newkey.replace(' ', '_')
                        newkey = newkey.lower()
                        perfdict.update({newkey: nestv})
        return perfdict