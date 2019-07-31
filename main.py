"""
- Din tjänst skall kunna ta en emot en filter query
- Gör anrop mot Monitor över apiet med en filter query
- Retunera tillbaka en dictionary av perfdata samt en dictionary av labels
- Labels är allt annat som frågan filter retunerar som inte är perfdata tex hostname, servicename, ...
"""
import json
from perfdata import Perfdata

# Create new Perfdata object
class_test = Perfdata('monitor.aw.oc-testbench.xyz', 'monitor', 'monitor', 'monitor')

# Fetch performance data from Monitor
class_test.get_perfdata()

#print(json.dumps(class_test.get_perfdata(), indent=4, sort_keys=True))

#Print in prometheus format
print(class_test.prometheus_format())
