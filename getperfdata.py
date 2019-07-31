"""
- Din tjänst skall kunna ta en emot en filter query
- Gör anrop mot Monitor över apiet med en filter query
- Retunera tillbaka en dictionary av perfdata samt en dictionary av labels
- Labels är allt annat som frågan filter retunerar som inte är perfdata tex hostname, servicename, ...
"""
import requests, urllib3, json
from requests.auth import HTTPBasicAuth
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'monitor.aw.oc-testbench.xyz'
user = 'monitor'
password = 'monitor'
query = '[services]%20all&columns=host.name,description,perf_data'

r = requests.get('https://' + url + '/api/filter/query?query=' + query, auth=HTTPBasicAuth(user, password), verify=False, headers={'Content-Type' : 'application/json'})
y = json.loads(r.content)

labeldict = {}
perfdict = {}

length = len(y)
print(length)
for i in range(length):
    labeldict.update({'hostname': y[i]['host']['name']})
    #labeldict.update({'service': y[i]['description']})
    lenny = len(y[i]['perf_data'])
    perfd = y[i]['perf_data']
    if lenny != 0:
        print(perfd)
        for k, v in perfd.items():
            print(k)
            print(v)


print(labeldict)