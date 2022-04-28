import unittest
# from unittest.mock import MagicMock
from unittest import mock

import os
import json
import monitor_exporter.monitorconnection as Monitor
import monitor_exporter.fileconfiguration as fileconfig
import monitor_exporter.perfdata as perfdata

import asyncio


def get_perf_mock_file(*args, **kwargs):
    file = open(os.path.join('test_data', 'perfdata.json'), 'r')
    json_file = file.read()
    file.close()

    return json.loads(json_file)


def get_custom_vars_mock_file(*args, **kwargs):
    file = open(os.path.join('test_data', 'perflabels.json'), 'r')
    json_file = file.read()
    file.close()

    return json.loads(json_file)


class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.config = fileconfig.read_config(os.path.join('test_data', 'config.yml'))

    def test_get_perfdata_from_monitor(self):
        mcon = Monitor.MonitorConfig(self.config)

        # Create Mock
        mcon.get_host_data = AsyncMock(return_value=get_perf_mock_file())

        perf = perfdata.Perfdata(mcon, 'google.se')

        # Get the data from Monitor
        monitor_data = _run(perf.get_perfdata())
        self.assertEqual(len(monitor_data), 11)

        self.assertTrue(
            'monitor_host_state{hostname="google.se", environment="production"}' in monitor_data)
        self.assertTrue(
            'monitor_check_disk_local_mb_slash_bytes{hostname="google.se", service="disk_root", environment="production"}' in monitor_data)
        self.assertTrue(
            'monitor_check_ping_rta_seconds{hostname="google.se", service="pingit", environment="production"}' in monitor_data)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def AsyncMock(*args, **kwargs):
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro
