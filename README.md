# monitor-exporter

## About
Prometheus exporter written in Python 3. The idea is to utilize OP5 Monitors API to fetch performance data and publish it in a way that lets prometheus scrape the performance data as metrics.

## Prerequsites
- flask
- requests

## Configuration
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

## Instructions
```
Clone repo
# git clone

Change directory
# cd monitor-exporter

Edit config file
# vim config.yml

Start application
# python3 __main__.py
```

## Other
### Change port
The web app will bind on port 5000 if nothing else is specified. If you want to run the app on another port start it with the `-p` flag
```
# python3 __main__.py -p 9999
```

### Troubleshooting
Application logs can be found in `monitor_exporter.log`.