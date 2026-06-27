# -*- coding: utf-8 -*-
"""
<plugin key="EaseeCloudAutoDiscoveryV1000" name="Easee Domoticz plugin v1 (0.6.0)" author="Richard Leunk" version="0.6.0"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://github.com/rleunk/easee-domoticz">
    <description>
        <h2>Easee Domoticz plugin v1 (0.6.0)</h2><br/>
        <p>Easee laadpaal integratie met compacte UI (11 tegels), Prijsbron Geen/Handmatig/Tibber/ENTSO-E/EnergyZero, handmatig vast/dag-nacht/dal-piek-tarief, P1/zon/thuisbatterij-hints en Equalizer. v1 ontwikkelingslijn.</p>
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
        <group label="Energieprijs (optioneel)">
            <param field="Mode9" label="Prijsbron" width="160px">
                <options>
                    <option label="Geen" value="Geen"/>
                    <option label="Handmatig" value="Handmatig"/>
                    <option label="Tibber" value="Tibber" default="true"/>
                    <option label="ENTSO-E" value="ENTSO-E"/>
                    <option label="EnergyZero" value="EnergyZero"/>
                </options>
            </param>
            <param field="BesteLadenHours" type="number" label="Beste laden venster uren (Tibber/Handmatig/ENTSO-E/EnergyZero)" min="1" max="12" default="3" width="80px"/>
            <param field="Mode11" label="Handmatig type (alleen bij Handmatig)" width="160px">
                <options>
                    <option label="Vast" value="Vast" default="true"/>
                    <option label="Dag/nacht" value="Dag/nacht"/>
                    <option label="Dal/piek" value="Dal/piek"/>
                </options>
            </param>
            <param field="Mode10" label="Vast tarief €/kWh (Handmatig — Vast)" width="100px" default="0.25"/>
            <param field="Mode12" label="Dal tarief €/kWh (Handmatig — Dag/nacht / Dal/piek)" width="100px" default="0.22"/>
            <param field="Mode13" label="Normal tarief €/kWh (Handmatig — Dag/nacht / Dal/piek)" width="100px" default="0.28"/>
            <param field="Mode14" label="Dal start uur 0–23 (Handmatig — Dag/nacht / Dal/piek)" width="80px" default="23"/>
            <param field="Mode15" label="Dal eind uur 0–23 (Handmatig — Dag/nacht / Dal/piek)" width="80px" default="7"/>
            <param field="Mode16" label="Piek tarief €/kWh (Handmatig — Dal/piek)" width="100px" default="0.35"/>
            <param field="Mode17" label="Piek start uur 0–23 (Handmatig — Dal/piek)" width="80px" default="17"/>
            <param field="Mode18" label="Piek eind uur 0–23 (Handmatig — Dal/piek)" width="80px" default="21"/>
            <param field="Mode19" label="Weekend alles dal (Handmatig — Dal/piek)" width="120px">
                <options>
                    <option label="Ja" value="Ja" default="true"/>
                    <option label="Nee" value="Nee"/>
                </options>
            </param>
            <param field="Mode7" label="Tibber token (alleen bij Tibber)" width="360px" password="true" default=""/>
            <param field="Mode8" label="Tibber token ophalen (alleen bij Tibber)" width="360px" default="https://developer.tibber.com/settings/access-token"/>
            <param field="Mode24" label="ENTSO-E API token (alleen bij ENTSO-E)" width="360px" password="true" default=""/>
            <param field="Mode28" label="ENTSO-E token aanvragen (alleen bij ENTSO-E)" width="360px" default="https://transparency.entsoe.eu/"/>
            <param field="Mode25" label="Opslag leverancier €/kWh (alleen bij ENTSO-E)" width="120px" default="0"/>
            <param field="Mode26" label="Energiebelasting €/kWh (alleen bij ENTSO-E, ca. 0,12)" width="120px" default="0"/>
            <param field="Mode27" label="BTW % (alleen bij ENTSO-E)" width="80px" default="21"/>
            <param field="Mode29" label="EnergyZero — geen token nodig (alleen bij EnergyZero)" width="360px" default="https://www.dynamische-energieprijzen.nl/"/>
        </group>
        <group label="Energie hints (optioneel)">
            <param field="Mode20" label="P1 / zon / thuisbatterij hints" width="100px">
                <options>
                    <option label="Aan" value="Aan" default="true"/>
                    <option label="Uit" value="Uit"/>
                </options>
            </param>
            <param field="Mode21" label="P1 meter apparaatnaam of idx" width="220px" default="Power"/>
            <param field="Mode22" label="Zonnepanelen apparaatnaam of idx" width="220px" default="Zonnepanelen"/>
            <param field="Mode23" label="Thuisbatterij apparaatnaam of idx (leeg = uit)" width="220px" default="Sessy"/>
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
import pricing
from pricing import ui as pricing_ui
import domoticz_icons
import domoticz_devices
import charger_logic
import equalizer_logic
import domoticz_energy_hints
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

    def _log_heartbeat_exception(self, step, exc):
        msg = f'heartbeat exception: {step}: {exc}\n{traceback.format_exc()}'
        try:
            easee_logging.error('plugin', msg, 'heartbeat')
        except Exception:
            pass

    def _heartbeat_step(self, step, func):
        try:
            return func()
        except Exception as e:
            self._log_heartbeat_exception(step, e)
            return None

    def discover_entities(self):
        self._discovery_network_error = False
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
        if not getattr(self, '_discovery_network_error', False):
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
        prev_chargers = list(self.chargers)
        prev_equalizers = list(self.equalizers)
        self.discover_entities()
        if getattr(self, '_discovery_network_error', False):
            self.chargers = prev_chargers
            self.equalizers = prev_equalizers
            easee_logging.warning(
                'plugin',
                'Discovery overgeslagen door netwerkfout — cache behouden, retry volgende poll',
                'discovery',
            )
            return
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
                'pricing_enabled': easee_helpers.pricing_enabled(self),
                'pricing_source': easee_helpers.pricing_source(self),
            }
            domoticz_devices.update_text(self, easee_helpers.pref(self, 'Debug'), json.dumps(dbg, ensure_ascii=False)[:4000])
            domoticz_devices.update_text(self, easee_helpers.pref(self, 'Counts'), f'chargers={len(self.chargers)}, equalizers={len(self.equalizers)}, devices={len(Devices)}')
            if easee_helpers.pricing_enabled(self):
                domoticz_devices.update_text(
                    self, easee_helpers.pref(self, 'Tibber prijs'),
                    json.dumps(pricing_ui.current_price(self), ensure_ascii=False)[:4000],
                )

    def poll_all(self):
        domoticz_energy_hints.clear_energy_context_cache(self)
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
        price_provider = pricing.get_provider(self)
        if price_provider.is_available() and ((easee_state.now_ts(self) - refreshed) > 900 or not (self.state.get('price_cache') or {})):
            self._heartbeat_step('pricing refresh', lambda: price_provider.refresh())
        for eq in self.equalizers:
            eid = eq.get('id', '?')
            self._heartbeat_step(f'poll equalizer {eid}', lambda eq=eq: equalizer_logic.poll_equalizer(self, eq))
        for c in self.chargers:
            cid = c.get('id', '?')
            self._heartbeat_step(f'poll charger {cid}', lambda c=c: charger_logic.poll_charger(self, c))
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
        source = easee_helpers.pricing_source(self)
        costs_on = easee_helpers.pricing_enabled(self)

        domoticz_devices.update_core_energy(self, 'Totaal Laden', total_power, total_wh)
        domoticz_devices.update_core_custom(self, 'Totaal kWh', int(round(total_kwh)))

        g = easee_state.global_day_state(self)
        day_kwh = round(sum(v.get('day_kwh', 0.0) for v in self.latest_chargers.values()), 3)
        any_charging = any(v.get('power', 0) > 50 for v in self.latest_chargers.values())
        easee_state.track_global_charge(self, 0, 0, any_charging)
        charge_hours = easee_helpers.safe_float(self, g.get('charge_hours'), 0.0)
        hours_txt = (
            f'{int(charge_hours)}u {int((charge_hours % 1) * 60):02d}m'
            if charge_hours >= 1 else f'{int(charge_hours * 60)} min'
        )

        dag_overzicht = None
        if source == 'Geen':
            dag_overzicht = (
                f'📅 Vandaag\n'
                f'⚡ {day_kwh:.2f} kWh\n'
                f'⏱️ Laaduren: {hours_txt}'
            )
        elif costs_on:
            total_day_cost = round(sum(v.get('day_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_energy = round(sum(v.get('day_energy_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_tax = round(sum(v.get('day_tax_cost', 0.0) for v in self.latest_chargers.values()), 2)
            current_price = pricing_ui.current_price(self)
            rate = easee_helpers.safe_float(self, current_price.get('total'), 0.0)

            if easee_helpers.beste_laden_enabled(self):
                domoticz_devices.update_core_text(self, 'Beste laden', pricing_ui.cheapest_window_text(self))

            if source in ('Tibber', 'ENTSO-E'):
                price_emoji = pricing_ui.price_status_emoji(self)
                dag_overzicht = (
                    f'📅 Vandaag\n'
                    f'⚡ {day_kwh:.2f} kWh | €{easee_helpers.euro_str(self, total_day_cost)}\n'
                    f'⏱️ Laaduren: {hours_txt}\n'
                    f'💰 {pricing_ui.dagrapport_cheapest_line(self)}\n'
                    f'{price_emoji} Tarief: €{easee_helpers.euro_str(self, rate)}/kWh\n'
                    f'Energy: €{easee_helpers.euro_str(self, total_day_energy)} | '
                    f'Belasting: €{easee_helpers.euro_str(self, total_day_tax)}'
                )
            else:
                price_emoji = pricing_ui.price_status_emoji(self)
                dag_overzicht = (
                    f'📅 Vandaag\n'
                    f'⚡ {day_kwh:.2f} kWh | €{easee_helpers.euro_str(self, total_day_cost)}\n'
                    f'⏱️ Laaduren: {hours_txt}\n'
                    f'💰 {pricing_ui.dagrapport_cheapest_line(self)}\n'
                    f'{price_emoji} Tarief: €{easee_helpers.euro_str(self, rate)}/kWh'
                )

        energy_hint = domoticz_energy_hints.global_hints_text(self, any_charging=any_charging)
        if dag_overzicht is not None and energy_hint:
            dag_overzicht = f'{dag_overzicht}\n{energy_hint}'
        if dag_overzicht is not None and easee_helpers.dag_overzicht_enabled(self):
            domoticz_devices.update_core_text(self, 'Dag overzicht', dag_overzicht)

        eq_part = f' | EQ: {eq_count}' if eq_count else ' | Geen EQ'
        if source == 'Tibber' and costs_on:
            tibber_stuurt = bool(not any_lb and any_charging)
            lb_part = ' | LB actief' if any_lb else (' | Tibber stuurt' if tibber_stuurt else '')
            status_msg = ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part + ' | Tibber actief'
        elif source == 'ENTSO-E' and costs_on:
            lb_part = ' | LB actief' if any_lb else ''
            rate = easee_helpers.safe_float(self, pricing_ui.current_price(self).get('total'), 0.0)
            status_msg = (
                ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part
                + f' | ENTSO-E spot €{easee_helpers.euro_str(self, rate)}/kWh'
            )
        elif source == 'Handmatig' and costs_on:
            lb_part = ' | LB actief' if any_lb else ''
            tariff_type = easee_helpers.manual_tariff_type(self)
            if tariff_type == 'Vast':
                rate = easee_helpers.manual_rate(self)
                status_msg = (
                    ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part
                    + f' | Handmatig €{easee_helpers.euro_str(self, rate)}/kWh'
                )
            else:
                rate = easee_helpers.manual_rate_at(self)
                period = easee_helpers.manual_tariff_period(self)
                status_msg = (
                    ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part
                    + f' | Handmatig {tariff_type.lower()} ({period}) €{easee_helpers.euro_str(self, rate)}/kWh'
                )
        else:
            lb_part = ' | LB actief' if any_lb else ''
            status_msg = ('✅ Online' if any_online else '❌ Offline') + eq_part + lb_part

        if self.icons_upload_required:
            status_msg = '⚠️ Upload Easee_icons_v2.zip (Instellingen) | ' + status_msg
        if energy_hint:
            status_msg = f'{status_msg} | {energy_hint}'
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
        easee_state.migrate_session_baseline(self)
        easee_state.migrate_charging_timer_state(self)
        easee_state.migrate_manual_tariff_fields(self)
        tibber_src = easee_state.sync_tibber_token_backup(self)
        entsoe_src = easee_state.sync_entsoe_token_backup(self)
        beste_src = easee_state.sync_besteladen_hours_backup(self)
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
        if beste_src == 'restored':
            easee_logging.info(
                'plugin',
                f'Beste laden venster hersteld uit state-backup ({easee_helpers.beste_laden_hours(self)} uur)',
                'startup',
            )
        self.pricing_provider = pricing.get_provider(self)
        prijsbron = easee_helpers.pricing_source(self)
        if prijsbron == 'Geen':
            easee_logging.info('plugin', 'Prijsbron Geen — kosten uitgeschakeld', 'startup')
        elif prijsbron == 'Handmatig':
            tariff_type = easee_helpers.manual_tariff_type(self)
            if tariff_type == 'Dag/nacht':
                easee_logging.info(
                    'plugin',
                    f'Prijsbron Handmatig — dag/nacht dal €{easee_helpers.manual_dal_rate(self):.2f}/kWh, '
                    f'normal €{easee_helpers.manual_normal_rate(self):.2f}/kWh '
                    f'({easee_helpers.manual_dal_start_hour(self):02d}:00–'
                    f'{easee_helpers.manual_dal_end_hour(self):02d}:00)',
                    'startup',
                )
            elif tariff_type == 'Dal/piek':
                easee_logging.info(
                    'plugin',
                    f'Prijsbron Handmatig — dal/piek dal €{easee_helpers.manual_dal_rate(self):.2f}, '
                    f'normal €{easee_helpers.manual_normal_rate(self):.2f}, '
                    f'piek €{easee_helpers.manual_piek_rate(self):.2f}/kWh '
                    f'(piek {easee_helpers.manual_piek_start_hour(self):02d}:00–'
                    f'{easee_helpers.manual_piek_end_hour(self):02d}:00, '
                    f'weekend alles dal={"ja" if easee_helpers.manual_weekend_all_dal(self) else "nee"})',
                    'startup',
                )
            else:
                rate = easee_helpers.manual_rate(self)
                easee_logging.info(
                    'plugin',
                    f'Prijsbron Handmatig — vast tarief €{rate:.2f}/kWh',
                    'startup',
                )
        if domoticz_energy_hints.energy_hints_enabled(self):
            names = domoticz_energy_hints.configured_device_names(self)
            easee_logging.info(
                'plugin',
                f'Energie hints aan — P1="{names["p1"]}", zon="{names["solar"]}", thuisbatterij="{names["thuisbatterij"]}"',
                'startup',
            )
        if prijsbron == 'Tibber':
            if easee_helpers.tibber_enabled(self):
                if tibber_src == 'restored':
                    easee_logging.info(
                        'plugin',
                        'Tibber actief — token hersteld uit state-backup (Mode7 leeg na opslag/herstart)',
                        'startup',
                    )
                else:
                    easee_logging.info(
                        'plugin',
                        'Tibber actief — kosten in Status/Dag overzicht na eerste poll',
                        'startup',
                    )
            else:
                easee_logging.info(
                    'plugin',
                    'Tibber uit (Mode7 leeg) — Dag overzicht en laadpaal-kosten in Status worden niet bijgewerkt',
                    'startup',
                )
        elif prijsbron == 'ENTSO-E':
            if easee_helpers.entsoe_enabled(self):
                if entsoe_src == 'restored':
                    easee_logging.info(
                        'plugin',
                        'ENTSO-E actief — token hersteld uit state-backup (Mode24 leeg na opslag/herstart)',
                        'startup',
                    )
                else:
                    easee_logging.info(
                        'plugin',
                        'ENTSO-E actief — kosten na eerste poll',
                        'startup',
                    )
                easee_logging.info(
                    'plugin',
                    f'ENTSO-E opslag €{easee_helpers.entsoe_opslag(self):.4f}/kWh, '
                    f'energiebelasting €{easee_helpers.entsoe_energiebelasting(self):.4f}/kWh, '
                    f'BTW {easee_helpers.entsoe_btw_pct(self):.0f}%',
                    'startup',
                )
            else:
                easee_logging.info(
                    'plugin',
                    'ENTSO-E uit (Mode24 leeg) — Dag overzicht en laadpaal-kosten in Status worden niet bijgewerkt',
                    'startup',
                )
        elif prijsbron == 'EnergyZero':
            easee_logging.info(
                'plugin',
                'EnergyZero actief — kosten na eerste poll',
                'startup',
            )
        easee_logging.info('plugin', 'Initiële sync wacht op Domoticz Devices-readiness', 'startup')

    def onStop(self):
        easee_state.sync_tibber_token_backup(self)
        easee_state.sync_entsoe_token_backup(self)
        easee_state.sync_besteladen_hours_backup(self)
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
            if not self.access_token:
                logged_in = self._heartbeat_step('login', lambda: easee_api.login(self))
                if not logged_in:
                    self._heartbeat_step(
                        'login status',
                        lambda: domoticz_devices.update_core_text(self, 'Status', 'Login mislukt'),
                    )
                    easee_logging.info('plugin', 'Poll overgeslagen: login mislukt', 'poll')
                    return
            if not self.sync_done:
                self._heartbeat_step('startup sync', self.handle_startup_sync)
                if not self.sync_done:
                    return
            if self.icon_reapply_remaining > 0:
                def _reapply_icons():
                    domoticz_icons.load_custom_images(self, plugin_globals=globals())
                    domoticz_icons.apply_images_to_devices(self, force=True)
                    self.icon_reapply_remaining -= 1
                self._heartbeat_step('icon reapply', _reapply_icons)
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
            self._heartbeat_step('discovery refresh', self.refresh_entity_cache_only)
            self._heartbeat_step('poll', self.poll_all)
            self._heartbeat_step('ui update', self.update_combined)
            self._heartbeat_step('state save', lambda: easee_state.save_state(self))
        except Exception as e:
            self._log_heartbeat_exception('onHeartbeat', e)
            self._heartbeat_step(
                'status after error',
                lambda: domoticz_devices.update_core_text(self, 'Status', f'Fout: {e}'),
            )


_plugin = BasePlugin()

def onStart(): _plugin.onStart()
def onStop(): _plugin.onStop()
def onHeartbeat():
    try:
        _plugin.onHeartbeat()
    except Exception as e:
        try:
            easee_logging.error(
                'plugin',
                f'heartbeat exception: onHeartbeat (module): {e}\n{traceback.format_exc()}',
                'heartbeat',
            )
        except Exception:
            pass
