import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.setdefault('Domoticz', types.ModuleType('Domoticz'))

from tibber_pricing import select_tibber_home
from easee_api import _is_expected_optional_failure


def _home(home_id, info=None, subscription=True):
    home = {'id': home_id}
    if subscription:
        home['currentSubscription'] = {'priceInfo': info or {}}
    else:
        home['currentSubscription'] = None
    return home


def _slot(total=0.3):
    return {'total': total, 'energy': 0.2, 'tax': 0.1, 'startsAt': '2026-11-26T12:00:00+01:00'}


class TibberHomeSelectTest(unittest.TestCase):
    def test_skips_old_home_without_prices(self):
        old = _home('old-home', subscription=False)
        current = _home('current-home', {'current': _slot(), 'today': [_slot()]})
        chosen, priced = select_tibber_home([old, current])
        self.assertEqual(chosen['id'], 'current-home')
        self.assertEqual(priced, 1)

    def test_uses_first_home_when_it_has_prices(self):
        first = _home('first', {'today': [_slot(0.2)]})
        second = _home('second', {'today': [_slot(0.4)]})
        chosen, priced = select_tibber_home([first, second])
        self.assertEqual(chosen['id'], 'first')
        self.assertEqual(priced, 2)

    def test_empty_price_info_is_not_a_contract(self):
        empty = _home('empty', {})
        later = _home('later', {'tomorrow': [_slot()]})
        chosen, priced = select_tibber_home([empty, later])
        self.assertEqual(chosen['id'], 'later')
        self.assertEqual(priced, 1)

    def test_no_priced_home(self):
        chosen, priced = select_tibber_home([_home('a', subscription=False), {}])
        self.assertIsNone(chosen)
        self.assertEqual(priced, 0)

    def test_site_circuit_403_is_optional_debug(self):
        self.assertTrue(_is_expected_optional_failure('/sites/1036677/circuits', 403))
        self.assertTrue(_is_expected_optional_failure('/sites/1036677/circuits/983920', 403))
        self.assertTrue(_is_expected_optional_failure('/cloud-loadbalancing/equalizer/Q/config', 403))
        self.assertFalse(_is_expected_optional_failure('/chargers/abc/state', 403))


if __name__ == '__main__':
    unittest.main()
