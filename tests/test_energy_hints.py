import json
import os
import sys
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.setdefault('Domoticz', types.ModuleType('Domoticz'))

import domoticz_runtime
from domoticz_energy_hints import (
    api_bases_from_args,
    clear_energy_context_cache,
    fetch_domoticz_devices,
    parse_watt_label,
    power_watts_from_api,
    read_energy_context,
    select_api_device,
    _http_get_json,
)


class _Plugin:
    def __init__(self, fetcher):
        self._domoticz_devices_fetcher = fetcher


class _Device:
    def __init__(self, name, svalue, device_id=''):
        self.Name = name
        self.sValue = svalue
        self.DeviceID = device_id


class EnergyHintParseTest(unittest.TestCase):
    def test_watt_labels(self):
        self.assertEqual(parse_watt_label('800 Watt'), 800)
        self.assertEqual(parse_watt_label('-1500 W', allow_bare=True), -1500)
        self.assertEqual(parse_watt_label('800', allow_bare=True), 800)
        self.assertIsNone(parse_watt_label('12.3 kWh'))
        self.assertIsNone(parse_watt_label('4.2 m3'))

    def test_negative_data_wins_over_usage(self):
        device = {'Usage': '1500 Watt', 'Data': '-1500 Watt'}
        self.assertEqual(power_watts_from_api(device), -1500)

    def test_api_bases_follow_domoticz_ports(self):
        self.assertEqual(
            api_bases_from_args(['domoticz', '-www', '8084', '-sslwww', '8443']),
            ['http://127.0.0.1:8084', 'https://127.0.0.1:8443'],
        )
        self.assertEqual(api_bases_from_args(['domoticz', '-www', '0']), ['http://127.0.0.1:8080'])

    def test_idx_and_exact_name(self):
        plugin = _Plugin(lambda: ([], None))
        devices = [
            {'idx': '12', 'Name': 'Power'},
            {'idx': '13', 'Name': 'Power usage'},
            {'idx': '14', 'Name': 'Easee - Vermogen', 'ID': 'EASEE_1'},
        ]
        chosen, status = select_api_device(plugin, devices, '12')
        self.assertEqual(status, 'ok')
        self.assertEqual(chosen['idx'], '12')
        chosen, status = select_api_device(plugin, devices, 'Power')
        self.assertEqual(chosen['idx'], '12')
        chosen, status = select_api_device(plugin, devices, 'usage')
        self.assertEqual(status, 'ok')
        self.assertEqual(chosen['idx'], '13')

    def test_ambiguous_partial_name(self):
        plugin = _Plugin(lambda: ([], None))
        devices = [{'idx': '1', 'Name': 'Zonnepanelen oost'}, {'idx': '2', 'Name': 'Zonnepanelen west'}]
        chosen, status = select_api_device(plugin, devices, 'Zonnepanelen')
        self.assertIsNone(chosen)
        self.assertEqual(status, 'ambiguous')


class EnergyHintContextTest(unittest.TestCase):
    def setUp(self):
        self._params = dict(domoticz_runtime.Parameters)
        self._devices = dict(domoticz_runtime.Devices)
        domoticz_runtime.Parameters.clear()
        domoticz_runtime.Parameters.update({'Mode20': 'Aan', 'Mode21': 'Power', 'Mode22': 'Zonnepanelen', 'Mode23': 'Sessy'})
        domoticz_runtime.Devices.clear()

    def tearDown(self):
        domoticz_runtime.Parameters.clear()
        domoticz_runtime.Parameters.update(self._params)
        domoticz_runtime.Devices.clear()
        domoticz_runtime.Devices.update(self._devices)

    def test_reads_other_hardware_by_idx_and_name(self):
        devices = [
            {'idx': '42', 'Name': 'Meterkast P1', 'Usage': '3500 Watt', 'UsageDeliv': '0 Watt'},
            {'idx': '43', 'Name': 'Zonnepanelen', 'Usage': '2200 Watt'},
            {'idx': '44', 'Name': 'Sessy', 'Data': '-800 Watt'},
            {'idx': '45', 'Name': 'Gas', 'Data': '3.1 m3'},
        ]
        domoticz_runtime.Parameters['Mode21'] = '42'
        plugin = _Plugin(lambda: (devices, None))
        ctx = read_energy_context(plugin)
        self.assertTrue(ctx['p1_ok'])
        self.assertEqual(ctx['import_w'], 3500)
        self.assertEqual(ctx['export_w'], 0)
        self.assertEqual(ctx['solar_w'], 2200)
        self.assertEqual(ctx['sessy_w'], -800)

    def test_gas_meter_is_not_a_power_source(self):
        devices = [{'idx': '7', 'Name': 'Power', 'Data': '12.0 m3'}]
        plugin = _Plugin(lambda: (devices, None))
        ctx = read_energy_context(plugin)
        self.assertFalse(ctx['p1_ok'])

    def test_api_down_uses_plugin_device(self):
        domoticz_runtime.Devices[3] = _Device('Power', '100;10;40;1')
        plugin = _Plugin(lambda: (None, 'connection refused'))
        ctx = read_energy_context(plugin)
        self.assertEqual(ctx['import_w'], 100)
        self.assertEqual(ctx['export_w'], 40)
        clear_energy_context_cache(plugin)
        ctx_again = read_energy_context(plugin)
        self.assertEqual(ctx_again['import_w'], 100)


class EnergyHintHttpTest(unittest.TestCase):
    def test_local_json_api(self):
        payload = {
            'status': 'OK',
            'result': [{'idx': '12', 'Name': 'Power', 'Usage': '800 Watt', 'UsageDeliv': '120 Watt'}],
        }
        body = json.dumps(payload).encode('utf-8')

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            devices, error = fetch_domoticz_devices([f'http://127.0.0.1:{port}'], _http_get_json)
            self.assertIsNone(error)
            self.assertEqual(devices[0]['Name'], 'Power')
            self.assertEqual(devices[0]['Usage'], '800 Watt')
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
