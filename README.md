[![PyPI version](https://badge.fury.io/py/monitor-exporter.svg)](https://badge.fury.io/py/monitor-exporter)

monitor-exporter
-----------------------

- [Overview](#overview)
- [Metrics naming](#metrics-naming)
    * [Service performance data](#service-performance-data)
    * [Host performance data](#host-performance-data)
    * [State](#state)
    * [Metric labels](#metric-labels)
    * [Performance metrics name to labels](#performance-metrics-name-to-labels)
- [Configuration](#configuration)
    * [monitor-exporter](#monitor-exporter-1)
- [Using Redis cache](#using-redis-cache)
- [Logging](#logging)
- [Prometheus configuration](#prometheus-configuration)
    * [Static config](#static-config)
    * [File discovery config for usage with `monitor-promdiscovery`](#file-discovery-config-for-usage-with--monitor-promdiscovery-)
- [Installing](#installing)
- [Running](#running)
    * [Development with Quart built in webserver](#development-with-quart-built-in-webserver)
    * [Production deployment](#production-deployment)
        + [Deploying with gunicorn](#deploying-with-gunicorn)
    * [Test the connection](#test-the-connection)
- [System requirements](#system-requirements)
- [License](#license)

# Overview

The monitor-exporter utilises ITRS, former OP5, Monitor's API to fetch host and service-based performance data and
publish it in a way that lets Prometheus scrape the performance data and state as metrics.

Benefits:

- Enable advanced queries and aggregation on time series
- Prometheus based alerting rules
- Grafana graphing
- Take advantage of metrics already collected by Monitor, without rerunning checks
- Collect hosts and services performance data and state and translate to Prometheus metrics

This solution is a perfect gateway for any Monitor users that would like to start using Prometheus and Grafana.

# Metrics naming
## Service performance data
Metrics that are scraped with the monitor-exporter will have the following naming structure:

    monitor_<check_command>_<perfname>_<unit>

> Unit is only added if it exists for the performance data

For example the check command `check_ping` will result in two metrics:

    monitor_check_ping_rta_seconds
    monitor_check_ping_pl_ratio

## Host performance data
In Monitor the host also have a check to verify the state of the host. The metric name is always called `monitor_check_host_alive`.
If this check as multiple performance values they will be reported as individual metrics, e.g.

```
monitor_check_host_alive_pkt{hostname="foo.com", environment="production", service="isalive"} 1
monitor_check_host_alive_rta{hostname="foo.com", environment="production", service="isalive"} 2.547
monitor_check_host_alive_pl_ratio{hostname="foo.com", environment="production", service="isalive"} 0.0
```

> Service label will always be `isalive`


## State
State metrics is reported for both hosts and services.
State metrics is reported as value 0 (okay), 1 (warning), 2 (critical) and 4 (unknown).

For hosts the metric name is:

    monitor_host_state

For services the metric name is:

    monitor_service_state


## Metric labels
The monitor-exporter adds a number of labels to each metric:

- **hostname** - is the `host_name` in Monitor
- **service** - is the `service_description` in Monitor
- **downtime** - if the host or service is currently in a downtime period - true/false. If the host is in downtime its
  services are also in downtime. **Attention, downtime is only support if monitor-export is running in cache mode.**
- **address** - the hosts real address
- **acknowledged** - is applicable if a host or service is in warning or critical and have been acknowledged by operations -
  0/1 where 1 is acknowledged.

Optionally the monitor-exporter can be configured to pass all or specific custom variables configured in Monitor as
labels Prometheus.

> Any host based custom variables that is used as labels is also set for its services.

> Labels created from custom variables are all transformed to lowercase.

## Performance metrics name to labels
As described above, the default naming of the Prometheus name is:

    monitor_<check_command>_<perfname>_<unit>

For some check commands this does not work well like for the `self_check_by_snmp_disk_usage_v3` check command where the
perfname are the unique mount paths.
For checks where the perfname is defined depending on a specific name, you can change it so the perfname becomes a
label instead.
This is defined in the configuration like:

```yaml
  perfnametolabel:
    # The command name
    self_check_by_snmp_disk_usage_v3:
      # the label name to be used
      label_name: disk
    check_disk_local_mb:
      label_name: local_disk
```
So if the check command is `self_check_by_snmp_disk_usage_v3`, the Prometheus metrics will have a format like:

    monitor_self_check_by_snmp_disk_usage_v3_bytes{hostname="monitor", service="Disk usage /", disk="/_used"} 48356130816.0

If we did not make this transformation, we would get the following:

    monitor_self_check_by_snmp_disk_usage_v3_slash_used_bytes{hostname="monitor", service="Disk usage /"} 48356130816.0

Which is bad since we get specific metric name from the perfname.

> Please be aware of naming conventions for perfname and services, especially when they include a name depending on
> what is checked like a mountpoint or disk name.


# Configuration
## monitor-exporter
All configuration is made in the config.yml file.

Example:
```yaml

# Port can be overridden by using -p if running development flask
# This is the default port assigned at https://github.com/prometheus/prometheus/wiki/Default-port-allocations
#port: 9631

op5monitor:
  # The url to the Monitor server
  url: https://monitor.example.com
  user: monitor
  passwd: monitor

  # Allow for metrics value that are empty or a string. Will be replaced with NaN. 
  # Default is false and will drop metrics that is NaN
  allow_nan: false
  
  # The prefix for the metric names
  metric_prefix: monitor
  # Example of custom vars that should be added as labels and how to be translated
  host_custom_vars:
    # Specify which custom_vars to extract from Monitor
    - env:
        # Name of the label in Prometheus
        label_name: environment
    - site:
        label_name: dc
  # This section enable that for specific check commands the perfdata metrics name will not be part of the
  # Prometheus metrics name, and is instead moved to a label
  # E.g for the self_check_by_snmp_disk_usage_v3 command the perfdata name will be set to the label disk like:
  # monitor_self_check_by_snmp_disk_usage_v3_bytes{hostname="monitor", service="Disk usage /", disk="/_used"}
  perfnametolabel:
    # The command name
    self_check_by_snmp_disk_usage_v3:
      label_name: disk
logger:
  # Path and name for the log file. If not set, send to stdout
  logfile: /var/tmp/monitor-exporter.log
  # Log level
  level: INFO

```

> When running with gunicorn the port is defined by gunicorn
# Using Redis cache
If you have a large Monitor configuration, the load of the Monitor server can get high when collecting host and service data over the api with a high rate.
We strongly recommend that you instead collect host and service data in a batch and store it in a redis cache.
The interval of the batch collecting is configurable, but considering that most service checks in Monitor are often done in 5 minutes interval,
collecting every minute should be more than enough.

To use caching just add this to your `config.yml`:
```
cache:
  # Use redis for cache - future may support others
  # Values below is the default
  redis:
    # redis host
    host: localhost
    # redis port
    port: 6379
    # the auth string used in redis
    #auth: secretstuff
    # the redis db to use
    db: 0
  # The interval to collect data from Monitor in secoends
  interval: 60
  # The time to live for the stored Monitor objects in the redis cache
  ttl: 300
```
> Redis must installed on some host on the network and be accessible from the server running monitor-exporter

# Logging
The log stream is configure in the above config. If `logfile` is not set the logs will go to stdout.

Logs are formatted as json so it's easy to store logs in log servers like Loki and Elasticsearch.

# Prometheus configuration
Prometheus can be used with static configuration or with dynamic file discovery using the project
[monitor-promdiscovery](https://bitbucket.org/opsdis/monitor-promdiscovery)

Please add the the job to the scrape_configs in prometheus.yml.

> The target is the `host_name` configured in Monitor.

## Static config
```yaml

scrape_configs:
  - job_name: 'op5monitor'
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
        replacement: localhost:9631

```

## File discovery config for usage with `monitor-promdiscovery`

```yaml

scrape_configs:
  - job_name: 'op5monitor'
    scrape_interval: 1m
    metrics_path: /metrics
    file_sd_configs:
      - files:
          - 'sd/monitor_sd.yml'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9631

```
# Installing
1. Clone the git repo.
2. Install dependencies

   `pip install -r requirements.txt`

3. Build a distribution

   `python setup.py sdist`

4. Install locally

   `pip install dist/monitor-exporter-X.Y.Z.tar.gz`


# Running
## Development with Quart built in webserver

    python -m  monitor_exporter -f config.yml

The switch -p enable setting of the port.

## Production deployment
The are a number of ASGI containers that can be can use to deploy *monitor-exporter*. The dependency for these are not
included in the distribution.

### Deploying with gunicorn
First install the guincorn dependency into the python environment.

    pip install gunicorn==20.1.0
    pip install uvicorn==0.14.0

Running with the default config.yml. The default location is current directory.

    gunicorn --access-logfile /dev/null -w 4 -k uvicorn.workers.UvicornWorker "wsgi:create_app()"

Set the path to the configuration file.

    gunicorn --access-logfile /dev/null -w 4 -k uvicorn.workers.UvicornWorker "wsgi:create_app('/etc/monitor-exporter/config.yml')"

> Port for gunicorn is default 8000, but can be set with -b, e.g. `-b localhost:9631`

## Docker
Alt 1: Edit the config.yml in repo:

    docker run -p 9631:9631 monitor-exporter

Alt 2: Have config in separate location

    docker run -v /path/to/config:/monitor-exporter/config/ -p 9631:9631 monitor-exporter

## Test the connection

Check if the exporter is working.

    curl -s http://localhost:9631/health

Get metrics for a host where `target` is a host using the same `host_name` in Monitor

    curl -s http://localhost:9631/metrics?target=foo.com

# System requirements
Python 3.8

For required packages, please review `requirements.txt`

# License
The monitor-exporter is licensed under GPL version 3.
