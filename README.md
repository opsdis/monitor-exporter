# monitor-exporter

## About
Prometheus exporter written in Python 3. The idea is to utilize OP5 Monitors API to fetch performance data and publish it in a way that lets prometheus scrape the performance data as metrics.

## Prerequsites
- flask
- requests

## Configuration
### monitor-exporter
All configuration is made in the config.yml file.

Example:
```
op5monitor:
  host: monitor.aw.oc-testbench.xyz # FQDN or IP to OP5 Monitor server
  user: monitor # Username of a user with permission to access the API
  passwd: monitor # The users password
  metric_prefix: monitor # Which prefix that you want on the metric names
  custom_vars:
    - env: # Specify which custom_vars to extract from Monitor
        label_name: environment # Name of the label in Prometheus
    - site: # Another example of a custom_var
        label_name: dc # Which will be renamned as dc in this case
```
### Prometheus

Example configuration:
```
prometheus.yml

scrape_configs:
  - job_name: 'monitor'
    metrics_path: /metrics
    static_configs:
      - targets:
        - monitor
        - google.se
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:5000
```

## Instructions
```
Clone repo
$ git clone

Change directory
$ cd monitor-exporter

Edit config file
$ vim config.yml

Start application
$ python3 __main__.py

Check if exporter is working. Target is a host that exists in Monitor.
$ curl -s http://localhost:5000/metrics?target=monitor
```


## Other
### Change port
The web app will bind on port 5000 if nothing else is specified. If you want to run the app on another port start it with the `-p` flag
```
$ python3 __main__.py -p 9999
```

### Troubleshooting
Application logs can be found in `monitor_exporter.log`.