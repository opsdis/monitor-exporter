import unittest
from unittest import mock
import os
import monitor_exporter.monitorconnection as Monitor
import monitor_exporter.fileconfiguration as fileconfig


def mocked_monitorconnection_get(*args, **kwargs):
    yield ({"TEST": "test"})


class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.config = fileconfig.read_config(os.path.join('test_data', 'config.yml'))

    def test_default_config(self):
        mcon = Monitor.MonitorConfig()
        self.assertEqual(mcon.get_url(), '')

    def test_with_config(self):
        mcon = Monitor.MonitorConfig(self.config)
        self.assertEqual(mcon.get_url(), 'https://monitor.xyz')

    def test_singleton(self):
        mcon1 = Monitor.MonitorConfig(self.config)
        mcon2 = Monitor.MonitorConfig()
        self.assertEqual(mcon2.get_url(), 'https://monitor.xyz')
        # Make sure it same object - singleton
        self.assertEqual(id(mcon1), id(mcon2))
        mcon2 = Monitor.MonitorConfig(self.config)
        self.assertNotEqual(id(mcon1), id(mcon2))

    @mock.patch('monitor_exporter.monitorconnection.MonitorConfig.get', side_effect=mocked_monitorconnection_get())
    def test_get_perfdata_from_monitor(self, mock_get):
        mcon = Monitor.MonitorConfig(self.config)
        response = mcon.get('sunet.se')
        self.assertEqual(response, {"TEST": "test"})
