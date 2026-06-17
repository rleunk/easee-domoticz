# -*- coding: utf-8 -*-
"""
<plugin key="EaseeCloudAutoDiscoveryV1000" name="Easee Domoticz plugin v10.6.3" author="Richard Leunk" version="10.6.3"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://github.com/rleunk/easee-domoticz">
    <description>
        <h2>Easee Domoticz plugin v10.6.3</h2><br/>
        <p>Stabiele Easee laadpaal integratie met compacte UI, emoji indicators, Tibber stroomtarief integratie en Equalizer (stap 1).</p>
    </description>
    <params>
        <param field="Username" label="Easee Username / telefoonnummer" width="260px" required="true"/>
        <param field="Password" label="Easee Password" width="260px" password="true" required="true"/>
        <group label="Weergave en polling">
            <param field="Mode1" label="Poll interval (sec)" width="80px" default="30"/>
            <param field="Mode5" label="Optionele site filter (tekst)" width="240px" default=""/>
            <param field="Mode6" label="Debug logging" width="100px">
                <options>
                    <option label="Normaal" value="Normal" default="true"/>
                    <option label="Debug" value="Debug"/>
                </options>
            </param>
        </group>
        <group label="Aangepaste laadpaalnamen (optioneel)">
            <param field="Mode2" label="Naam laadpaal 1" width="220px" default=""/>
            <param field="Mode3" label="Naam laadpaal 2" width="220px" default=""/>
            <param field="Mode4" label="Extra laadpaalnamen (komma-gescheiden, vanaf lader 3)" width="360px" default=""/>
        </group>
        <group label="Equalizer (optioneel, stap 1)">
            <param field="Address" label="Naam Equalizer" width="220px" default=""/>
            <param field="IP" label="Equalizer ID (handmatig, optioneel)" width="260px" default=""/>
        </group>
        <group label="Tibber (optioneel)">
            <param field="Mode7" label="Tibber Personal Access Token" width="360px" password="true" default=""/>
            <param field="Mode8" label="Tibber token ophalen" width="360px" default="https://developer.tibber.com/settings/access-token"/>
        </group>
    </params>
</plugin>
"""


import Domoticz
import os, json, time
try:
    import requests
except Exception:
    requests = None

import domoticz_runtime
domoticz_runtime.bind_plugin_globals(globals())

import easee_logging
import easee_helpers
import easee_api
import easee_state
import tibber_pricing
import domoticz_icons
import domoticz_devices
import charger_logic
import equalizer_logic
from easee_constants import ULTRA_DEBUG, PLUGIN_VERSION

class BasePlugin:
    def __init__(self):
        self.session = None
        self.access_token = ''
        self.refresh_token = ''
        self.started = False
        self.sync_done = False
        self.last_poll = 0
        self.units_by_name = {}
        self.units_by_devid = {}
        self.image_ids = {}
        self.state = {'chargers': {}, 'price_cache': {}, 'currency': 'EUR'}
        self.chargers = []
        self.equalizers = []
        self.latest_chargers = {}
        self.latest_equalizers = {}
        self.charger_names = {}
        self.equalizer_names = {}
        self.equalizer_source = 'none'
        self.equalizer_probes = {}
        self.site_fuse_cache = {}
        self.fuse_structure_logged = set()
        self.fuse_first_poll_logged = set()
        self.site_structure_numerics_logged = set()
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))

    # ---- logging ----
    def log(self, msg, module='plugin', context=''):
        easee_logging.info(module, msg, context)

    def debug(self, msg, module='plugin', context=''):
        easee_logging.debug(module, msg, context)

    def warning(self, msg, module='plugin', context=''):
        easee_logging.warning(module, msg, context)

    def error(self, msg, module='plugin', context=''):
        easee_logging.error(module, msg, context)

    def amp_value(self, *args, **kwargs): return equalizer_logic.amp_value(self, *args, **kwargs)
    def is_same_as_main_fuse(self, *args, **kwargs): return equalizer_logic.is_same_as_main_fuse(self, *args, **kwargs)
    def fuse_limit_keys(self, *args, **kwargs): return equalizer_logic.fuse_limit_keys(self, *args, **kwargs)
    def emobility_keys(self, *args, **kwargs): return equalizer_logic.emobility_keys(self, *args, **kwargs)
    def offline_circuit_current_keys(self, *args, **kwargs): return equalizer_logic.offline_circuit_current_keys(self, *args, **kwargs)
    def is_offline_circuit_current_key(self, *args, **kwargs): return equalizer_logic.is_offline_circuit_current_key(self, *args, **kwargs)
    def main_fuse_keys(self, *args, **kwargs): return equalizer_logic.main_fuse_keys(self, *args, **kwargs)
    def is_fuse_limit_key(self, *args, **kwargs): return equalizer_logic.is_fuse_limit_key(self, *args, **kwargs)
    def is_main_limit_key(self, *args, **kwargs): return equalizer_logic.is_main_limit_key(self, *args, **kwargs)
    def is_emobility_key(self, *args, **kwargs): return equalizer_logic.is_emobility_key(self, *args, **kwargs)
    def fuse_limit_from_dict(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_dict(self, *args, **kwargs)
    def emobility_from_dict(self, *args, **kwargs): return equalizer_logic.emobility_from_dict(self, *args, **kwargs)
    def root_circuit_ids(self, *args, **kwargs): return equalizer_logic.root_circuit_ids(self, *args, **kwargs)
    def _unique_circuits(self, *args, **kwargs): return equalizer_logic._unique_circuits(self, *args, **kwargs)
    def fuse_limit_from_circuits(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_circuits(self, *args, **kwargs)
    def fuse_limit_from_circuit_states(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_circuit_states(self, *args, **kwargs)
    def parse_site_structure_json(self, *args, **kwargs): return equalizer_logic.parse_site_structure_json(self, *args, **kwargs)
    def deep_scan_amp_keys(self, *args, **kwargs): return equalizer_logic.deep_scan_amp_keys(self, *args, **kwargs)
    def deep_scan_amp_range(self, *args, **kwargs): return equalizer_logic.deep_scan_amp_range(self, *args, **kwargs)
    def is_valid_fuse_limit(self, *args, **kwargs): return equalizer_logic.is_valid_fuse_limit(self, *args, **kwargs)
    def pick_best_fuse_candidate(self, *args, **kwargs): return equalizer_logic.pick_best_fuse_candidate(self, *args, **kwargs)
    def add_fuse_candidate(self, *args, **kwargs): return equalizer_logic.add_fuse_candidate(self, *args, **kwargs)
    def note_raw_fuse_value(self, *args, **kwargs): return equalizer_logic.note_raw_fuse_value(self, *args, **kwargs)
    def collect_fuse_from_circuits_list(self, *args, **kwargs): return equalizer_logic.collect_fuse_from_circuits_list(self, *args, **kwargs)
    def fetch_root_circuit_details(self, *args, **kwargs): return equalizer_logic.fetch_root_circuit_details(self, *args, **kwargs)
    def collect_fuse_from_dict(self, *args, **kwargs): return equalizer_logic.collect_fuse_from_dict(self, *args, **kwargs)
    def scan_any_fuse_keys(self, *args, **kwargs): return equalizer_logic.scan_any_fuse_keys(self, *args, **kwargs)
    def collect_fuse_from_circuit_settings(self, *args, **kwargs): return equalizer_logic.collect_fuse_from_circuit_settings(self, *args, **kwargs)
    def collect_fuse_from_equalizer_circuit(self, *args, **kwargs): return equalizer_logic.collect_fuse_from_equalizer_circuit(self, *args, **kwargs)
    def collect_explicit_circuit_fuses(self, *args, **kwargs): return equalizer_logic.collect_explicit_circuit_fuses(self, *args, **kwargs)
    def collect_fuse_from_cloud_loadbalancing(self, *args, **kwargs): return equalizer_logic.collect_fuse_from_cloud_loadbalancing(self, *args, **kwargs)
    def root_circuit_fuse(self, *args, **kwargs): return equalizer_logic.root_circuit_fuse(self, *args, **kwargs)
    def select_main_fuse_limit(self, *args, **kwargs): return equalizer_logic.select_main_fuse_limit(self, *args, **kwargs)
    def collect_json_key_tree(self, *args, **kwargs): return equalizer_logic.collect_json_key_tree(self, *args, **kwargs)
    def log_site_structure_once(self, *args, **kwargs): return equalizer_logic.log_site_structure_once(self, *args, **kwargs)
    def collect_numeric_values(self, *args, **kwargs): return equalizer_logic.collect_numeric_values(self, *args, **kwargs)
    def log_site_structure_numerics_once(self, *args, **kwargs): return equalizer_logic.log_site_structure_numerics_once(self, *args, **kwargs)
    def log_equalizer_fuse_once(self, *args, **kwargs): return equalizer_logic.log_equalizer_fuse_once(self, *args, **kwargs)
    def fuse_limit_from_deep_scan(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_deep_scan(self, *args, **kwargs)
    def collect_fuse_debug(self, *args, **kwargs): return equalizer_logic.collect_fuse_debug(self, *args, **kwargs)
    def structure_top_keys(self, *args, **kwargs): return equalizer_logic.structure_top_keys(self, *args, **kwargs)
    def fuse_limit_from_site_structure(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_site_structure(self, *args, **kwargs)
    def emobility_from_site_structure(self, *args, **kwargs): return equalizer_logic.emobility_from_site_structure(self, *args, **kwargs)
    def fuse_limit_from_equalizer_values(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_equalizer_values(self, *args, **kwargs)
    def fuse_limit_from_products(self, *args, **kwargs): return equalizer_logic.fuse_limit_from_products(self, *args, **kwargs)
    def set_emobility(self, *args, **kwargs): return equalizer_logic.set_emobility(self, *args, **kwargs)
    def log_fuse_probe_debug(self, *args, **kwargs): return equalizer_logic.log_fuse_probe_debug(self, *args, **kwargs)
    def fetch_site_fuse_info(self, *args, **kwargs): return equalizer_logic.fetch_site_fuse_info(self, *args, **kwargs)
    def parse_equalizer_observations(self, *args, **kwargs): return equalizer_logic.parse_equalizer_observations(self, *args, **kwargs)
    def custom_equalizer_name(self, *args, **kwargs): return equalizer_logic.custom_equalizer_name(self, *args, **kwargs)
    def manual_equalizer_id(self, *args, **kwargs): return equalizer_logic.manual_equalizer_id(self, *args, **kwargs)
    def equalizer_display_name(self, *args, **kwargs): return equalizer_logic.equalizer_display_name(self, *args, **kwargs)
    def equalizer_dev_name(self, *args, **kwargs): return equalizer_logic.equalizer_dev_name(self, *args, **kwargs)
    def _equalizer_matches_filter(self, *args, **kwargs): return equalizer_logic._equalizer_matches_filter(self, *args, **kwargs)
    def _append_equalizer(self, *args, **kwargs): return equalizer_logic._append_equalizer(self, *args, **kwargs)
    def _scan_equalizers_in_object(self, *args, **kwargs): return equalizer_logic._scan_equalizers_in_object(self, *args, **kwargs)
    def _ingest_equalizer_items(self, *args, **kwargs): return equalizer_logic._ingest_equalizer_items(self, *args, **kwargs)
    def discover_equalizers(self, *args, **kwargs): return equalizer_logic.discover_equalizers(self, *args, **kwargs)
    def poll_equalizer(self, *args, **kwargs): return equalizer_logic.poll_equalizer(self, *args, **kwargs)
    def session_energy_kwh(self, *args, **kwargs): return charger_logic.session_energy_kwh(self, *args, **kwargs)
    def power_integrated_kwh(self, *args, **kwargs): return charger_logic.power_integrated_kwh(self, *args, **kwargs)
    def custom_charger_name(self, *args, **kwargs): return charger_logic.custom_charger_name(self, *args, **kwargs)
    def charger_display_name(self, *args, **kwargs): return charger_logic.charger_display_name(self, *args, **kwargs)
    def charger_dev_name(self, *args, **kwargs): return charger_logic.charger_dev_name(self, *args, **kwargs)
    def op_mode_label(self, *args, **kwargs): return charger_logic.op_mode_label(self, *args, **kwargs)
    def power_emoji(self, *args, **kwargs): return charger_logic.power_emoji(self, *args, **kwargs)
    def status_emoji(self, *args, **kwargs): return charger_logic.status_emoji(self, *args, **kwargs)
    def compute_duration_text(self, *args, **kwargs): return charger_logic.compute_duration_text(self, *args, **kwargs)
    def discover_chargers(self, *args, **kwargs): return charger_logic.discover_chargers(self, *args, **kwargs)
    def poll_charger(self, *args, **kwargs): return charger_logic.poll_charger(self, *args, **kwargs)
    def login(self, *args, **kwargs): return easee_api.login(self, *args, **kwargs)
    def refresh(self, *args, **kwargs): return easee_api.refresh(self, *args, **kwargs)
    def api_get(self, *args, **kwargs): return easee_api.api_get(self, *args, **kwargs)
    def api_get_optional(self, *args, **kwargs): return easee_api.api_get_optional(self, *args, **kwargs)
    def tibber_query(self, *args, **kwargs): return tibber_pricing.tibber_query(self, *args, **kwargs)
    def refresh_tibber_prices(self, *args, **kwargs): return tibber_pricing.refresh_tibber_prices(self, *args, **kwargs)
    def current_tibber_price(self, *args, **kwargs): return tibber_pricing.current_tibber_price(self, *args, **kwargs)
    def price_status_emoji(self, *args, **kwargs): return tibber_pricing.price_status_emoji(self, *args, **kwargs)
    def cheapest_window_text(self, *args, **kwargs): return tibber_pricing.cheapest_window_text(self, *args, **kwargs)
    def price_emoji(self, *args, **kwargs): return tibber_pricing.price_emoji(self, *args, **kwargs)
    def make_charger_device_id(self, *args, **kwargs): return domoticz_devices.make_charger_device_id(self, *args, **kwargs)
    def make_equalizer_device_id(self, *args, **kwargs): return domoticz_devices.make_equalizer_device_id(self, *args, **kwargs)
    def make_device_id(self, *args, **kwargs): return domoticz_devices.make_device_id(self, *args, **kwargs)
    def rebuild_index(self, *args, **kwargs): return domoticz_devices.rebuild_index(self, *args, **kwargs)
    def find_unit(self, *args, **kwargs): return domoticz_devices.find_unit(self, *args, **kwargs)
    def find_unit_by_devid(self, *args, **kwargs): return domoticz_devices.find_unit_by_devid(self, *args, **kwargs)
    def resolve_unit(self, *args, **kwargs): return domoticz_devices.resolve_unit(self, *args, **kwargs)
    def resolve_charger_unit(self, *args, **kwargs): return domoticz_devices.resolve_charger_unit(self, *args, **kwargs)
    def resolve_equalizer_unit(self, *args, **kwargs): return domoticz_devices.resolve_equalizer_unit(self, *args, **kwargs)
    def resolve_core_unit(self, *args, **kwargs): return domoticz_devices.resolve_core_unit(self, *args, **kwargs)
    def sync_device_name(self, *args, **kwargs): return domoticz_devices.sync_device_name(self, *args, **kwargs)
    def next_free_unit(self, *args, **kwargs): return domoticz_devices.next_free_unit(self, *args, **kwargs)
    def ensure_device_once(self, *args, **kwargs): return domoticz_devices.ensure_device_once(self, *args, **kwargs)
    def update_core_text(self, *args, **kwargs): return domoticz_devices.update_core_text(self, *args, **kwargs)
    def update_core_custom(self, *args, **kwargs): return domoticz_devices.update_core_custom(self, *args, **kwargs)
    def update_core_energy(self, *args, **kwargs): return domoticz_devices.update_core_energy(self, *args, **kwargs)
    def update_core_sw(self, *args, **kwargs): return domoticz_devices.update_core_sw(self, *args, **kwargs)
    def update_text(self, *args, **kwargs): return domoticz_devices.update_text(self, *args, **kwargs)
    def update_custom(self, *args, **kwargs): return domoticz_devices.update_custom(self, *args, **kwargs)
    def update_energy(self, *args, **kwargs): return domoticz_devices.update_energy(self, *args, **kwargs)
    def update_sw(self, *args, **kwargs): return domoticz_devices.update_sw(self, *args, **kwargs)
    def update_charger_text(self, *args, **kwargs): return domoticz_devices.update_charger_text(self, *args, **kwargs)
    def update_charger_custom(self, *args, **kwargs): return domoticz_devices.update_charger_custom(self, *args, **kwargs)
    def update_charger_costs(self, *args, **kwargs): return domoticz_devices.update_charger_costs(self, *args, **kwargs)
    def update_charger_energy(self, *args, **kwargs): return domoticz_devices.update_charger_energy(self, *args, **kwargs)
    def update_equalizer_text(self, *args, **kwargs): return domoticz_devices.update_equalizer_text(self, *args, **kwargs)
    def update_equalizer_energy(self, *args, **kwargs): return domoticz_devices.update_equalizer_energy(self, *args, **kwargs)
    def ensure_core_devices(self, *args, **kwargs): return domoticz_devices.ensure_core_devices(self, *args, **kwargs)
    def ensure_charger_devices(self, *args, **kwargs): return domoticz_devices.ensure_charger_devices(self, *args, **kwargs)
    def ensure_equalizer_devices(self, *args, **kwargs): return domoticz_devices.ensure_equalizer_devices(self, *args, **kwargs)
    def image_root(self, *args, **kwargs): return domoticz_icons.image_root(self, *args, **kwargs)
    def icon_base(self, *args, **kwargs): return domoticz_icons.icon_base(self, *args, **kwargs)
    def _icon_images_key(self, *args, **kwargs): return domoticz_icons._icon_images_key(self, *args, **kwargs)
    def _collect_image_ids(self, *args, **kwargs): return domoticz_icons._collect_image_ids(self, *args, **kwargs)
    def _try_create_icon_zip(self, *args, **kwargs): return domoticz_icons._try_create_icon_zip(self, *args, **kwargs)
    def load_custom_images(self, *args, **kwargs): return domoticz_icons.load_custom_images(self, *args, **kwargs)
    def apply_images_to_devices(self, *args, **kwargs): return domoticz_icons.apply_images_to_devices(self, *args, **kwargs)
    def state_path(self, *args, **kwargs): return easee_state.state_path(self, *args, **kwargs)
    def load_state(self, *args, **kwargs): return easee_state.load_state(self, *args, **kwargs)
    def save_state(self, *args, **kwargs): return easee_state.save_state(self, *args, **kwargs)
    def today_key(self, *args, **kwargs): return easee_state.today_key(self, *args, **kwargs)
    def now_ts(self, *args, **kwargs): return easee_state.now_ts(self, *args, **kwargs)
    def charger_state(self, *args, **kwargs): return easee_state.charger_state(self, *args, **kwargs)
    def norm(self, *args, **kwargs): return easee_helpers.norm(self, *args, **kwargs)
    def prefix(self, *args, **kwargs): return easee_helpers.prefix(self, *args, **kwargs)
    def extra_charger_names(self, *args, **kwargs): return easee_helpers.extra_charger_names(self, *args, **kwargs)
    def pref(self, *args, **kwargs): return easee_helpers.pref(self, *args, **kwargs)
    def clean_label(self, *args, **kwargs): return easee_helpers.clean_label(self, *args, **kwargs)
    def safe_float(self, *args, **kwargs): return easee_helpers.safe_float(self, *args, **kwargs)
    def safe_int(self, *args, **kwargs): return easee_helpers.safe_int(self, *args, **kwargs)
    def truthy(self, *args, **kwargs): return easee_helpers.truthy(self, *args, **kwargs)
    def euro_str(self, *args, **kwargs): return easee_helpers.euro_str(self, *args, **kwargs)
    def power_watts(self, *args, **kwargs): return easee_helpers.power_watts(self, *args, **kwargs)
    def kwh_value(self, *args, **kwargs): return easee_helpers.kwh_value(self, *args, **kwargs)
    def wh_from_kwh(self, *args, **kwargs): return easee_helpers.wh_from_kwh(self, *args, **kwargs)
    def poll_interval_sec(self, *args, **kwargs): return easee_helpers.poll_interval_sec(self, *args, **kwargs)
    def short_id(self, *args, **kwargs): return easee_helpers.short_id(self, *args, **kwargs)
    def parse_iso(self, *args, **kwargs): return easee_helpers.parse_iso(self, *args, **kwargs)
    def tibber_token(self, *args, **kwargs): return easee_helpers.tibber_token(self, *args, **kwargs)
    def tibber_enabled(self, *args, **kwargs): return easee_helpers.tibber_enabled(self, *args, **kwargs)
    def kw_to_watts(self, *args, **kwargs): return easee_helpers.kw_to_watts(self, *args, **kwargs)
    def format_amp(self, *args, **kwargs): return easee_helpers.format_amp(self, *args, **kwargs)
    def current_from_power_3phase(self, *args, **kwargs): return easee_helpers.current_from_power_3phase(self, *args, **kwargs)
    def amps_balanced_3phase_from_power(self, *args, **kwargs): return easee_helpers.amps_balanced_3phase_from_power(self, *args, **kwargs)
    def phase_currents_from_values(self, *args, **kwargs): return easee_helpers.phase_currents_from_values(self, *args, **kwargs)
    def format_phase_amp(self, *args, **kwargs): return easee_helpers.format_phase_amp(self, *args, **kwargs)
    def actual_current_line(self, *args, **kwargs): return easee_helpers.actual_current_line(self, *args, **kwargs)
    def format_kw(self, *args, **kwargs): return easee_helpers.format_kw(self, *args, **kwargs)
    def first_dict_value(self, *args, **kwargs): return easee_helpers.first_dict_value(self, *args, **kwargs)

    # ---- orchestration ----
    def discover_entities(self):
        self.chargers = self.discover_chargers()
        self.equalizers = self.discover_equalizers()
        return self.chargers, self.equalizers

    # ---- lifecycle sync ----

    def initial_sync(self):
        self.discover_entities()
        self.charger_names = {}
        self.equalizer_names = {}
        self.ensure_core_devices()
        for i, c in enumerate(self.chargers):
            self.charger_names[c['id']] = self.charger_display_name(c, i)
            self.ensure_charger_devices(c, i)
        for i, eq in enumerate(self.equalizers):
            self.equalizer_names[eq['id']] = self.equalizer_display_name(eq, i)
            self.ensure_equalizer_devices(eq, i)
        if self.equalizers:
            self.log(f'Equalizer gevonden: {len(self.equalizers)} via {self.equalizer_source}')
            self.log('Hoofdzekering limiet komt uit circuit.fuse (API), niet uit max import vermogen')
        else:
            self.log('Geen Equalizer gevonden (stap 1 discovery)')
            if Parameters.get('Mode6') == 'Debug':
                self.log(f'Equalizer probes: {json.dumps(self.equalizer_probes, ensure_ascii=False)}')
            elif self.manual_equalizer_id():
                self.log('Tip: controleer handmatige Equalizer ID in hardware (IP-veld)')
            else:
                self.log('Tip: zet Debug aan of vul Equalizer ID handmatig in (IP-veld)')
        self.write_debug(True)

    def refresh_entity_cache_only(self):
        old_eq_ids = {e['id'] for e in self.equalizers}
        old_charger_ids = {c['id'] for c in self.chargers}
        self.discover_entities()
        self.charger_names = {c['id']: self.charger_display_name(c, i) for i, c in enumerate(self.chargers)}
        self.equalizer_names = {e['id']: self.equalizer_display_name(e, i) for i, e in enumerate(self.equalizers)}
        for i, c in enumerate(self.chargers):
            if c['id'] not in old_charger_ids:
                self.ensure_charger_devices(c, i)
        for i, eq in enumerate(self.equalizers):
            if eq['id'] not in old_eq_ids:
                self.ensure_equalizer_devices(eq, i)
        self.write_debug(False)

    def write_debug(self, created=False):
        if ULTRA_DEBUG:
            dbg = {
                'charger_ids': [c['id'] for c in self.chargers],
                'equalizer_ids': [e['id'] for e in self.equalizers],
                'equalizer_source': self.equalizer_source,
                'device_count': len(Devices),
                'created_cycle': created,
                'tibber_enabled': self.tibber_enabled(),
            }
            self.update_text(self.pref('Debug'), json.dumps(dbg, ensure_ascii=False)[:4000])
            self.update_text(self.pref('Counts'), f'chargers={len(self.chargers)}, equalizers={len(self.equalizers)}, devices={len(Devices)}')
            if self.tibber_enabled():
                self.update_text(self.pref('Tibber prijs'), json.dumps(self.current_tibber_price(), ensure_ascii=False)[:4000])

    # ---- polling ----

    def poll_all(self):
        self.latest_chargers = {}
        self.latest_equalizers = {}
        self.site_fuse_cache = {}
        refreshed = self.safe_int(self.state.get('price_cache_refreshed', 0), 0)
        if self.tibber_enabled() and ((self.now_ts() - refreshed) > 900 or not (self.state.get('price_cache') or {})):
            self.refresh_tibber_prices()
        for c in self.chargers:
            self.poll_charger(c)
        for eq in self.equalizers:
            self.poll_equalizer(eq)
        total_power = sum(v.get('power', 0) for v in self.latest_chargers.values())
        online = sum(1 for v in self.latest_chargers.values() if v.get('online'))
        self.debug(
            f'Poll klaar: {len(self.chargers)} lader(s), {len(self.equalizers)} EQ, '
            f'{online}/{len(self.chargers)} online, totaal {total_power} W',
            module='plugin',
            context='poll',
        )

    def update_combined(self):
        total_power = sum(v.get('power', 0) for v in self.latest_chargers.values())
        total_kwh = round(sum(v.get('kwh', 0.0) for v in self.latest_chargers.values()), 3)
        total_wh = sum(v.get('wh', 0) for v in self.latest_chargers.values())
        any_online = any(bool(v.get('online')) for v in self.latest_chargers.values())
        any_lb = any(bool(v.get('loadbal')) for v in self.latest_equalizers.values())
        eq_count = len(self.equalizers)

        self.update_core_energy('Totaal Laden', total_power, total_wh)
        self.update_core_custom('Totaal kWh', int(round(total_kwh)))

        if self.tibber_enabled():
            total_day_cost = round(sum(v.get('day_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_energy = round(sum(v.get('day_energy_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_tax = round(sum(v.get('day_tax_cost', 0.0) for v in self.latest_chargers.values()), 2)

            price_emoji = self.price_status_emoji()
            rate = self.safe_float(self.current_tibber_price().get('total'), 0.0)
            currency = self.current_tibber_price().get("currency","EUR")
            kosten_samenvatting = f'{price_emoji} {currency}\nKosten: €{self.euro_str(total_day_cost)} | Tarief: €{self.euro_str(rate)}/kWh\nEnergy: €{self.euro_str(total_day_energy)} | Belasting: €{self.euro_str(total_day_tax)}'
            self.update_core_text('Kosten & Samenvatting', kosten_samenvatting)

            self.update_core_text('Beste laden', self.cheapest_window_text(3))
            eq_part = f' | EQ: {eq_count}' if eq_count else ' | Geen EQ'
            lb_part = ' | LB actief' if any_lb else ''
            status_msg = ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part + ' | Tibber actief'
            self.update_core_text('Status', status_msg)
        else:
            eq_part = f' | EQ: {eq_count}' if eq_count else ' | Geen EQ'
            lb_part = ' | LB actief' if any_lb else ''
            self.update_core_text('Status', ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part)

        self.update_core_sw('LoadBal', any_lb)

    def onStart(self):
        domoticz_runtime.bind_plugin_globals(globals())
        if requests is None:
            self.error("Python module 'requests' ontbreekt. Installeer python3-requests in dezelfde Python omgeving als Domoticz.")
            return
        if Parameters.get('Mode6') == 'Debug':
            try:
                Domoticz.Debugging(1)
            except Exception:
                pass
        self.session = requests.Session()
        self.session.headers.update({'accept': 'application/json'})
        self.load_custom_images()
        self.apply_images_to_devices()
        self.rebuild_index()
        self.load_state()
        self.login()
        self.started = True
        self.log('Plugin gestart (initiële sync is vertraagd om dubbele devices na restart te voorkomen)')

    def onStop(self):
        self.save_state()
        try:
            if self.session:
                self.session.close()
        except Exception:
            pass
        self.log('Plugin gestopt')

    def onHeartbeat(self):
        if not self.started:
            return
        interval = max(10, self.safe_int(Parameters.get('Mode1', '30'), 30))
        if time.time() - self.last_poll < interval:
            return
        self.last_poll = time.time()
        try:
            if not self.access_token and not self.login():
                self.update_core_text('Status', 'Login mislukt')
                return
            if not self.sync_done:
                self.rebuild_index()
                self.initial_sync()
                self.sync_done = True
                self.save_state()
                return
            self.refresh_entity_cache_only()
            self.poll_all()
            self.update_combined()
            self.save_state()
        except Exception as e:
            self.error(f'onHeartbeat fout: {e}')
            self.update_core_text('Status', f'Fout: {e}')


_plugin = BasePlugin()

def onStart(): _plugin.onStart()
def onStop(): _plugin.onStop()
def onHeartbeat(): _plugin.onHeartbeat()