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

r = requests.get('https://' + url + '/api/filter/query?query=' + query + '', auth=HTTPBasicAuth(user, password), verify=False, headers={'Content-Type' : 'application/json'})
y = json.loads(r.content)

labeldict = {}

length = len(y)
print(length)
for i in range(length):
    #print(y[i]['host']['name'])
    labeldict.update({'hostname': y[i]['host']['name']})
    #print(y[i]['description'])
    labeldict.update({'service': y[i]['description']})
    lenny = len(y[i]['perf_data'])
    print(lenny)
    for ds in range(lenny):
        if ds != 0:
            print(y[i]['perf_data'])

print(labeldict)