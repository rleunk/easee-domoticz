# -*- coding: utf-8 -*-
"""
<plugin key="EaseeCloudAutoDiscoveryV1000" name="Easee Domoticz plugin v10.9.31" author="Richard Leunk" version="10.9.31"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://github.com/rleunk/easee-domoticz">
    <description>
        <h2>Easee Domoticz plugin v10.9.31</h2><br/>
        <p>Stabiele Easee laadpaal integratie met compacte UI, emoji indicators, Tibber stroomtarief integratie en Equalizer (compacte meterkast-tegels).</p>
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
import os, json, time, traceback
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
        self.initial_sync_done = False
        self.startup_at = 0
        self.startup_min_delay = 3
        self.startup_force_after = 60
        self.devices_stable_count = 0
        self.last_devices_count = -1
        self.last_poll = 0
        self.last_discovery = 0
        self.charger_rate_limited_until = 0
        self.equalizer_rate_limited_until = 0
        self.general_rate_limited_until = 0
        self.ongoing_skip_until = 0
        self.equalizer_state_denied_until = {}
        self.units_by_name = {}
        self.units_by_devid = {}
        self.image_ids = {}
        self.icons_upload_required = False
        self.icon_reapply_remaining = 0
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

    def discover_entities(self):
        self.chargers = charger_logic.discover_chargers(self)
        self.equalizers = equalizer_logic.discover_equalizers(self)
        return self.chargers, self.equalizers

    def count_easee_devices(self):
        return sum(
            1 for devid in self.units_by_devid
            if str(devid).startswith('EASEE_')
        )

    def devices_ready(self):
        """Controleer of Domoticz Devices geladen zijn voor veilige initiële sync."""
        domoticz_devices.rebuild_index(self)
        devices_count = len(Devices)
        easee_count = self.count_easee_devices()

        if easee_count > 0:
            return True, f'{easee_count} bestaande Easee-device(s) in index'

        if devices_count > 0:
            if devices_count == self.last_devices_count:
                self.devices_stable_count += 1
            else:
                self.devices_stable_count = 1
            self.last_devices_count = devices_count
            if self.devices_stable_count >= 2:
                return True, f'Devices stabiel ({devices_count}, {self.devices_stable_count} heartbeats)'
            return True, f'Devices geladen ({devices_count})'

        self.devices_stable_count = 0
        self.last_devices_count = -1
        return False, 'Devices-lijst nog leeg'

    def handle_startup_sync(self):
        elapsed = time.time() - self.startup_at
        if self.initial_sync_done:
            if not self.sync_done:
                easee_logging.warning(
                    'plugin',
                    'Initiële sync was voltooid maar sync_done ontbrak — poll wordt hervat',
                    'startup',
                )
                self.sync_done = True
            return

        if elapsed < self.startup_min_delay:
            easee_logging.info(
                'plugin',
                f'Poll overgeslagen: startup-sync wacht op minimale vertraging ({elapsed:.1f}/{self.startup_min_delay}s)',
                'poll',
            )
            return

        ready, reason = self.devices_ready()
        force = elapsed >= self.startup_force_after

        if not ready and not force:
            easee_logging.info(
                'plugin',
                f'Poll overgeslagen: startup-sync wacht op Devices ({reason}, elapsed={elapsed:.1f}s)',
                'poll',
            )
            return

        if force and not ready:
            easee_logging.warning(
                'plugin',
                f'Startup-sync geforceerd na {elapsed:.0f}s (readiness niet bereikt: {reason})',
                'startup',
            )
            reason = f'fallback na {self.startup_force_after}s'

        easee_logging.info(
            'plugin',
            f'Initiële sync start ({reason}, elapsed={elapsed:.1f}s)',
            'startup',
        )
        try:
            domoticz_devices.rebuild_index(self)
            domoticz_icons.load_custom_images(self, plugin_globals=globals())
            self.initial_sync()
            self.initial_sync_done = True
            self.sync_done = True
            easee_logging.info(
                'plugin',
                f'Initiële sync voltooid ({len(self.chargers)} lader(s), {len(self.equalizers)} EQ) — poll start',
                'startup',
            )
        except Exception as e:
            easee_logging.error('plugin', f'Initiële sync mislukt: {e}', 'startup')
            return

        try:
            domoticz_icons.apply_images_to_devices(self, force=True)
            self.icon_reapply_remaining = 1
        except Exception as e:
            easee_logging.warning(
                'plugin',
                f'Iconen na initiële sync mislukt (poll gaat door): {e}',
                'startup',
            )
            self.icon_reapply_remaining = 0

        try:
            easee_state.save_state(self)
        except Exception as e:
            easee_logging.warning('plugin', f'State opslaan na initiële sync mislukt: {e}', 'startup')

    def initial_sync(self):
        self.discover_entities()
        self.last_discovery = time.time()
        self.charger_names = {}
        self.equalizer_names = {}
        domoticz_devices.ensure_core_devices(self)
        for i, c in enumerate(self.chargers):
            self.charger_names[c['id']] = charger_logic.charger_display_name(self, c, i)
            domoticz_devices.ensure_charger_devices(self, c, i)
        for i, eq in enumerate(self.equalizers):
            self.equalizer_names[eq['id']] = equalizer_logic.equalizer_display_name(self, eq, i)
            domoticz_devices.ensure_equalizer_devices(self, eq, i)
        if self.equalizers:
            easee_logging.info('plugin', f'Equalizer gevonden: {len(self.equalizers)} via {self.equalizer_source}')
            easee_logging.info('plugin', 'Hoofdzekering limiet komt uit circuit.fuse (API), niet uit max import vermogen')
        else:
            easee_logging.info('plugin', 'Geen Equalizer gevonden (stap 1 discovery)')
            if Parameters.get('Mode6') == 'Debug':
                easee_logging.info('plugin', f'Equalizer probes: {json.dumps(self.equalizer_probes, ensure_ascii=False)}')
            elif equalizer_logic.manual_equalizer_id(self):
                easee_logging.info('plugin', 'Tip: controleer handmatige Equalizer ID in hardware (IP-veld)')
            else:
                easee_logging.info('plugin', 'Tip: zet Debug aan of vul Equalizer ID handmatig in (IP-veld)')
        self.write_debug(True)

    def refresh_entity_cache_only(self):
        poll_interval = max(10, easee_helpers.safe_int(self, Parameters.get('Mode1', '30'), 30))
        discovery_interval = max(300, poll_interval * 10)
        since_discovery = time.time() - self.last_discovery
        if self.last_discovery > 0 and since_discovery < discovery_interval:
            easee_logging.debug(
                'plugin',
                f'Discovery overgeslagen ({since_discovery:.0f}/{discovery_interval}s)',
                'discovery',
            )
            return
        old_eq_ids = {e['id'] for e in self.equalizers}
        old_charger_ids = {c['id'] for c in self.chargers}
        self.discover_entities()
        self.last_discovery = time.time()
        self.charger_names = {c['id']: charger_logic.charger_display_name(self, c, i) for i, c in enumerate(self.chargers)}
        self.equalizer_names = {e['id']: equalizer_logic.equalizer_display_name(self, e, i) for i, e in enumerate(self.equalizers)}
        created = False
        for i, c in enumerate(self.chargers):
            if c['id'] not in old_charger_ids:
                domoticz_devices.ensure_charger_devices(self, c, i)
                created = True
        for i, eq in enumerate(self.equalizers):
            if eq['id'] not in old_eq_ids:
                domoticz_devices.ensure_equalizer_devices(self, eq, i)
                created = True
        if created:
            domoticz_icons.apply_images_to_devices(self)
        self.write_debug(False)

    def write_debug(self, created=False):
        if ULTRA_DEBUG:
            dbg = {
                'charger_ids': [c['id'] for c in self.chargers],
                'equalizer_ids': [e['id'] for e in self.equalizers],
                'equalizer_source': self.equalizer_source,
                'device_count': len(Devices),
                'created_cycle': created,
                'tibber_enabled': easee_helpers.tibber_enabled(self),
            }
            domoticz_devices.update_text(self, easee_helpers.pref(self, 'Debug'), json.dumps(dbg, ensure_ascii=False)[:4000])
            domoticz_devices.update_text(self, easee_helpers.pref(self, 'Counts'), f'chargers={len(self.chargers)}, equalizers={len(self.equalizers)}, devices={len(Devices)}')
            if easee_helpers.tibber_enabled(self):
                domoticz_devices.update_text(self, easee_helpers.pref(self, 'Tibber prijs'), json.dumps(tibber_pricing.current_tibber_price(self), ensure_ascii=False)[:4000])

    def poll_all(self):
        self.latest_chargers = {}
        self.latest_equalizers = {}
        self.site_fuse_cache = {}
        if not self.equalizers:
            easee_logging.info(
                'plugin',
                'Equalizer poll overgeslagen: geen equalizer(s) in cache (discovery vond er geen)',
                'poll',
            )
        refreshed = easee_helpers.safe_int(self, self.state.get('price_cache_refreshed', 0), 0)
        if easee_helpers.tibber_enabled(self) and ((easee_state.now_ts(self) - refreshed) > 900 or not (self.state.get('price_cache') or {})):
            tibber_pricing.refresh_tibber_prices(self)
        for eq in self.equalizers:
            equalizer_logic.poll_equalizer(self, eq)
        for c in self.chargers:
            charger_logic.poll_charger(self, c)
        total_power = sum(v.get('power', 0) for v in self.latest_chargers.values())
        online = sum(1 for v in self.latest_chargers.values() if v.get('online'))
        easee_logging.debug(
            'plugin',
            f'Poll voltooid: {len(self.chargers)} lader(s), {len(self.equalizers)} EQ, '
            f'{online}/{len(self.chargers)} online, totaal {total_power} W',
            'poll',
        )

    def update_combined(self):
        total_power = sum(v.get('power', 0) for v in self.latest_chargers.values())
        total_kwh = round(sum(v.get('kwh', 0.0) for v in self.latest_chargers.values()), 3)
        total_wh = sum(v.get('counter_wh', v.get('wh', 0)) for v in self.latest_chargers.values())
        any_online = any(bool(v.get('online')) for v in self.latest_chargers.values())
        any_lb = any(bool(v.get('loadbal')) for v in self.latest_equalizers.values())
        eq_count = len(self.equalizers)

        domoticz_devices.update_core_energy(self, 'Totaal Laden', total_power, total_wh)
        domoticz_devices.update_core_custom(self, 'Totaal kWh', int(round(total_kwh)))

        if easee_helpers.tibber_enabled(self):
            total_day_cost = round(sum(v.get('day_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_energy = round(sum(v.get('day_energy_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_tax = round(sum(v.get('day_tax_cost', 0.0) for v in self.latest_chargers.values()), 2)

            price_emoji = tibber_pricing.price_status_emoji(self)
            current_price = tibber_pricing.current_tibber_price(self)
            rate = easee_helpers.safe_float(self, current_price.get('total'), 0.0)
            currency = current_price.get('currency', 'EUR')
            kosten_samenvatting = f'{price_emoji} {currency}\nKosten: €{easee_helpers.euro_str(self, total_day_cost)} | Tarief: €{easee_helpers.euro_str(self, rate)}/kWh\nEnergy: €{easee_helpers.euro_str(self, total_day_energy)} | Belasting: €{easee_helpers.euro_str(self, total_day_tax)}'
            domoticz_devices.update_core_text(self, 'Kosten & Samenvatting', kosten_samenvatting)

            domoticz_devices.update_core_text(self, 'Beste laden', tibber_pricing.cheapest_window_text(self, 3))
            eq_part = f' | EQ: {eq_count}' if eq_count else ' | Geen EQ'
            lb_part = ' | LB actief' if any_lb else ''
            status_msg = ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part + ' | Tibber actief'
            if self.icons_upload_required:
                status_msg = '⚠️ Upload Easee_icons_v2.zip (Instellingen) | ' + status_msg
            domoticz_devices.update_core_text(self, 'Status', status_msg)
        else:
            eq_part = f' | EQ: {eq_count}' if eq_count else ' | Geen EQ'
            lb_part = ' | LB actief' if any_lb else ''
            status_msg = ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part
            if self.icons_upload_required:
                status_msg = '⚠️ Upload Easee_icons_v2.zip (Instellingen) | ' + status_msg
            domoticz_devices.update_core_text(self, 'Status', status_msg)

        domoticz_devices.update_core_sw(self, 'LoadBal', any_lb)

    def onStart(self):
        domoticz_runtime.bind_plugin_globals(globals())
        if requests is None:
            easee_logging.error('plugin', "Python module 'requests' ontbreekt. Installeer python3-requests in dezelfde Python omgeving als Domoticz.")
            return
        if Parameters.get('Mode6') == 'Debug':
            try:
                Domoticz.Debugging(1)
            except Exception:
                pass
        self.session = requests.Session()
        self.session.headers.update({'accept': 'application/json'})
        self._icon_diagnostic_done = False
        domoticz_icons.load_custom_images(self, plugin_globals=globals())
        domoticz_devices.rebuild_index(self)
        domoticz_devices.reset_cost_diagnostics(self)
        domoticz_icons.apply_images_to_devices(self)
        easee_state.load_state(self)
        easee_state.migrate_state_for_version(self)
        easee_state.migrate_cost_tracking(self)
        tibber_src = easee_state.sync_tibber_token_backup(self)
        try:
            easee_state.save_state(self)
        except Exception as e:
            easee_logging.warning('plugin', f'State opslaan na migratie mislukt: {e}', 'startup')
        self.sync_done = False
        self.initial_sync_done = False
        self.icon_reapply_remaining = 0
        self._icon_diagnostic_done = False
        self.startup_at = time.time()
        self.startup_min_delay = 3
        self.startup_force_after = 60
        self.devices_stable_count = 0
        self.last_devices_count = -1
        easee_api.login(self)
        self.started = True
        easee_logging.info('plugin', f'Plugin v{PLUGIN_VERSION} gestart', 'startup')
        if easee_helpers.tibber_enabled(self):
            if tibber_src == 'restored':
                easee_logging.info(
                    'plugin',
                    'Tibber actief — token hersteld uit state-backup (Mode7 leeg na opslag/herstart)',
                    'startup',
                )
            else:
                easee_logging.info('plugin', 'Tibber actief — kosten-tegels worden bijgewerkt na eerste poll', 'startup')
        else:
            easee_logging.info(
                'plugin',
                'Tibber uit (Mode7 leeg) — per-lader kosten-tegels worden niet bijgewerkt',
                'startup',
            )
        easee_logging.info('plugin', 'Initiële sync wacht op Domoticz Devices-readiness', 'startup')

    def onStop(self):
        easee_state.sync_tibber_token_backup(self)
        easee_state.save_state(self)
        try:
            if self.session:
                self.session.close()
        except Exception:
            pass
        easee_logging.info('plugin', 'Plugin gestopt')

    def onHeartbeat(self):
        if not self.started:
            return
        try:
            if not self.access_token and not easee_api.login(self):
                domoticz_devices.update_core_text(self, 'Status', 'Login mislukt')
                easee_logging.info('plugin', 'Poll overgeslagen: login mislukt', 'poll')
                return
            if not self.sync_done:
                self.handle_startup_sync()
                if not self.sync_done:
                    return
            if self.icon_reapply_remaining > 0:
                domoticz_icons.load_custom_images(self, plugin_globals=globals())
                domoticz_icons.apply_images_to_devices(self, force=True)
                self.icon_reapply_remaining -= 1
            interval = max(10, easee_helpers.safe_int(self, Parameters.get('Mode1', '30'), 30))
            since_poll = time.time() - self.last_poll
            if since_poll < interval:
                easee_logging.debug(
                    'plugin',
                    f'Poll overgeslagen: interval ({since_poll:.1f}/{interval}s)',
                    'poll',
                )
                return
            self.last_poll = time.time()
            self.refresh_entity_cache_only()
            self.poll_all()
            self.update_combined()
            easee_state.save_state(self)
        except Exception as e:
            easee_logging.error('plugin', f'onHeartbeat fout: {e}\n{traceback.format_exc()}')
            domoticz_devices.update_core_text(self, 'Status', f'Fout: {e}')


_plugin = BasePlugin()

def onStart(): _plugin.onStart()
def onStop(): _plugin.onStop()
def onHeartbeat(): _plugin.onHeartbeat()
