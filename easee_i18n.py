# -*- coding: utf-8 -*-
"""User-facing strings — Nederlands (default) and English (Mode30)."""

import domoticz_runtime
from easee_constants import OP_MODE_LABELS

LOCALE_PARAM = 'Mode30'
DEFAULT_LOCALE = 'nl'

# Canonical device/tile keys (internal — do not translate for DeviceID hashing).
DEVICE_LABELS = {
    'Status': ('Status', 'Status'),
    'Totaal Laden': ('Totaal Laden', 'Total charging'),
    'Totaal kWh': ('Totaal kWh', 'Total kWh'),
    'LoadBal': ('LoadBal', 'LoadBal'),
    'Dag overzicht': ('Dag overzicht', 'Daily overview'),
    'Beste laden': ('Beste laden', 'Best charging'),
    'Laden': ('Laden', 'Charging'),
    'Vermogen': ('Vermogen', 'Power'),
}

OP_MODE_KEYS = {
    0: 'op.offline',
    1: 'op.no_car',
    2: 'op.wait_start',
    3: 'op.charging',
    4: 'op.completed',
    5: 'op.error',
    6: 'op.ready',
    7: 'op.wait_auth',
    8: 'op.signing_off',
}

MESSAGES = {
    'nl': {
        'switch.on': 'Aan',
        'switch.off': 'Uit',
        'lb.on': 'Aan',
        'lb.off': 'Uit',
        'lb.tibber': 'Tibber',
        'online': 'Online',
        'offline': 'Offline',
        'eq_count': 'EQ: {n}',
        'no_eq': 'Geen EQ',
        'lb_active': 'LB actief',
        'tibber_controls': 'Tibber stuurt',
        'upload_icons': '⚠️ Upload Easee_icons_v2.zip (Instellingen)',
        'today_header': '📅 Vandaag',
        'charge_hours': '⏱️ Laaduren: {hours}',
        'tariff': 'Tarief: €{rate}/kWh',
        'energy_cost': 'Energy: €{energy}',
        'tax_cost': 'Belasting: €{tax}',
        'day_cost_line': '⚡ {kwh:.2f} kWh | €{cost}',
        'kwh_only_line': '⚡ {kwh:.2f} kWh',
        'session': 'Sessie',
        'last_session': 'Laatste sessie',
        'day_eur': 'Dag €{cost}',
        'laden_desc': 'Sessie: {session:.3f} kWh | Vandaag: {day:.3f} kWh | Totaal: {total:.1f} kWh',
        'unknown': 'Onbekend',
        'mode_n': 'Modus {n}',
        'charger_default': 'Laadpaal {n}',
        'charger_fallback': 'Lader',
        'equalizer_default': 'Equalizer',
        'equalizer_n': 'Equalizer {n}',
        'disabled': '(uit)',
        'hours_long': '{h}u {m:02d}m',
        'hours_short': '{m} min',
        'price.none': ' | Prijsbron: Geen',
        'price.tibber_active': ' | Tibber actief',
        'price.tibber': ' | Prijsbron: Tibber',
        'price.entsoe_spot': ' | ENTSO-E spot €{rate}/kWh',
        'price.entsoe': ' | Prijsbron: ENTSO-E',
        'price.energyzero': ' | EnergyZero €{rate}/kWh',
        'price.manual_fixed': ' | Handmatig €{rate}/kWh',
        'price.manual_typed': ' | Handmatig {tariff} ({period}) €{rate}/kWh',
        'cheapest': 'Goedkoopste: {time} (€{price:.2f}/kWh)',
        'cheapest_unknown': 'Goedkoopste: onbekend',
        'insufficient_prices': 'Onvoldoende prijsdata',
        'best_window': '{start} - {end} ({hours}u) | €{avg:.2f}/kWh',
        'manual.fixed_tariff': 'Vast tarief €{rate:.2f}/kWh',
        'hint.expensive': 'Laden bij duur tarief',
        'hint.cheap': 'Laden bij goedkoop tarief',
        'hint.grid_rewards': 'Waarschijnlijk Grid Rewards',
        'hint.solar_surplus': '☀️ Zonne-overschot',
        'hint.export': '↩️ Teruglevering',
        'hint.battery': '🔋 Thuisbatterij actief',
        'hint.high_import': '📥 Hoog netverbruik',
        'eq.online': 'Equalizer online',
        'eq.offline': 'Equalizer offline',
        'eq.lb_line': '{emoji} Load balancing: {state}',
        'eq.vrij_est': 'Vrij≈',
        'eq.vrij': 'Vrij',
        'eq.lb_phases': '   ⚖️ {vrij_label}: {vrij} | Laad: {laad} A',
        'eq.measured': '   📊 Gemeten L1/L2/L3: {amps} A',
        'eq.current_phases': '   📊 Stroom L1/L2/L3: {amps} A',
        'eq.lb_wait': '   LB-fase: wacht op API-data',
        'eq.phase_wait': '   Fase-data: nog niet beschikbaar',
        'eq.limits': '🛡️ eMobility: {emob} | Hoofd: {hoofd} | Limiet: {limiet}',
        'eq.max_import': '⚡ Max import: {kw}',
        'eq.na': 'n/b',
        'eq.import_export': '📥 Import: {import_w} W | Terug: {export_w} W',
        'eq.netto': '📊 Netto: {net_w} W',
        'eq.export_active': '↩️ Teruglevering actief',
        'eq.today_import_net': '📈 Vandaag import: {import_kwh:.3f} kWh | netto: {sign}{net_kwh:.3f} kWh',
        'eq.today_import': '📈 Vandaag import: {import_kwh:.3f} kWh',
        'eq.today_net': '📈 Vandaag netto: {sign}{net_kwh:.3f} kWh',
        'eq.total_net': '📈 Totaal netto: {net_kwh:.3f} kWh',
        'eq.voltage': '🔌 Spanning L1/L2/L3: {volts} V',
        'eq.voltage_wait': '🔌 Spanning L1/L2/L3: nog niet beschikbaar',
        'eq.phases_a': '📊 L1/L2/L3: {amps} A',
        'eq.current_single': '📊 Actuele stroom: {amps:.1f} A (3-fase)',
        'login_failed': 'Login mislukt',
        'error': 'Fout: {msg}',
        'op.offline': OP_MODE_LABELS[0],
        'op.no_car': OP_MODE_LABELS[1],
        'op.wait_start': OP_MODE_LABELS[2],
        'op.charging': OP_MODE_LABELS[3],
        'op.completed': OP_MODE_LABELS[4],
        'op.error': OP_MODE_LABELS[5],
        'op.ready': OP_MODE_LABELS[6],
        'op.wait_auth': OP_MODE_LABELS[7],
        'op.signing_off': OP_MODE_LABELS[8],
    },
    'en': {
        'switch.on': 'On',
        'switch.off': 'Off',
        'lb.on': 'On',
        'lb.off': 'Off',
        'lb.tibber': 'Tibber',
        'online': 'Online',
        'offline': 'Offline',
        'eq_count': 'EQ: {n}',
        'no_eq': 'No EQ',
        'lb_active': 'LB active',
        'tibber_controls': 'Tibber controls',
        'upload_icons': '⚠️ Upload Easee_icons_v2.zip (Settings)',
        'today_header': '📅 Today',
        'charge_hours': '⏱️ Charging hours: {hours}',
        'tariff': 'Tariff: €{rate}/kWh',
        'energy_cost': 'Energy: €{energy}',
        'tax_cost': 'Tax: €{tax}',
        'day_cost_line': '⚡ {kwh:.2f} kWh | €{cost}',
        'kwh_only_line': '⚡ {kwh:.2f} kWh',
        'session': 'Session',
        'last_session': 'Last session',
        'day_eur': 'Day €{cost}',
        'laden_desc': 'Session: {session:.3f} kWh | Today: {day:.3f} kWh | Total: {total:.1f} kWh',
        'unknown': 'Unknown',
        'mode_n': 'Mode {n}',
        'charger_default': 'Charger {n}',
        'charger_fallback': 'Charger',
        'equalizer_default': 'Equalizer',
        'equalizer_n': 'Equalizer {n}',
        'disabled': '(off)',
        'hours_long': '{h}h {m:02d}m',
        'hours_short': '{m} min',
        'price.none': ' | Price source: None',
        'price.tibber_active': ' | Tibber active',
        'price.tibber': ' | Price source: Tibber',
        'price.entsoe_spot': ' | ENTSO-E spot €{rate}/kWh',
        'price.entsoe': ' | Price source: ENTSO-E',
        'price.energyzero': ' | EnergyZero €{rate}/kWh',
        'price.manual_fixed': ' | Manual €{rate}/kWh',
        'price.manual_typed': ' | Manual {tariff} ({period}) €{rate}/kWh',
        'cheapest': 'Cheapest: {time} (€{price:.2f}/kWh)',
        'cheapest_unknown': 'Cheapest: unknown',
        'insufficient_prices': 'Insufficient price data',
        'best_window': '{start} - {end} ({hours}h) | €{avg:.2f}/kWh',
        'manual.fixed_tariff': 'Fixed rate €{rate:.2f}/kWh',
        'hint.expensive': 'Charging at expensive rate',
        'hint.cheap': 'Charging at cheap rate',
        'hint.grid_rewards': 'Probably Grid Rewards',
        'hint.solar_surplus': '☀️ Solar surplus',
        'hint.export': '↩️ Exporting to grid',
        'hint.battery': '🔋 Home battery active',
        'hint.high_import': '📥 High grid import',
        'eq.online': 'Equalizer online',
        'eq.offline': 'Equalizer offline',
        'eq.lb_line': '{emoji} Load balancing: {state}',
        'eq.vrij_est': 'Avail≈',
        'eq.vrij': 'Avail',
        'eq.lb_phases': '   ⚖️ {vrij_label}: {vrij} | Charge: {laad} A',
        'eq.measured': '   📊 Measured L1/L2/L3: {amps} A',
        'eq.current_phases': '   📊 Current L1/L2/L3: {amps} A',
        'eq.lb_wait': '   LB phases: waiting for API data',
        'eq.phase_wait': '   Phase data: not available yet',
        'eq.limits': '🛡️ eMobility: {emob} | Main fuse: {hoofd} | Limit: {limiet}',
        'eq.max_import': '⚡ Max import: {kw}',
        'eq.na': 'n/a',
        'eq.import_export': '📥 Import: {import_w} W | Export: {export_w} W',
        'eq.netto': '📊 Net: {net_w} W',
        'eq.export_active': '↩️ Grid export active',
        'eq.today_import_net': '📈 Today import: {import_kwh:.3f} kWh | net: {sign}{net_kwh:.3f} kWh',
        'eq.today_import': '📈 Today import: {import_kwh:.3f} kWh',
        'eq.today_net': '📈 Today net: {sign}{net_kwh:.3f} kWh',
        'eq.total_net': '📈 Total net: {net_kwh:.3f} kWh',
        'eq.voltage': '🔌 Voltage L1/L2/L3: {volts} V',
        'eq.voltage_wait': '🔌 Voltage L1/L2/L3: not available yet',
        'eq.phases_a': '📊 L1/L2/L3: {amps} A',
        'eq.current_single': '📊 Current draw: {amps:.1f} A (3-phase)',
        'login_failed': 'Login failed',
        'error': 'Error: {msg}',
        'op.offline': 'Offline',
        'op.no_car': 'No car',
        'op.wait_start': 'Waiting to start',
        'op.charging': 'Charging',
        'op.completed': 'Completed',
        'op.error': 'Error',
        'op.ready': 'Ready to charge',
        'op.wait_auth': 'Waiting for authorisation',
        'op.signing_off': 'Signing off',
    },
}


def locale(plugin=None):
    raw = (domoticz_runtime.Parameters.get(LOCALE_PARAM, '') or DEFAULT_LOCALE).strip().lower()
    if raw in ('en', 'english', 'engels'):
        return 'en'
    return 'nl'


def t(plugin, key, **kwargs):
    loc = locale(plugin)
    template = MESSAGES.get(loc, MESSAGES['nl']).get(key)
    if template is None:
        template = MESSAGES['nl'].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    return template


def tile_name(plugin, canonical_key):
    pair = DEVICE_LABELS.get(canonical_key)
    if not pair:
        return canonical_key
    loc = locale(plugin)
    return pair[1] if loc == 'en' else pair[0]


def pref_tile(plugin, canonical_key):
    import easee_helpers
    return easee_helpers.pref(plugin, tile_name(plugin, canonical_key))


def op_mode_label(plugin, value):
    if value is None or value == '':
        return t(plugin, 'unknown')
    try:
        mode = int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return text if text else t(plugin, 'unknown')
    key = OP_MODE_KEYS.get(mode)
    if key:
        return t(plugin, key)
    return t(plugin, 'mode_n', n=mode)


def charge_hours_text(plugin, charge_hours):
    if charge_hours >= 1:
        return t(
            plugin, 'hours_long',
            h=int(charge_hours),
            m=int((charge_hours % 1) * 60),
        )
    return t(plugin, 'hours_short', m=int(charge_hours * 60))


def switch_value(plugin, state):
    return t(plugin, 'switch.on' if state else 'switch.off')
