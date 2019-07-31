"""
- Din tjänst skall kunna ta en emot en filter query
- Gör anrop mot Monitor över apiet med en filter query
- Retunera tillbaka en dictionary av perfdata samt en dictionary av labels
- Labels är allt annat som frågan filter retunerar som inte är perfdata tex hostname, servicename, ...
"""
import json
from perfdata import Perfdata


class_test = Perfdata('monitor.aw.oc-testbench.xyz', 'monitor', 'monitor', '[services]%20all&columns=host.name,description,perf_data')

print(json.dumps(class_test.get_perfdata(), indent=4, sort_keys=True))