# -*- coding: utf-8 -*-
"""
<plugin key="EaseeCloudAutoDiscoveryV1000" name="Easee Domoticz plugin v10.5.12" author="Richard Leunk" version="10.5.12"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://github.com/rleunk/easee-domoticz">
    <description>
        <h2>Easee Domoticz plugin v10.5.12</h2><br/>
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
import os, json, time, hashlib, math
from datetime import datetime
try:
    import requests
except Exception:
    requests = None

BASE_URL = 'https://api.easee.com/api'
LOGIN_URL = BASE_URL + '/accounts/login'
REFRESH_URL = BASE_URL + '/accounts/refresh_token'
TIBBER_GQL = 'https://api.tibber.com/v1-beta/gql'
STATE_FILE = 'easee_v9_0_state.json'
PLUGIN_KEY = 'EaseeCloudAutoDiscoveryV1000'
ULTRA_DEBUG = False

OP_MODE_LABELS = {
    0: 'Offline',
    1: 'Geen auto',
    2: 'Wacht op start',
    3: 'Laden',
    4: 'Voltooid',
    5: 'Fout',
    6: 'Klaar om te laden',
    7: 'Wacht op autorisatie',
    8: 'Bezig met afmelden',
}

DEVICE_TYPES = {
    'Text':      {'Type': 243, 'Subtype': 19},
    'Switch':    {'Type': 244, 'Subtype': 73, 'Switchtype': 0},
    'Energy':    {'Type': 243, 'Subtype': 29},
    'CustomkWh': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;kWh'}},
    'CustomEUR': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;€'}},
}

CORE_DEVICE_IDS = {
    'Status': 'EASEE_CORE_STATUS',
    'Totaal Laden': 'EASEE_CORE_ENERGY',
    'Totaal kWh': 'EASEE_CORE_KWH',
    'LoadBal': 'EASEE_CORE_LOADBAL',
    'Kosten & Samenvatting': 'EASEE_CORE_COSTS',
    'Beste laden': 'EASEE_CORE_BEST',
}

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
    def log(self, msg): Domoticz.Log(f'[Easee v10.5.12] {msg}')
    def debug(self, msg):
        if Parameters.get('Mode6') == 'Debug':
            Domoticz.Debug(f'[Easee v10.5.12] {msg}')
    def error(self, msg): Domoticz.Error(f'[Easee v10.5.12] {msg}')

    # ---- helpers ----
    def norm(self, value):
        return ' '.join(str(value).strip().split())
    def prefix(self):
        return 'Easee'
    def extra_charger_names(self):
        raw = (Parameters.get('Mode4', '') or '').strip()
        if not raw or raw.lower() == 'easee':
            return []
        return [self.clean_label(part.strip()) for part in raw.split(',') if part.strip()]
    def pref(self, label):
        return f'{self.prefix()} - {label}'
    def clean_label(self, name):
        """Verwijder dubbele Easee/hardware prefix uit device-namen."""
        name = self.norm(name)
        if not name:
            return name
        prefixes = []
        for p in (self.prefix(), 'Easee'):
            p = str(p).strip()
            if p and p.lower() not in [x.lower() for x in prefixes]:
                prefixes.append(p)
        changed = True
        while changed:
            changed = False
            for p in prefixes:
                token = f'{p} - '
                if name.lower().startswith(token.lower()):
                    name = name[len(token):].strip()
                    changed = True
        return name
    def safe_float(self, value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default
    def safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
    def truthy(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1','true','yes','on')
        if isinstance(value, (int,float)):
            return bool(value)
        return False
    def euro_str(self, value):
        try:
            return f'{float(value):.2f}'
        except Exception:
            return '0.00'
    def power_watts(self, value):
        x = self.safe_float(value, 0.0)
        if 0 < abs(x) < 100:
            x *= 1000.0
        if x < 0:
            x = 0.0
        return int(round(x))
    def kwh_value(self, value):
        x = self.safe_float(value, 0.0)
        if x > 10000:
            x /= 1000.0
        if x < 0:
            x = 0.0
        return round(x, 3)
    def wh_from_kwh(self, value):
        try:
            return int(round(float(value) * 1000.0))
        except Exception:
            return 0
    def poll_interval_sec(self):
        return max(10, self.safe_int(Parameters.get('Mode1', '30'), 30))
    def session_energy_kwh(self, values, session):
        for source in (values, session if isinstance(session, dict) else {}):
            if not isinstance(source, dict):
                continue
            val = source.get('sessionEnergy')
            if val is not None:
                return self.kwh_value(val)
        return None
    def power_integrated_kwh(self, power_w):
        if power_w <= 50:
            return 0.0
        interval = float(self.poll_interval_sec())
        return round((float(power_w) / 1000.0) * (interval / 3600.0), 6)
    def short_id(self, full_id):
        s = str(full_id).strip()
        return s[-8:] if len(s) > 8 else s
    def custom_charger_name(self, index):
        if index == 0:
            return self.clean_label(Parameters.get('Mode2', '') or '')
        if index == 1:
            return self.clean_label(Parameters.get('Mode3', '') or '')
        extras = self.extra_charger_names()
        extra_index = index - 2
        if 0 <= extra_index < len(extras):
            return extras[extra_index]
        return ''
    def charger_display_name(self, charger, index):
        custom = self.custom_charger_name(index)
        if custom:
            return custom
        api_name = self.clean_label(str(charger.get('name') or '').strip())
        cid = str(charger.get('id') or '').strip()
        if api_name and api_name.lower() not in (cid.lower(), self.short_id(cid).lower()):
            return api_name
        return f'Laadpaal {index + 1}'
    def charger_dev_name(self, display, label):
        return self.clean_label(f'{display} - {label}')
    def custom_equalizer_name(self):
        return self.clean_label(Parameters.get('Address', '') or '')
    def manual_equalizer_id(self):
        return str(Parameters.get('IP', '') or '').strip()
    def equalizer_display_name(self, equalizer, index):
        custom = self.custom_equalizer_name()
        if custom and index == 0:
            return custom
        api_name = self.clean_label(str(equalizer.get('name') or '').strip())
        eid = str(equalizer.get('id') or '').strip()
        if api_name and api_name.lower() not in (eid.lower(), self.short_id(eid).lower(), 'circuit', 'equalizer'):
            return api_name
        return 'Equalizer' if index == 0 else f'Equalizer {index + 1}'
    def equalizer_dev_name(self, display, label):
        return self.clean_label(f'{display} - {label}')
    def make_charger_device_id(self, cid, label_key):
        raw = f'{cid}|{label_key}'.encode('utf-8', errors='ignore')
        return 'EASEE_CHG_' + hashlib.sha1(raw).hexdigest()[:24].upper()
    def make_equalizer_device_id(self, eid, label_key):
        raw = f'{eid}|{label_key}'.encode('utf-8', errors='ignore')
        return 'EASEE_EQ_' + hashlib.sha1(raw).hexdigest()[:24].upper()
    def make_device_id(self, name):
        raw = self.norm(name).encode('utf-8', errors='ignore')
        return 'EASEE_' + hashlib.sha1(raw).hexdigest()[:28].upper()
    def now_ts(self):
        return time.time()
    def today_key(self):
        return datetime.now().strftime('%Y-%m-%d')
    def parse_iso(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return None
    def tibber_token(self):
        return (Parameters.get('Mode7', '') or '').strip()
    def tibber_enabled(self):
        return bool(self.tibber_token())

    # ---- emoji & status helpers ----
    def op_mode_label(self, value):
        if value is None or value == '':
            return 'Onbekend'
        try:
            return OP_MODE_LABELS.get(int(value), f'Modus {int(value)}')
        except Exception:
            text = str(value).strip()
            return text if text else 'Onbekend'
    def power_emoji(self, power_w):
        """Emoji based on power level"""
        if power_w >= 7000:
            return '⚡⚡'
        elif power_w >= 3500:
            return '⚡'
        elif power_w > 50:
            return '🔌'
        else:
            return '⏸️'

    def status_emoji(self, online, session_active):
        """Emoji for charger status"""
        if not online:
            return '❌'
        elif session_active:
            return '✅'
        else:
            return '🔴'

    def price_emoji(self, price_total, cache):
        """Emoji for price level"""
        if not cache:
            return '⚪'
        prices = sorted(self.safe_float(v.get('total'), 0.0) for v in cache.values() if isinstance(v, dict))
        if len(prices) < 3:
            return '⚪'
        lo = prices[max(0, int(len(prices)*0.33)-1)]
        hi = prices[max(0, int(len(prices)*0.66)-1)]
        if price_total <= lo:
            return '🟢'
        if price_total >= hi:
            return '🔴'
        return '🟡'

    # ---- state ----
    def state_path(self):
        return os.path.join(self.plugin_dir, STATE_FILE)
    def load_state(self):
        try:
            fp = self.state_path()
            if os.path.isfile(fp):
                with open(fp, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.state.update(loaded)
        except Exception as e:
            self.debug(f'state load failed: {e}')
    def save_state(self):
        try:
            with open(self.state_path(), 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.debug(f'state save failed: {e}')

    # ---- index ----
    def rebuild_index(self):
        self.units_by_name = {}
        self.units_by_devid = {}
        for unit, dev in Devices.items():
            self.units_by_name[self.norm(dev.Name)] = unit
            devid = getattr(dev, 'DeviceID', '') or ''
            if devid:
                self.units_by_devid[str(devid)] = unit
    def find_unit(self, name):
        return self.units_by_name.get(self.norm(name))
    def find_unit_by_devid(self, devid):
        return self.units_by_devid.get(str(devid))
    def resolve_unit(self, name):
        return self.find_unit(name) or self.find_unit_by_devid(self.make_device_id(name))
    def resolve_charger_unit(self, cid, label_key):
        return self.find_unit_by_devid(self.make_charger_device_id(cid, label_key))
    def resolve_equalizer_unit(self, eid, label_key):
        return self.find_unit_by_devid(self.make_equalizer_device_id(eid, label_key))
    def resolve_core_unit(self, label):
        label = self.clean_label(label)
        devid = CORE_DEVICE_IDS.get(label)
        if devid:
            u = self.find_unit_by_devid(devid)
            if u is not None:
                return u
        return self.find_unit(label)
    def sync_device_name(self, unit, name):
        key = self.clean_label(name)
        try:
            current = self.norm(Devices[unit].Name)
            if current == key:
                return
            Devices[unit].Name = key
            self.rebuild_index()
        except Exception as e:
            self.debug(f'device rename failed unit {unit}: {e}')
    def next_free_unit(self):
        for unit in range(1, 256):
            if unit not in Devices:
                return unit
        self.error('Geen vrije Unit meer beschikbaar (1-255)')
        return None

    # ---- images ----
    def image_root(self, name):
        n = name.lower()
        if 'overzicht' in n or 'beste laden' in n:
            return 'EaseeOverview'
        if 'kosten' in n or 'goedkoop' in n or '€' in n:
            return 'EaseeCost'
        if 'status' in n:
            return 'EaseeStatus'
        if 'loadbal' in n:
            return 'EaseeLoadBal'
        if 'equalizer' in n or 'meterkast' in n:
            return 'EaseeEqualizer'
        if 'totaal & sessie' in n or ' laden' in n or 'totaal kwh' in n:
            return 'EaseePower'
        return 'EaseeCharger'
    def icon_base(self, root):
        return f'{PLUGIN_KEY}{root}'

    def _icon_images_key(self, root):
        if root in Images:
            return root
        prefixed = self.icon_base(root)
        if prefixed in Images:
            return prefixed
        return None

    def _collect_image_ids(self):
        roots = ['EaseeCharger','EaseeEqualizer','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
        found = {}
        for r in roots:
            key = self._icon_images_key(r)
            if key:
                found[r] = Images[key].ID
        return found

    def _try_create_icon_zip(self, fn):
        errors = []
        for attempt in (lambda: Domoticz.Image(fn).Create(), lambda: Domoticz.Image(Filename=fn).Create()):
            try:
                attempt()
                return True, errors
            except Exception as e:
                errors.append(str(e))
        return False, errors

    def load_custom_images(self):
        roots = ['EaseeCharger','EaseeEqualizer','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
        candidates = ['Easee_icons_v2.zip', 'Easee_icons.zip']
        loaded_zip = None
        load_errors = []
        found_zips = []
        zip_loaded = False
        preloaded = self._collect_image_ids()
        if len(preloaded) == len(roots):
            self.image_ids = preloaded
            self.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(self.image_ids)} sets')
            return
        for fn in candidates:
            path = os.path.join(self.plugin_dir, fn)
            if not os.path.isfile(path):
                continue
            found_zips.append(fn)
            try:
                if any(self._icon_images_key(r) is None for r in roots):
                    self.log(f'Custom icons laden uit {fn} (map: {self.plugin_dir})')
                    ok, create_errors = self._try_create_icon_zip(fn)
                    if ok:
                        zip_loaded = True
                    elif create_errors:
                        msg = f'{fn}: Create() mislukt ({"; ".join(create_errors)})'
                        load_errors.append(msg)
                        self.error(msg)
                self.image_ids = self._collect_image_ids()
                if self.image_ids:
                    loaded_zip = fn
                    break
                missing = [r for r in roots if self._icon_images_key(r) is None]
                if missing:
                    load_errors.append(f'{fn}: icons niet in Images ({", ".join(missing[:3])}{"..." if len(missing) > 3 else ""})')
            except Exception as e:
                msg = f'{fn}: {e}'
                load_errors.append(msg)
                self.error(msg)
        if not self.image_ids and preloaded:
            self.image_ids = preloaded
            self.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(self.image_ids)} sets')
        elif self.image_ids:
            if zip_loaded and loaded_zip:
                self.log(f'Custom icons geladen: {len(self.image_ids)} sets ({loaded_zip})')
            else:
                self.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(self.image_ids)} sets')
        elif found_zips:
            self.log('Waarschuwing: zip gevonden maar laden mislukt — upload handmatig via Instellingen → Meer opties → Aangepaste pictogrammen')
            self.log(f'Icon zip zoekpad: {self.plugin_dir}')
            for fn in found_zips:
                self.log(f'  {fn}: aanwezig')
            if load_errors:
                self.log('Icon zip laden mislukt: ' + '; '.join(load_errors))
        else:
            self.log('Waarschuwing: geen custom icon zip gevonden — standaard Domoticz iconen worden gebruikt')
            self.log(f'Icon zip zoekpad: {self.plugin_dir}')
            for fn in candidates:
                path = os.path.join(self.plugin_dir, fn)
                self.log(f'  {fn}: {"aanwezig" if os.path.isfile(path) else "ontbreekt"}')

    def apply_images_to_devices(self):
        if not self.image_ids:
            return
        updated = 0
        for unit, dev in Devices.items():
            try:
                root = self.image_root(self.norm(dev.Name))
                img_id = self.image_ids.get(root)
                if not img_id or getattr(dev, 'Image', 0) == img_id:
                    continue
                dev.Update(nValue=dev.nValue, sValue=str(dev.sValue), Image=img_id)
                updated += 1
            except Exception as e:
                self.debug(f'icon update failed unit {unit}: {e}')
        if updated:
            self.log(f'Custom icons toegepast op {updated} devices')

    # ---- create/update ----
    def ensure_device_once(self, name, typename, device_id=None, legacy_names=None):
        key = self.clean_label(name)
        devid = device_id or self.make_device_id(key)
        unit = self.find_unit_by_devid(devid) if device_id else None
        if unit is None:
            for legacy in (legacy_names or []):
                legacy_key = self.clean_label(legacy)
                unit = self.find_unit_by_devid(self.make_device_id(legacy_key)) or self.find_unit(legacy_key)
                if unit is not None:
                    break
        if unit is None and not device_id:
            unit = self.find_unit_by_devid(devid) or self.find_unit(key)
        if unit is not None:
            self.sync_device_name(unit, key)
            return unit
        unit = self.next_free_unit()
        if unit is None:
            return None
        spec = DEVICE_TYPES.get(typename, DEVICE_TYPES['Text'])
        kwargs = {'Name': key, 'Unit': int(unit), 'DeviceID': devid}
        if 'TypeName' in spec:
            kwargs['TypeName'] = spec['TypeName']
        else:
            kwargs['Type'] = spec['Type']
            kwargs['Subtype'] = spec['Subtype']
            if 'Switchtype' in spec:
                kwargs['Switchtype'] = spec['Switchtype']
            if 'Options' in spec:
                kwargs['Options'] = spec['Options']
        root = self.image_root(key)
        if root in self.image_ids:
            kwargs['Image'] = self.image_ids[root]
        try:
            Domoticz.Device(**kwargs).Create()
        except Exception:
            kwargs.pop('Image', None)
            try:
                Domoticz.Device(**kwargs).Create()
            except Exception as e:
                self.error(f'Device creation failed for {key}: {e}')
                return None
        self.rebuild_index()
        return self.resolve_unit(key)
    def update_core_text(self, label, value):
        u = self.resolve_core_unit(self.clean_label(label))
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value)[:4000])
    def update_core_custom(self, label, value):
        u = self.resolve_core_unit(self.clean_label(label))
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value))
    def update_core_energy(self, label, power_w, total_wh):
        u = self.resolve_core_unit(self.clean_label(label))
        if u is not None:
            Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')
    def update_core_sw(self, label, value):
        u = self.resolve_core_unit(self.clean_label(label))
        if u is not None:
            state = self.truthy(value)
            Devices[u].Update(nValue=1 if state else 0, sValue='Aan' if state else 'Uit')
    def update_text(self, name, value):
        u = self.resolve_unit(name)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value)[:4000])
    def update_custom(self, name, value):
        u = self.resolve_unit(name)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value))
    def update_energy(self, name, power_w, total_wh):
        u = self.resolve_unit(name)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')
    def update_sw(self, name, value):
        u = self.resolve_unit(name)
        if u is not None:
            state = self.truthy(value)
            Devices[u].Update(nValue=1 if state else 0, sValue='Aan' if state else 'Uit')
    def update_charger_text(self, cid, label_key, value):
        u = self.resolve_charger_unit(cid, label_key)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value)[:4000])
    def update_charger_custom(self, cid, label_key, value):
        u = self.resolve_charger_unit(cid, label_key)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value))
    def update_charger_costs(self, cid, session_cost, day_cost, session_kwh, session_active):
        u = self.resolve_charger_unit(cid, 'Kosten (Sessie/Dag)')
        if u is None:
            return
        tibber_rate = self.safe_float(self.current_tibber_price().get('total'), 0.0)
        rate = session_cost / session_kwh if session_kwh > 0 else tibber_rate
        price_emoji = self.price_emoji(rate, self.state.get('price_cache', {}))
        session_label = 'Sessie' if session_active else 'Laatste sessie'
        text = f'{price_emoji} {session_label}: €{self.euro_str(session_cost)} | Dag: €{self.euro_str(day_cost)}'
        try:
            is_text = int(Devices[u].SubType) == DEVICE_TYPES['Text']['Subtype']
        except Exception:
            is_text = False
        if is_text:
            Devices[u].Update(nValue=0, sValue=text[:4000])
        else:
            Devices[u].Update(nValue=0, sValue=self.euro_str(session_cost))
    def update_charger_energy(self, cid, label_key, power_w, total_wh):
        u = self.resolve_charger_unit(cid, label_key)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')
    def update_equalizer_text(self, eid, label_key, value):
        u = self.resolve_equalizer_unit(eid, label_key)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=str(value)[:4000])
    def update_equalizer_energy(self, eid, label_key, power_w, total_wh=0):
        u = self.resolve_equalizer_unit(eid, label_key)
        if u is not None:
            Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')

    # ---- Easee API ----
    def login(self):
        try:
            r = self.session.post(LOGIN_URL, json={'userName': Parameters.get('Username',''), 'password': Parameters.get('Password','')}, timeout=20)
            if r.status_code == 200:
                data = r.json()
                self.access_token = data.get('accessToken','')
                self.refresh_token = data.get('refreshToken','')
                return bool(self.access_token)
            self.error(f'Login mislukt, HTTP {r.status_code}: {r.text[:300]}')
        except Exception as e:
            self.error(f'Login exception: {e}')
        return False
    def refresh(self):
        if not self.access_token or not self.refresh_token:
            return self.login()
        try:
            r = self.session.post(REFRESH_URL, json={'accessToken': self.access_token, 'refreshToken': self.refresh_token}, timeout=20)
            if r.status_code == 200:
                data = r.json()
                self.access_token = data.get('accessToken','')
                self.refresh_token = data.get('refreshToken','')
                return bool(self.access_token)
        except Exception:
            pass
        return self.login()
    def api_get(self, path, retry=True):
        r = self.session.get(BASE_URL + path, headers={'Authorization': f'Bearer {self.access_token}'}, timeout=20)
        if r.status_code == 401 and retry:
            if self.refresh():
                return self.api_get(path, False)
        r.raise_for_status()
        return r.json() if r.text else None
    def api_get_optional(self, path):
        try:
            return self.api_get(path)
        except Exception as e:
            self.debug(f'GET {path} optioneel mislukt: {e}')
            return None

    def kw_to_watts(self, value):
        x = self.safe_float(value, 0.0)
        if x <= 0:
            return 0
        if abs(x) < 100:
            return int(round(x * 1000.0))
        return int(round(x))
    def format_amp(self, value):
        x = self.safe_float(value, 0.0)
        if x <= 0:
            return None
        if abs(x - round(x)) < 0.05:
            return f'{int(round(x))} A'
        return f'{x:.1f} A'
    def current_from_power_3phase(self, power_w):
        """Bereken lijnstroom (A) uit actief vermogen op 3×230 V."""
        p = self.safe_float(power_w, 0.0)
        if p <= 0:
            return 0.0
        return p / (math.sqrt(3.0) * 230.0)
    def amps_balanced_3phase_from_power(self, power_w, voltage=230):
        """Max import vermogen (W) → lijnstroom (A) bij evenwichtige 3-fase (17200 W → 24,9 A)."""
        p = self.safe_float(power_w, 0.0)
        if p <= 0:
            return 0.0
        return p / (3.0 * voltage)
    def phase_currents_from_values(self, values):
        phases = []
        any_obs = False
        for key in ('currentL1', 'currentL2', 'currentL3'):
            if key in values and values.get(key) is not None:
                any_obs = True
                phases.append(self.safe_float(values.get(key), 0.0))
            else:
                phases.append(None)
        if not any_obs:
            return None, None, None, 0.0, False
        nums = [p for p in phases if p is not None]
        load_a = max(nums) if nums else 0.0
        return phases[0], phases[1], phases[2], load_a, True
    def format_phase_amp(self, val):
        if val is None:
            return '—'
        if val <= 0:
            return '0.0'
        if abs(val - round(val)) < 0.05:
            return f'{int(round(val))}.0'
        return f'{val:.1f}'
    def actual_current_line(self, values, power_w):
        l1, l2, l3, load_a, has_phases = self.phase_currents_from_values(values)
        if has_phases:
            parts = [self.format_phase_amp(v) for v in (l1, l2, l3)]
            return f'📊 L1/L2/L3: {" / ".join(parts)} A', load_a
        calc_a = self.current_from_power_3phase(power_w)
        if calc_a > 0:
            return f'📊 Actuele stroom: {calc_a:.1f} A (3-fase)', calc_a
        return None, 0.0
    def format_kw(self, value):
        x = self.safe_float(value, 0.0)
        if x <= 0:
            return None
        if abs(x) >= 100:
            x /= 1000.0
        if abs(x - round(x)) < 0.05:
            return f'{int(round(x))} kW'
        return f'{x:.1f} kW'
    def first_dict_value(self, data, keys):
        if not isinstance(data, dict):
            return None
        for key in keys:
            if data.get(key) is not None:
                return data.get(key)
        return None
    def amp_value(self, value):
        x = self.safe_float(value, 0.0)
        if x <= 0 or x > 200:
            return 0.0
        return x
    def is_same_as_main_fuse(self, fuse_a, main_fuse_a):
        return main_fuse_a > 0 and fuse_a > 0 and abs(fuse_a - main_fuse_a) < 0.5
    def fuse_limit_keys(self):
        return (
            'fuse', 'mainFuseLimit', 'fuseLimit', 'mainFuseCurrentLimit',
            'mainFuseLimitCurrent', 'maxFuse', 'maxFuseCurrent', 'fuseCurrent',
            'mainFuseLimitAmps', 'mainFuseCurrentLimitAmps',
            'mainCurrentLimit', 'currentLimit', 'importLimit', 'mainImportLimit',
            'householdCurrentLimit', 'gridCurrentLimit', 'maxImportCurrent',
            'maxMainCurrent', 'panelCurrentLimit', 'siteCurrentLimit',
        )
    def emobility_keys(self):
        return ('maxAllocatedCurrent', 'maxCurrent', 'eMobilityLimit', 'emobilityLimit')
    def offline_circuit_current_keys(self):
        return ('offlineMaxCircuitCurrentP1', 'offlineMaxCircuitCurrentP2', 'offlineMaxCircuitCurrentP3')
    def is_offline_circuit_current_key(self, key):
        if not isinstance(key, str):
            return False
        return key in self.offline_circuit_current_keys()
    def main_fuse_keys(self):
        return ('ratedCurrent', 'mainFuseSize', 'mainFuse')
    def is_fuse_limit_key(self, key):
        if not isinstance(key, str):
            return False
        kl = key.lower()
        if kl in ('ratedcurrent', 'mainfuse', 'mainfusesize', 'fusegroup', 'fuseid',
                  'maxallocatedcurrent', 'allocatedcurrent', 'maxcurrent', 'emobilitylimit',
                  'offlinemaxcircuitcurrentp1', 'offlinemaxcircuitcurrentp2', 'offlinemaxcircuitcurrentp3'):
            return False
        if kl in ('fuse', 'mainfuselimit', 'fuselimit', 'mainfusecurrentlimit',
                  'mainfuselimitcurrent', 'maxfuse', 'maxfusecurrent', 'fusecurrent',
                  'mainfuselimitamps', 'mainfusecurrentlimitamps', 'maincurrentlimit',
                  'currentlimit', 'importlimit', 'mainimportlimit', 'householdcurrentlimit',
                  'gridcurrentlimit', 'maximportcurrent', 'maxmaincurrent', 'panelcurrentlimit',
                  'sitecurrentlimit'):
            return True
        if 'fuselimit' in kl or 'fusecurrentlimit' in kl or 'mainfuselimit' in kl:
            return True
        if kl.endswith('fuse') or (kl.startswith('fuse') and 'rating' not in kl):
            return True
        if kl.endswith('limit') and any(x in kl for x in ('fuse', 'main', 'grid', 'import', 'household', 'panel', 'site')):
            return True
        return False
    def is_main_limit_key(self, key):
        if not isinstance(key, str):
            return False
        if self.is_fuse_limit_key(key):
            return True
        kl = key.lower()
        if kl in ('limit', 'maxlimit', 'currentlimit', 'importlimit'):
            return True
        return kl.endswith('limit') and 'circuit' not in kl and 'emobility' not in kl and 'charger' not in kl
    def is_emobility_key(self, key):
        if not isinstance(key, str):
            return False
        kl = key.lower()
        return kl in ('maxallocatedcurrent', 'maxcurrent', 'emobilitylimit', 'emobilitycurrent')
    def fuse_limit_from_dict(self, data):
        val = self.first_dict_value(data, self.fuse_limit_keys())
        return self.amp_value(val) if val is not None else 0.0
    def emobility_from_dict(self, data):
        val = self.first_dict_value(data, self.emobility_keys())
        return self.amp_value(val) if val is not None else 0.0
    def root_circuit_ids(self, circuits):
        if not isinstance(circuits, list):
            return set()
        roots = set()
        all_ids = set()
        child_ids = set()
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            cid = circuit.get('id')
            if cid is not None:
                all_ids.add(str(cid))
            parent = circuit.get('parentCircuitId')
            if parent not in (None, 0, '0', ''):
                child_ids.add(str(parent))
            elif cid is not None:
                roots.add(str(cid))
        for cid in all_ids:
            if cid not in child_ids:
                roots.add(cid)
        return roots
    def _unique_circuits(self, circuits):
        unique = []
        seen = set()
        if not isinstance(circuits, list):
            return unique
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            cid = circuit.get('id')
            cid_s = str(cid) if cid is not None else ''
            if not cid_s or cid_s in seen:
                continue
            seen.add(cid_s)
            unique.append(circuit)
        return unique
    def fuse_limit_from_circuits(self, circuits, circuit_id=None, main_fuse_a=0.0):
        if not isinstance(circuits, list):
            return 0.0, ''
        preferred = None
        root = None
        fallback = None
        target_id = str(circuit_id) if circuit_id is not None else None
        root_ids = self.root_circuit_ids(circuits)
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            fuse_a = self.fuse_limit_from_dict(circuit)
            if fuse_a <= 0 or self.is_same_as_main_fuse(fuse_a, main_fuse_a):
                continue
            cid = circuit.get('id')
            cid_s = str(cid) if cid is not None else ''
            if target_id and cid_s == target_id:
                preferred = (fuse_a, f'circuit[{cid}].fuse')
            if cid_s in root_ids:
                root = (fuse_a, f'circuit[{cid}].fuse(root)')
            if fallback is None:
                fallback = (fuse_a, f'circuit[{cid}].fuse')
        pick = preferred or root or fallback
        if pick:
            return pick[0], pick[1]
        return 0.0, ''
    def fuse_limit_from_circuit_states(self, circuit_states, circuit_id=None, main_fuse_a=0.0):
        if not isinstance(circuit_states, list):
            return 0.0, ''
        circuits = []
        for item in circuit_states:
            if not isinstance(item, dict):
                continue
            circuit = item.get('circuit')
            if isinstance(circuit, dict):
                circuits.append(circuit)
        fuse_a, path = self.fuse_limit_from_circuits(circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
        if fuse_a > 0 and path:
            return fuse_a, f'circuitStates.{path}'
        return fuse_a, path
    def parse_site_structure_json(self, raw):
        if raw is None:
            return {}
        data = raw
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                return {}
            try:
                data = json.loads(text)
            except Exception:
                return {}
        if isinstance(data, str):
            text = data.strip()
            if text:
                try:
                    data = json.loads(text)
                except Exception:
                    return {}
        if not isinstance(data, dict):
            return {}
        return data
    def deep_scan_amp_keys(self, obj, key_matcher, path=''):
        found = []
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f'{path}.{key}' if path else str(key)
                if key_matcher(key):
                    amps = self.amp_value(val)
                    if amps > 0:
                        found.append((p, amps))
                if isinstance(val, (dict, list)):
                    found.extend(self.deep_scan_amp_keys(val, key_matcher, p))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                found.extend(self.deep_scan_amp_keys(item, key_matcher, f'{path}[{idx}]'))
        return found
    def deep_scan_amp_range(self, obj, path='', min_a=15.0, max_a=30.0, depth=0, max_depth=14):
        """Zoek numerieke waarden in amp-range (voor fuse-limiet diagnostiek)."""
        found = []
        if depth > max_depth:
            return found
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f'{path}.{key}' if path else str(key)
                if isinstance(val, bool):
                    continue
                if isinstance(val, (int, float)):
                    if min_a <= float(val) <= max_a:
                        found.append(f'{p}={val}')
                elif isinstance(val, str) and val.strip():
                    s = val.strip()
                    try:
                        num = float(s)
                        if min_a <= num <= max_a:
                            found.append(f'{p}={s}')
                    except Exception:
                        pass
                elif isinstance(val, (dict, list)):
                    found.extend(self.deep_scan_amp_range(val, p, min_a, max_a, depth + 1, max_depth))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj[:32]):
                found.extend(self.deep_scan_amp_range(item, f'{path}[{idx}]', min_a, max_a, depth + 1, max_depth))
        return found
    def is_valid_fuse_limit(self, val, main_fuse_a=0.0):
        if val <= 0 or val > 63:
            return False
        if self.is_same_as_main_fuse(val, main_fuse_a):
            return False
        if main_fuse_a > 0 and val >= main_fuse_a - 0.4:
            return False
        return True
    def pick_best_fuse_candidate(self, candidates, main_fuse_a=0.0):
        if not candidates:
            return 0.0, ''
        candidates = {
            path: val for path, val in candidates.items()
            if self.is_valid_fuse_limit(val, main_fuse_a)
        }
        if not candidates:
            return 0.0, ''
        def score(path_val):
            path, val = path_val
            pl = path.lower()
            s = 0
            if pl.endswith('.fuse') or '.fuse(' in pl:
                s += 60
            if '(root)' in pl:
                s += 35
            if 'site.state' in pl or 'circuitstates.circuit' in pl:
                s += 30
            if 'mainpanel' in pl or '.site.' in pl or pl.startswith('site.'):
                s += 28
            if 'sitestructure.maxcontinuouscurrent' in pl:
                s += 48
            elif 'sitestructure' in pl:
                s += 22
            if 'cloud-loadbalancing' in pl:
                s += 18
            if 'panel' in pl and 'circuit' not in pl:
                s += 15
            if 'circuit[' in pl:
                s += 12
            if 'settings' in pl and 'offline' not in pl:
                s += 8
            if main_fuse_a > 0 and val < main_fuse_a - 0.4:
                s += 25
            return s
        ranked = sorted(candidates.items(), key=lambda kv: (-score(kv), -kv[1], kv[0]))
        path, val = ranked[0]
        return val, path
    def add_fuse_candidate(self, candidates, amps, source, main_fuse_a=0.0, rejected=None):
        val = self.amp_value(amps)
        if not source or val <= 0:
            return
        if not self.is_valid_fuse_limit(val, main_fuse_a):
            if rejected is not None:
                reason = 'gelijk aan hoofdzekering' if self.is_same_as_main_fuse(val, main_fuse_a) else 'gefilterd'
                rejected.append(f'{source}={int(round(val))}A ({reason})')
            return
        existing = candidates.get(source)
        if existing is None or val > existing:
            candidates[source] = val
    def note_raw_fuse_value(self, raw_hits, amps, source):
        val = self.amp_value(amps)
        if source and val > 0:
            raw_hits.append(f'{source}={int(round(val))}A')
    def collect_fuse_from_circuits_list(self, circuits, prefix, candidates, main_fuse_a=0.0, rejected=None, raw_hits=None):
        if not isinstance(circuits, list):
            return 0.0, ''
        if raw_hits is not None:
            for circuit in circuits:
                if not isinstance(circuit, dict):
                    continue
                cid = circuit.get('id')
                if circuit.get('fuse') is not None:
                    self.note_raw_fuse_value(raw_hits, circuit.get('fuse'), f'{prefix}circuit[{cid}].fuse')
                for key, val in circuit.items():
                    if isinstance(key, str) and 'fuse' in key.lower() and key.lower() not in ('fusegroup', 'fuseid'):
                        self.note_raw_fuse_value(raw_hits, val, f'{prefix}circuit[{cid}].{key}')
        self.collect_explicit_circuit_fuses(
            circuits, prefix, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        rf, rs = self.root_circuit_fuse(circuits, main_fuse_a=main_fuse_a, rejected=rejected, raw_hits=raw_hits)
        return rf, rs
    def fetch_root_circuit_details(self, site_id, circuits, candidates, main_fuse_a=0.0, probes=None, rejected=None, raw_hits=None):
        if not site_id or not isinstance(circuits, list):
            return 0.0, ''
        root_ids = sorted(self.root_circuit_ids(circuits))
        best = 0.0
        best_src = ''
        for cid in root_ids:
            path = f'/sites/{site_id}/circuits/{cid}'
            if probes is not None:
                probes.append(path)
            circuit = self.api_get_optional(path)
            if isinstance(circuit, dict):
                if raw_hits is not None and circuit.get('fuse') is not None:
                    self.note_raw_fuse_value(raw_hits, circuit.get('fuse'), f'circuit[{cid}].fuse')
                self.collect_fuse_from_dict(
                    circuit, f'circuit[{cid}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
                fuse_a = self.fuse_limit_from_dict(circuit)
                if fuse_a > 0:
                    self.add_fuse_candidate(
                        candidates, fuse_a, f'circuit[{cid}].fuse(detail)',
                        main_fuse_a=main_fuse_a, rejected=rejected)
                    if self.is_valid_fuse_limit(fuse_a, main_fuse_a) and fuse_a > best:
                        best = fuse_a
                        best_src = f'circuit[{cid}].fuse(detail)'
            self.collect_fuse_from_circuit_settings(
                site_id, cid, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        return best, best_src
    def collect_fuse_from_dict(self, data, prefix, candidates, main_fuse_a=0.0, rejected=None):
        if not isinstance(data, dict):
            return
        fuse_a = self.fuse_limit_from_dict(data)
        if fuse_a > 0:
            self.add_fuse_candidate(candidates, fuse_a, f'{prefix}.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
        rated = self.amp_value(data.get('ratedCurrent'))
        if rated > 0:
            for key, val in data.items():
                if not isinstance(key, str):
                    continue
                kl = key.lower()
                if 'fuse' not in kl or kl in ('fusegroup', 'fuseid', 'ratedcurrent'):
                    continue
                fuse_val = self.amp_value(val)
                if fuse_val > 0 and not self.is_same_as_main_fuse(fuse_val, rated):
                    self.add_fuse_candidate(
                        candidates, fuse_val, f'{prefix}.{key}', main_fuse_a=main_fuse_a, rejected=rejected)
    def scan_any_fuse_keys(self, obj, prefix, candidates, main_fuse_a=0.0, rejected=None):
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f'{prefix}.{key}' if prefix else str(key)
                if isinstance(key, str) and 'fuse' in key.lower():
                    kl = key.lower()
                    if kl not in ('fusegroup', 'fuseid'):
                        self.add_fuse_candidate(candidates, val, p, main_fuse_a=main_fuse_a, rejected=rejected)
                if isinstance(val, (dict, list)):
                    self.scan_any_fuse_keys(val, p, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self.scan_any_fuse_keys(item, f'{prefix}[{idx}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    def collect_fuse_from_circuit_settings(self, site_id, circuit_id, candidates, main_fuse_a=0.0, rejected=None):
        if not site_id or circuit_id is None:
            return
        settings = self.api_get_optional(f'/sites/{site_id}/circuits/{circuit_id}/settings')
        if not isinstance(settings, dict):
            return
        self.collect_fuse_from_dict(settings, f'circuit[{circuit_id}].settings', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        self.scan_any_fuse_keys(settings, f'circuit[{circuit_id}].settings', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        phase_vals = []
        max_phase_vals = []
        for key in ('maxCircuitCurrentP1', 'maxCircuitCurrentP2', 'maxCircuitCurrentP3'):
            val = self.amp_value(settings.get(key))
            if val > 0:
                phase_vals.append(val)
                max_phase_vals.append(val)
                self.add_fuse_candidate(
                    candidates, val, f'circuit[{circuit_id}].settings.{key}',
                    main_fuse_a=main_fuse_a, rejected=rejected)
        for key in self.offline_circuit_current_keys():
            val = self.amp_value(settings.get(key))
            if val > 0 and rejected is not None:
                rejected.append(
                    f'circuit[{circuit_id}].settings.{key}={int(round(val))}A (offline fallback)')
        if max_phase_vals:
            self.add_fuse_candidate(
                candidates, min(max_phase_vals), f'circuit[{circuit_id}].settings.maxCircuitCurrentPhasesMin',
                main_fuse_a=main_fuse_a, rejected=rejected)
        elif phase_vals:
            self.add_fuse_candidate(
                candidates, min(phase_vals), f'circuit[{circuit_id}].settings.circuitCurrentMin',
                main_fuse_a=main_fuse_a, rejected=rejected)
    def collect_fuse_from_equalizer_circuit(self, site_id, circuit_id, candidates, main_fuse_a=0.0, rejected=None):
        if not site_id or circuit_id is None:
            return
        circuit = self.api_get_optional(f'/sites/{site_id}/circuits/{circuit_id}')
        if not isinstance(circuit, dict):
            return
        self.collect_fuse_from_dict(
            circuit, f'equalizerCircuit[{circuit_id}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        self.scan_any_fuse_keys(
            circuit, f'equalizerCircuit[{circuit_id}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        fuse_a = self.fuse_limit_from_dict(circuit)
        if fuse_a > 0:
            self.add_fuse_candidate(
                candidates, fuse_a, f'equalizerCircuit[{circuit_id}].fuse',
                main_fuse_a=main_fuse_a, rejected=rejected)
    def collect_explicit_circuit_fuses(self, circuits, prefix, candidates, main_fuse_a=0.0, root_only=False, rejected=None):
        if not isinstance(circuits, list):
            return
        root_ids = self.root_circuit_ids(circuits) if root_only else None
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            cid = circuit.get('id')
            cid_s = str(cid) if cid is not None else ''
            if root_only and cid_s not in root_ids:
                continue
            if circuit.get('fuse') is not None:
                fuse_val = self.amp_value(circuit.get('fuse'))
                tag = '(root)' if root_only else ''
                self.add_fuse_candidate(
                    candidates, fuse_val, f'{prefix}circuit[{cid}].fuse{tag}',
                    main_fuse_a=main_fuse_a, rejected=rejected)
            self.collect_fuse_from_dict(
                circuit, f'{prefix}circuit[{cid}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    def collect_fuse_from_cloud_loadbalancing(self, equalizer_id, candidates, main_fuse_a=0.0, probes=None):
        if not equalizer_id:
            return
        paths = [
            f'/cloud-loadbalancing/equalizer/{equalizer_id}/config',
            f'/cloud-loadbalancing/equalizers/{equalizer_id}/config',
            f'/cloud-loadbalancing/equalizer/{equalizer_id}/config/surplus-energy',
            f'/cloud-loadbalancing/equalizer/{equalizer_id}',
            f'/equalizers/{equalizer_id}/loadbalancing/config',
            f'/equalizers/{equalizer_id}/loadbalancing',
        ]
        for path in paths:
            if probes is not None:
                probes.append(path)
            data = self.api_get_optional(path)
            if not isinstance(data, dict):
                continue
            prefix = path.strip('/').replace('/', '.')
            self.collect_fuse_from_dict(data, prefix, candidates, main_fuse_a=main_fuse_a)
            self.scan_any_fuse_keys(data, prefix, candidates, main_fuse_a=main_fuse_a)
            for path2, amps in self.deep_scan_amp_keys(data, self.is_main_limit_key):
                self.add_fuse_candidate(candidates, amps, f'{prefix}.{path2}', main_fuse_a=main_fuse_a)
    def root_circuit_fuse(self, circuits, main_fuse_a=0.0, rejected=None, raw_hits=None):
        if not isinstance(circuits, list):
            return 0.0, ''
        root_ids = self.root_circuit_ids(circuits)
        best = 0.0
        best_src = ''
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            cid = circuit.get('id')
            cid_s = str(cid) if cid is not None else ''
            if cid_s not in root_ids:
                continue
            fuse_a = 0.0
            if circuit.get('fuse') is not None:
                fuse_a = self.amp_value(circuit.get('fuse'))
            if fuse_a <= 0:
                fuse_a = self.fuse_limit_from_dict(circuit)
            if fuse_a <= 0:
                for key, val in circuit.items():
                    if isinstance(key, str) and 'fuse' in key.lower():
                        kl = key.lower()
                        if kl in ('fusegroup', 'fuseid'):
                            continue
                        fuse_a = max(fuse_a, self.amp_value(val))
            if raw_hits is not None and fuse_a > 0:
                self.note_raw_fuse_value(raw_hits, fuse_a, f'circuit[{cid}].fuse(root-scan)')
            if not self.is_valid_fuse_limit(fuse_a, main_fuse_a):
                if rejected is not None and fuse_a > 0:
                    reason = 'gelijk aan hoofdzekering' if self.is_same_as_main_fuse(fuse_a, main_fuse_a) else 'gefilterd'
                    rejected.append(f'circuit[{cid}].fuse(root)={int(round(fuse_a))}A ({reason})')
                continue
            if fuse_a > best:
                best = fuse_a
                best_src = f'circuit[{cid}].fuse(root)'
        return best, best_src
    def select_main_fuse_limit(self, candidates, main_fuse_a=0.0, root_fuse=0.0, root_source=''):
        if root_fuse > 0 and root_source and self.is_valid_fuse_limit(root_fuse, main_fuse_a):
            return root_fuse, root_source
        if root_fuse > 0 and root_source:
            self.add_fuse_candidate(candidates, root_fuse, root_source, main_fuse_a=main_fuse_a)
        mcc_src = 'siteStructure.maxContinuousCurrent'
        if mcc_src in candidates and self.is_valid_fuse_limit(candidates[mcc_src], main_fuse_a):
            return candidates[mcc_src], mcc_src
        if not candidates:
            return 0.0, ''
        filtered = {
            src: val for src, val in candidates.items()
            if self.is_valid_fuse_limit(val, main_fuse_a)
        }
        if not filtered:
            return 0.0, ''
        values = list(filtered.values())
        if main_fuse_a > 0:
            below = [v for v in values if v < main_fuse_a - 0.4]
            if below:
                pick = max(below)
                for src, val in filtered.items():
                    if abs(val - pick) < 0.05:
                        return pick, src
        pick = max(values)
        for src, val in filtered.items():
            if abs(val - pick) < 0.05:
                return pick, src
        return pick, ''
    def collect_json_key_tree(self, obj, path='', depth=0, max_depth=6):
        parts = []
        if depth > max_depth:
            return parts
        if isinstance(obj, dict):
            keys = list(obj.keys())[:24]
            if keys:
                parts.append(f'{path}{{{",".join(str(k) for k in keys)}}}')
            for key in keys[:16]:
                val = obj.get(key)
                p = f'{path}.{key}' if path else str(key)
                if isinstance(val, dict):
                    parts.extend(self.collect_json_key_tree(val, p, depth + 1, max_depth))
                elif isinstance(val, list) and val and isinstance(val[0], dict):
                    parts.extend(self.collect_json_key_tree(val[0], f'{p}[0]', depth + 1, max_depth))
        return parts
    def log_site_structure_once(self, site_id, raw, candidates):
        key = str(site_id or 'unknown')
        if key in self.fuse_structure_logged:
            return
        self.fuse_structure_logged.add(key)
        keys = self.structure_top_keys(raw)
        cand_parts = [f'{src}={int(round(v))}A' for src, v in sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:16]]
        cand_text = ', '.join(cand_parts) if cand_parts else 'geen'
        key_text = ', '.join(keys[:14]) if keys else 'leeg'
        self.log(f'Equalizer siteStructure (site {key}): keys={key_text} | fuse kandidaten: {cand_text}')
        data = self.parse_site_structure_json(raw)
        if data:
            mcc = self.amp_value(data.get('maxContinuousCurrent'))
            rated = self.amp_value(data.get('ratedCurrent'))
            if mcc > 0:
                if rated > 0 and mcc < rated - 0.4:
                    self.log(f'siteStructure maxContinuousCurrent (site {key}): {int(round(mcc))}A (hoofdzekering limiet kandidaat)')
                else:
                    self.log(f'siteStructure maxContinuousCurrent (site {key}): {int(round(mcc))}A')
            tree = self.collect_json_key_tree(data, 'siteStructure')
            if tree:
                tree_text = ' | '.join(tree[:12])
                if len(tree_text) > 900:
                    tree_text = tree_text[:900] + '...'
                self.log(f'siteStructure structuur (site {key}): {tree_text}')
        self.log_site_structure_numerics_once(site_id, raw)
    def collect_numeric_values(self, obj, path='', depth=0, max_depth=12):
        found = []
        if depth > max_depth:
            return found
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f'{path}.{key}' if path else str(key)
                if isinstance(val, bool):
                    continue
                if isinstance(val, (int, float)):
                    found.append(f'{p}={val}')
                elif isinstance(val, str) and val.strip():
                    s = val.strip()
                    if s.replace('.', '', 1).replace('-', '', 1).isdigit():
                        found.append(f'{p}={s}')
                elif isinstance(val, (dict, list)):
                    found.extend(self.collect_numeric_values(val, p, depth + 1, max_depth))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj[:24]):
                found.extend(self.collect_numeric_values(item, f'{path}[{idx}]', depth + 1, max_depth))
        return found
    def log_site_structure_numerics_once(self, site_id, raw):
        key = str(site_id or 'unknown')
        if key in self.site_structure_numerics_logged:
            return
        self.site_structure_numerics_logged.add(key)
        data = self.parse_site_structure_json(raw)
        if not data:
            return
        amp_range = self.deep_scan_amp_range(data, 'siteStructure', min_a=15.0, max_a=30.0)
        if amp_range:
            chunk_size = 20
            for i in range(0, len(amp_range), chunk_size):
                chunk = amp_range[i:i + chunk_size]
                self.log(f'siteStructure amp-range 15-30 (site {key}): ' + '; '.join(chunk))
        if Parameters.get('Mode6') == 'Debug':
            numerics = self.collect_numeric_values(data, 'siteStructure')
            if numerics:
                chunk_size = 40
                for i in range(0, len(numerics), chunk_size):
                    chunk = numerics[i:i + chunk_size]
                    self.debug(f'siteStructure numerics (site {key}) [{i // chunk_size + 1}]: ' + '; '.join(chunk))
    def log_equalizer_fuse_once(self, eid, limit_a, source, probes=None, debug_hits=None, raw_hits=None, rejected=None):
        key = str(eid or '')
        if not key or key in self.fuse_first_poll_logged:
            return
        self.fuse_first_poll_logged.add(key)
        if limit_a > 0:
            self.log(f'Equalizer fuse: limit={int(round(limit_a))}A src={source}')
        else:
            parts = []
            if probes:
                parts.append('probes: ' + ', '.join(probes[:16]))
            if raw_hits:
                parts.append('gevonden: ' + '; '.join(raw_hits[:16]))
            if rejected:
                parts.append('afgewezen: ' + '; '.join(rejected[:12]))
            if debug_hits:
                parts.append('keys: ' + '; '.join(debug_hits[:20]))
            self.log('Equalizer fuse: limit=onbekend | ' + (' | '.join(parts) if parts else 'geen fuse-data'))
    def fuse_limit_from_deep_scan(self, obj, source_prefix='', main_fuse_a=0.0):
        candidates = {}
        for path, amps in self.deep_scan_amp_keys(obj, self.is_fuse_limit_key):
            full = f'{source_prefix}.{path}' if source_prefix else path
            candidates[full] = amps
        for path, amps in self.deep_scan_amp_keys(obj, self.is_main_limit_key):
            full = f'{source_prefix}.{path}' if source_prefix else path
            if full not in candidates:
                candidates[full] = amps
        if not candidates:
            return 0.0, ''
        val, path = self.pick_best_fuse_candidate(candidates, main_fuse_a=main_fuse_a)
        return val, path
    def collect_fuse_debug(self, obj, path=''):
        found = []
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f'{path}.{key}' if path else str(key)
                kl = str(key).lower()
                if (self.is_fuse_limit_key(key) or self.is_emobility_key(key)
                        or self.is_main_limit_key(key)
                        or kl in ('ratedcurrent', 'maxallocatedcurrent', 'limit')):
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        found.append(f'{p}={val}')
                    elif isinstance(val, str) and val.strip().replace('.', '', 1).replace('-', '', 1).isdigit():
                        found.append(f'{p}={val.strip()}')
                if isinstance(val, (dict, list)):
                    found.extend(self.collect_fuse_debug(val, p))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj[:8]):
                found.extend(self.collect_fuse_debug(item, f'{path}[{idx}]'))
        return found
    def structure_top_keys(self, raw):
        data = self.parse_site_structure_json(raw)
        if not data:
            return []
        keys = list(data.keys())[:20]
        for nest_key in ('site', 'panel', 'mainPanel', 'root', 'limits', 'loadBalancing'):
            nested = data.get(nest_key)
            if isinstance(nested, dict):
                keys.append(f'{nest_key}:{{{",".join(list(nested.keys())[:12])}}}')
        return keys
    def fuse_limit_from_site_structure(self, raw, main_fuse_a=0.0, candidates=None):
        data = self.parse_site_structure_json(raw)
        if not data:
            return 0.0, ''
        mcc = self.amp_value(data.get('maxContinuousCurrent'))
        if mcc > 0 and self.is_valid_fuse_limit(mcc, main_fuse_a):
            if candidates is not None:
                self.add_fuse_candidate(
                    candidates, mcc, 'siteStructure.maxContinuousCurrent',
                    main_fuse_a=main_fuse_a)
        if candidates is not None:
            self.collect_fuse_from_dict(data, 'siteStructure', candidates, main_fuse_a=main_fuse_a)
            self.scan_any_fuse_keys(data, 'siteStructure', candidates, main_fuse_a=main_fuse_a)
        direct = self.fuse_limit_from_dict(data)
        if direct > 0 and not self.is_same_as_main_fuse(direct, main_fuse_a):
            if candidates is not None:
                self.add_fuse_candidate(candidates, direct, 'siteStructure.fuse', main_fuse_a=main_fuse_a)
            return direct, 'siteStructure.fuse'
        for key in ('site', 'panel', 'root', 'mainPanel', 'main', 'limits', 'loadBalancing', 'energy'):
            nested = data.get(key)
            if isinstance(nested, dict):
                if candidates is not None:
                    self.collect_fuse_from_dict(nested, f'siteStructure.{key}', candidates, main_fuse_a=main_fuse_a)
                nested_val = self.fuse_limit_from_dict(nested)
                if nested_val > 0 and not self.is_same_as_main_fuse(nested_val, main_fuse_a):
                    if candidates is not None:
                        self.add_fuse_candidate(candidates, nested_val, f'siteStructure.{key}.fuse', main_fuse_a=main_fuse_a)
                    return nested_val, f'siteStructure.{key}.fuse'
        circuits = data.get('circuits')
        if isinstance(circuits, list):
            if candidates is not None:
                self.collect_explicit_circuit_fuses(
                    circuits, 'siteStructure.', candidates, main_fuse_a=main_fuse_a)
            fuse_a, path = self.fuse_limit_from_circuits(circuits, main_fuse_a=main_fuse_a)
            if fuse_a > 0 and not self.is_same_as_main_fuse(fuse_a, main_fuse_a):
                if candidates is not None:
                    self.add_fuse_candidate(candidates, fuse_a, f'siteStructure.{path}', main_fuse_a=main_fuse_a)
                return fuse_a, f'siteStructure.{path}'
        panels = data.get('panels')
        if isinstance(panels, list):
            if candidates is not None:
                for panel in panels:
                    if isinstance(panel, dict):
                        pid = panel.get('id', panel.get('circuitPanelId', ''))
                        self.collect_fuse_from_dict(
                            panel, f'siteStructure.panel[{pid}]', candidates, main_fuse_a=main_fuse_a)
            fuse_a, path = self.fuse_limit_from_circuits(panels, main_fuse_a=main_fuse_a)
            if fuse_a > 0 and not self.is_same_as_main_fuse(fuse_a, main_fuse_a):
                if candidates is not None:
                    self.add_fuse_candidate(candidates, fuse_a, f'siteStructure.{path}', main_fuse_a=main_fuse_a)
                return fuse_a, f'siteStructure.{path}'
        fuse_a, path = self.fuse_limit_from_deep_scan(data, 'siteStructure', main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            if candidates is not None:
                self.add_fuse_candidate(candidates, fuse_a, path, main_fuse_a=main_fuse_a)
            return fuse_a, path
        return 0.0, ''
    def emobility_from_site_structure(self, raw):
        data = self.parse_site_structure_json(raw)
        if not data:
            return 0.0
        direct = self.emobility_from_dict(data)
        if direct > 0:
            return direct
        for key in ('site', 'panel', 'limits', 'loadBalancing', 'energy'):
            nested = data.get(key)
            if isinstance(nested, dict):
                nested_val = self.emobility_from_dict(nested)
                if nested_val > 0:
                    return nested_val
        for _, amps in self.deep_scan_amp_keys(data, self.is_emobility_key):
            if amps > 0:
                return amps
        return 0.0
    def fuse_limit_from_equalizer_values(self, values, main_fuse_a=0.0):
        if not isinstance(values, dict):
            return 0.0, ''
        direct = self.fuse_limit_from_dict(values)
        if direct > 0 and not self.is_same_as_main_fuse(direct, main_fuse_a):
            return direct, 'equalizer.fuse'
        for key in ('config', 'state', 'settings', 'loadBalancing', 'limits'):
            nested = values.get(key)
            if isinstance(nested, dict):
                nested_val = self.fuse_limit_from_dict(nested)
                if nested_val > 0 and not self.is_same_as_main_fuse(nested_val, main_fuse_a):
                    return nested_val, f'equalizer.{key}.fuse'
        fuse_a, path = self.fuse_limit_from_deep_scan(values, 'equalizer', main_fuse_a=main_fuse_a)
        return fuse_a, path
    def fuse_limit_from_products(self, site_id, circuit_id=None, main_fuse_a=0.0):
        products = self.api_get_optional('/accounts/products')
        if not isinstance(products, list):
            return 0.0, ''
        target = str(site_id)
        for product in products:
            if not isinstance(product, dict):
                continue
            pid = product.get('id') or product.get('siteId')
            if pid is None or str(pid) != target:
                continue
            fuse_a = self.fuse_limit_from_dict(product)
            if fuse_a > 0 and not self.is_same_as_main_fuse(fuse_a, main_fuse_a):
                return fuse_a, 'accounts/products.fuse'
            circuits = product.get('circuits')
            fuse_a, path = self.fuse_limit_from_circuits(circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
            if fuse_a > 0:
                return fuse_a, f'accounts/products.{path}'
            equalizers = product.get('equalizers')
            if isinstance(equalizers, list):
                for eq in equalizers:
                    if isinstance(eq, dict):
                        fuse_a = self.fuse_limit_from_dict(eq)
                        if fuse_a > 0 and not self.is_same_as_main_fuse(fuse_a, main_fuse_a):
                            return fuse_a, 'accounts/products.equalizer.fuse'
        return 0.0, ''
    def set_emobility(self, info, amps, source):
        if amps <= 0:
            return
        existing = info.get('emobility_a', 0.0)
        existing_src = str(info.get('emobility_source', ''))
        src_text = str(source)
        if 'site.state.maxAllocatedCurrent' in src_text:
            info['emobility_a'] = amps
            info['emobility_source'] = source
            return
        if 'site.state.maxAllocatedCurrent' in existing_src:
            return
        prefer_new = 'maxAllocatedCurrent' in src_text
        prefer_existing = 'maxAllocatedCurrent' in existing_src
        site_new = src_text.startswith('site.') or 'site.state' in src_text
        site_existing = existing_src.startswith('site.') or 'site.state' in existing_src
        if prefer_new and prefer_existing:
            if site_new:
                info['emobility_a'] = amps
                info['emobility_source'] = source
            elif not site_existing:
                info['emobility_a'] = max(existing, amps)
                info['emobility_source'] = source
            return
        if prefer_new and site_new:
            info['emobility_a'] = amps
            info['emobility_source'] = source
        elif prefer_new:
            info['emobility_a'] = amps
            info['emobility_source'] = source
        elif prefer_existing and site_existing:
            return
        elif existing <= 0 or amps > existing:
            info['emobility_a'] = amps
            info['emobility_source'] = source
    def log_fuse_probe_debug(self, site_id, info, debug_hits, candidates=None, site_structure=None, raw_hits=None, rejected=None):
        if Parameters.get('Mode6') != 'Debug':
            return
        parts = [
            f'site={site_id}',
            f"main={info.get('main_fuse_a', 0)}A",
            f"limit={info.get('main_fuse_limit_a', 0)}A",
            f"src={info.get('main_fuse_limit_source', '—')}",
            f"emob={info.get('emobility_a', 0)}A",
        ]
        if candidates:
            parts.append('candidates=' + '; '.join(
                f'{k}={int(round(v))}A' for k, v in sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:20]
            ))
        if raw_hits:
            parts.append('raw=' + '; '.join(raw_hits[:20]))
        if rejected:
            parts.append('rejected=' + '; '.join(rejected[:16]))
        if debug_hits:
            parts.append('hits=' + '; '.join(debug_hits[:24]))
        if site_structure is not None:
            keys = self.structure_top_keys(site_structure)
            if keys:
                parts.append('siteStructure keys=' + ', '.join(keys))
        self.debug('Fuse probes: ' + ' | '.join(parts))
    def fetch_site_fuse_info(self, site_id, circuit_id=None, site_structure=None, equalizer_values=None, equalizer_id=None):
        if not site_id:
            return {}
        cache_key = f'{site_id}:{circuit_id or ""}'
        if cache_key in self.site_fuse_cache:
            return self.site_fuse_cache[cache_key]
        info = {'emobility_source': '', 'fuse_probes_ran': []}
        probes = info['fuse_probes_ran']
        debug_hits = []
        raw_hits = []
        rejected = []
        candidates = {}
        root_fuse = 0.0
        root_source = ''
        main_fuse_a = 0.0
        all_circuits = []

        def remember_root(rf, rs):
            nonlocal root_fuse, root_source
            if rf > 0 and (root_fuse <= 0 or rf >= root_fuse):
                root_fuse, root_source = rf, rs

        state_path = f'/sites/{site_id}/state'
        probes.append(state_path)
        state = self.api_get_optional(state_path)
        if isinstance(state, dict):
            site = state.get('site') or {}
            if isinstance(site, dict):
                debug_hits.extend(self.collect_fuse_debug(site, 'site.state'))
                main_fuse = self.first_dict_value(site, self.main_fuse_keys())
                if main_fuse is not None:
                    main_fuse_a = self.amp_value(main_fuse)
                    info['main_fuse_a'] = main_fuse_a
                if site.get('fuse') is not None:
                    self.note_raw_fuse_value(raw_hits, site.get('fuse'), 'site.state.fuse')
                    self.add_fuse_candidate(
                        candidates, site.get('fuse'), 'site.state.fuse',
                        main_fuse_a=main_fuse_a, rejected=rejected)
                self.collect_fuse_from_dict(site, 'site.state', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
                self.scan_any_fuse_keys(site, 'site.state', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
                for path, amps in self.deep_scan_amp_keys(site, self.is_main_limit_key):
                    self.add_fuse_candidate(
                        candidates, amps, f'site.state.{path}', main_fuse_a=main_fuse_a, rejected=rejected)
                fuse_limit = self.first_dict_value(site, self.fuse_limit_keys())
                if fuse_limit is not None:
                    self.note_raw_fuse_value(raw_hits, fuse_limit, 'site.state.fuseLimit')
                    self.add_fuse_candidate(
                        candidates, fuse_limit, 'site.state.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
                mac = site.get('maxAllocatedCurrent')
                if mac is not None:
                    self.set_emobility(info, self.amp_value(mac), 'site.state.maxAllocatedCurrent')
                else:
                    emobility = self.first_dict_value(site, ('maxCurrent', 'eMobilityLimit', 'emobilityLimit'))
                    if emobility is not None:
                        self.set_emobility(info, self.amp_value(emobility), 'site.state.emobility')
                site_circuits = site.get('circuits')
                if isinstance(site_circuits, list):
                    all_circuits.extend(site_circuits)
                    debug_hits.extend(self.collect_fuse_debug(site_circuits, 'site.state.circuits'))
                    rf, rs = self.collect_fuse_from_circuits_list(
                        site_circuits, 'site.state.circuits.', candidates, main_fuse_a=main_fuse_a,
                        rejected=rejected, raw_hits=raw_hits)
                    remember_root(rf, f'site.state.circuits.{rs}')
            mac_root = state.get('maxAllocatedCurrent')
            if mac_root is not None:
                self.set_emobility(info, self.amp_value(mac_root), 'site.state.maxAllocatedCurrent')
            circuit_states = state.get('circuitStates')
            debug_hits.extend(self.collect_fuse_debug(circuit_states, 'circuitStates'))
            if isinstance(circuit_states, list):
                circuits = []
                for item in circuit_states:
                    if not isinstance(item, dict):
                        continue
                    circuit = item.get('circuit')
                    if isinstance(circuit, dict):
                        circuits.append(circuit)
                        all_circuits.append(circuit)
                    mac = item.get('maxAllocatedCurrent')
                    if mac is not None:
                        self.set_emobility(info, self.amp_value(mac), 'circuitStates.maxAllocatedCurrent')
                rf, rs = self.collect_fuse_from_circuits_list(
                    circuits, 'circuitStates.', candidates, main_fuse_a=main_fuse_a,
                    rejected=rejected, raw_hits=raw_hits)
                remember_root(rf, f'circuitStates.{rs}')
                if circuit_id is not None:
                    fuse_a, src = self.fuse_limit_from_circuits(
                        circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
                    if fuse_a > 0:
                        self.add_fuse_candidate(
                            candidates, fuse_a, f'circuitStates.{src}',
                            main_fuse_a=main_fuse_a, rejected=rejected)

        if site_structure is not None:
            probes.append('equalizer.observations.siteStructure')
            debug_hits.extend(self.collect_fuse_debug(self.parse_site_structure_json(site_structure), 'siteStructure'))
            self.fuse_limit_from_site_structure(
                site_structure, main_fuse_a=main_fuse_a, candidates=candidates)
            emob = self.emobility_from_site_structure(site_structure)
            if emob > 0:
                self.set_emobility(info, emob, 'siteStructure.maxAllocatedCurrent')
            self.log_site_structure_once(site_id, site_structure, candidates)

        site_path = f'/sites/{site_id}'
        probes.append(site_path)
        site_basic = self.api_get_optional(site_path)
        if isinstance(site_basic, dict):
            debug_hits.extend(self.collect_fuse_debug(site_basic, 'site.basic'))
            if main_fuse_a <= 0:
                main_fuse = self.first_dict_value(site_basic, self.main_fuse_keys())
                if main_fuse is not None:
                    main_fuse_a = self.amp_value(main_fuse)
                    info['main_fuse_a'] = main_fuse_a
            self.collect_fuse_from_dict(site_basic, 'site.basic', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            if isinstance(site_basic.get('circuits'), list):
                all_circuits.extend(site_basic.get('circuits'))
            rf, rs = self.collect_fuse_from_circuits_list(
                site_basic.get('circuits'), 'site.basic.', candidates, main_fuse_a=main_fuse_a,
                rejected=rejected, raw_hits=raw_hits)
            remember_root(rf, f'site.basic.{rs}')

        detailed_path = f'/sites/{site_id}?detailed=true'
        probes.append(detailed_path)
        detailed = self.api_get_optional(detailed_path)
        if isinstance(detailed, dict):
            debug_hits.extend(self.collect_fuse_debug(detailed, 'site.detailed'))
            if main_fuse_a <= 0:
                main_fuse = self.first_dict_value(detailed, self.main_fuse_keys())
                if main_fuse is not None:
                    main_fuse_a = self.amp_value(main_fuse)
                    info['main_fuse_a'] = main_fuse_a
            self.collect_fuse_from_dict(detailed, 'site.detailed', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            fuse_limit = self.first_dict_value(detailed, self.fuse_limit_keys())
            if fuse_limit is not None:
                self.note_raw_fuse_value(raw_hits, fuse_limit, 'site.detailed.fuseLimit')
                self.add_fuse_candidate(
                    candidates, fuse_limit, 'site.detailed.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
            if isinstance(detailed.get('circuits'), list):
                all_circuits.extend(detailed.get('circuits'))
            rf, rs = self.collect_fuse_from_circuits_list(
                detailed.get('circuits'), 'site.detailed.', candidates, main_fuse_a=main_fuse_a,
                rejected=rejected, raw_hits=raw_hits)
            remember_root(rf, f'site.detailed.{rs}')
            fuse_a, src = self.fuse_limit_from_circuits(
                detailed.get('circuits'), circuit_id=circuit_id, main_fuse_a=main_fuse_a)
            if fuse_a > 0:
                self.add_fuse_candidate(
                    candidates, fuse_a, f'site.detailed.{src}', main_fuse_a=main_fuse_a, rejected=rejected)
            mac = detailed.get('maxAllocatedCurrent')
            if mac is not None:
                self.set_emobility(info, self.amp_value(mac), 'site.detailed.maxAllocatedCurrent')
            elif info.get('emobility_a', 0.0) <= 0:
                emobility = self.first_dict_value(detailed, ('maxCurrent', 'eMobilityLimit', 'emobilityLimit'))
                if emobility is not None:
                    self.set_emobility(info, self.amp_value(emobility), 'site.detailed.emobility')

        circuits_path = f'/sites/{site_id}/circuits'
        probes.append(circuits_path)
        circuits = self.api_get_optional(circuits_path)
        debug_hits.extend(self.collect_fuse_debug(circuits, 'circuits'))
        if isinstance(circuits, list):
            all_circuits.extend(circuits)
            rf, rs = self.collect_fuse_from_circuits_list(
                circuits, 'circuits.', candidates, main_fuse_a=main_fuse_a,
                rejected=rejected, raw_hits=raw_hits)
            remember_root(rf, f'circuits.{rs}')
            fuse_a, src = self.fuse_limit_from_circuits(
                circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
            if fuse_a > 0:
                self.add_fuse_candidate(
                    candidates, fuse_a, f'circuits.{src}', main_fuse_a=main_fuse_a, rejected=rejected)

        rf, rs = self.fetch_root_circuit_details(
            site_id, self._unique_circuits(all_circuits), candidates, main_fuse_a=main_fuse_a,
            probes=probes, rejected=rejected, raw_hits=raw_hits)
        remember_root(rf, rs)

        if circuit_id is not None:
            settings_path = f'/sites/{site_id}/circuits/{circuit_id}/settings'
            probes.append(settings_path)
        self.collect_fuse_from_circuit_settings(
            site_id, circuit_id, candidates, main_fuse_a=main_fuse_a, rejected=rejected)

        if circuit_id is not None:
            eq_circuit_path = f'/sites/{site_id}/circuits/{circuit_id}'
            probes.append(eq_circuit_path)
        self.collect_fuse_from_equalizer_circuit(
            site_id, circuit_id, candidates, main_fuse_a=main_fuse_a, rejected=rejected)

        self.collect_fuse_from_cloud_loadbalancing(
            equalizer_id, candidates, main_fuse_a=main_fuse_a, probes=probes)

        probes.append('/accounts/products')
        fuse_a, src = self.fuse_limit_from_products(
            site_id, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            self.add_fuse_candidate(
                candidates, fuse_a, f'accounts/products.{src}', main_fuse_a=main_fuse_a, rejected=rejected)

        if equalizer_values:
            debug_hits.extend(self.collect_fuse_debug(equalizer_values, 'equalizer'))
            self.collect_fuse_from_dict(
                equalizer_values, 'equalizer', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            self.scan_any_fuse_keys(
                equalizer_values, 'equalizer', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            for key in ('config', 'state', 'settings', 'loadBalancing', 'limits'):
                nested = equalizer_values.get(key)
                if isinstance(nested, dict):
                    self.collect_fuse_from_dict(
                        nested, f'equalizer.{key}', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
                    self.scan_any_fuse_keys(
                        nested, f'equalizer.{key}', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            fuse_a, src = self.fuse_limit_from_equalizer_values(
                equalizer_values, main_fuse_a=main_fuse_a)
            if fuse_a > 0:
                self.add_fuse_candidate(
                    candidates, fuse_a, src or 'equalizer.fuse', main_fuse_a=main_fuse_a, rejected=rejected)

        limit_a, limit_src = self.select_main_fuse_limit(
            candidates, main_fuse_a=main_fuse_a,
            root_fuse=root_fuse, root_source=root_source)
        if limit_a > 0:
            info['main_fuse_limit_a'] = limit_a
            info['main_fuse_limit_source'] = limit_src

        info['fuse_raw_hits'] = raw_hits
        info['fuse_rejected'] = rejected
        info['fuse_debug_hits'] = debug_hits

        if equalizer_values:
            mpi = equalizer_values.get('maxPowerImport')
            if mpi is not None:
                power_w = self.kw_to_watts(mpi)
                if power_w > 0:
                    info['max_power_import_kw'] = self.safe_float(mpi, 0.0)
                    if abs(info['max_power_import_kw']) >= 100:
                        info['max_power_import_kw'] /= 1000.0
                    info['max_power_import_w'] = power_w
                    info['max_power_import_a'] = round(self.amps_balanced_3phase_from_power(power_w))

        self.log_fuse_probe_debug(
            site_id, info, debug_hits, candidates=candidates, site_structure=site_structure,
            raw_hits=raw_hits, rejected=rejected)
        self.site_fuse_cache[cache_key] = info
        return info
    def parse_equalizer_observations(self, obs):
        values = {}
        if not isinstance(obs, dict):
            return values
        observations = obs.get('observations') or obs.get('data') or []
        if not isinstance(observations, list):
            return values
        for item in observations:
            if not isinstance(item, dict):
                continue
            obs_id = item.get('id')
            obs_val = item.get('value')
            if obs_id == 31:
                values['currentL1'] = obs_val
            elif obs_id == 32:
                values['currentL2'] = obs_val
            elif obs_id == 33:
                values['currentL3'] = obs_val
            elif obs_id == 40:
                values['activePowerImport'] = obs_val
            elif obs_id == 41:
                values['activePowerExport'] = obs_val
            elif obs_id == 20:
                values['siteStructure'] = obs_val
            elif obs_id == 44:
                values['maxPowerImport'] = obs_val
        return values

    # ---- Tibber API ----
    def tibber_query(self, query):
        token = self.tibber_token()
        if not token:
            return None
        try:
            r = self.session.post(TIBBER_GQL, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json={'query': query}, timeout=20)
            if r.status_code == 200:
                return r.json()
            self.debug(f'tibber query http {r.status_code}: {r.text[:300]}')
        except Exception as e:
            self.debug(f'tibber query failed: {e}')
        return None
    def refresh_tibber_prices(self):
        if not self.tibber_enabled():
            self.state['price_cache'] = {}
            self.state['currency'] = 'EUR'
            return
        query = '{ viewer { homes { id currentSubscription { priceInfo { current { total energy tax currency startsAt } today { total energy tax startsAt } tomorrow { total energy tax startsAt } } } } } }'
        result = self.tibber_query(query)
        if not result:
            return
        try:
            homes = (((result or {}).get('data') or {}).get('viewer') or {}).get('homes') or []
            if not homes:
                return
            info = ((((homes[0] or {}).get('currentSubscription') or {}).get('priceInfo')) or {})
            cache = {}
            curr = info.get('current') or {}
            if curr.get('currency'):
                self.state['currency'] = str(curr.get('currency'))
            for bucket_name in ('today','tomorrow'):
                for node in (info.get(bucket_name) or []):
                    start = node.get('startsAt')
                    total = node.get('total')
                    if start and total is not None:
                        cache[str(start)] = {'total': self.safe_float(total,0.0), 'energy': self.safe_float(node.get('energy'),0.0), 'tax': self.safe_float(node.get('tax'),0.0)}
            if curr.get('startsAt') and curr.get('total') is not None:
                cache[str(curr.get('startsAt'))] = {'total': self.safe_float(curr.get('total'),0.0), 'energy': self.safe_float(curr.get('energy'),0.0), 'tax': self.safe_float(curr.get('tax'),0.0)}
            self.state['price_cache'] = cache
            self.state['price_cache_refreshed'] = int(self.now_ts())
        except Exception as e:
            self.debug(f'parse tibber prices failed: {e}')
    def current_tibber_price(self):
        cache = self.state.get('price_cache') or {}
        if not cache:
            return {'total':0.0,'energy':0.0,'tax':0.0,'currency': self.state.get('currency','EUR')}
        now = datetime.now().astimezone()
        best = None
        best_delta = None
        best_start = None
        for start_s, data in cache.items():
            dt = self.parse_iso(start_s)
            if dt is None:
                continue
            delta = (now - dt).total_seconds()
            if delta >= 0 and (best_delta is None or delta < best_delta):
                best_delta = delta
                best = data
                best_start = start_s
        if best is None:
            for start_s, data in cache.items():
                dt = self.parse_iso(start_s)
                if dt is None:
                    continue
                delta = abs((dt - now).total_seconds())
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best = data
                    best_start = start_s
        out = dict(best or {})
        out['currency'] = self.state.get('currency','EUR')
        out['startsAt'] = best_start
        return out
    def price_status_emoji(self):
        cache = self.state.get('price_cache') or {}
        current = self.current_tibber_price()
        cur = self.safe_float(current.get('total'), 0.0)
        return self.price_emoji(cur, cache)
    def cheapest_window_text(self, hours=3):
        cache = self.state.get('price_cache') or {}
        points = []
        for start_s, data in cache.items():
            dt = self.parse_iso(start_s)
            if dt is None:
                continue
            points.append((dt, self.safe_float(data.get('total'),0.0)))
        points.sort(key=lambda x: x[0])
        if len(points) < hours:
            return 'Onvoldoende prijsdata'
        best_idx = None
        best_avg = None
        for i in range(0, len(points)-hours+1):
            avg = sum(p[1] for p in points[i:i+hours]) / float(hours)
            if best_avg is None or avg < best_avg:
                best_avg = avg
                best_idx = i
        if best_idx is None:
            return 'Onvoldoende prijsdata'
        start = points[best_idx][0]
        end = points[best_idx+hours-1][0]
        return f'{start.strftime("%H:%M")} - {end.strftime("%H:%M")} | €{best_avg:.2f}/kWh'

    # ---- charger state ----
    def charger_state(self, cid):
        store = self.state.setdefault('chargers', {})
        st = store.setdefault(cid, {
            'prev_total_kwh': None,
            'prev_session_kwh': None,
            'session_active': False,
            'session_start_ts': None,
            'session_start_kwh': None,
            'session_cost_total': 0.0,
            'session_cost_energy': 0.0,
            'session_cost_tax': 0.0,
            'last_session_kwh': 0.0,
            'last_session_cost_total': 0.0,
            'last_session_cost_energy': 0.0,
            'last_session_cost_tax': 0.0,
            'last_session_duration': '00:00',
            'day_key': self.today_key(),
            'day_cost_total': 0.0,
            'day_cost_energy': 0.0,
            'day_cost_tax': 0.0,
        })
        if st.get('day_key') != self.today_key():
            st['day_key'] = self.today_key()
            st['day_cost_total'] = 0.0
            st['day_cost_energy'] = 0.0
            st['day_cost_tax'] = 0.0
        return st
    def compute_duration_text(self, start_ts):
        if not start_ts:
            return '00:00'
        secs = max(0, int(self.now_ts() - float(start_ts)))
        return f'{secs // 3600:02d}:{(secs % 3600) // 60:02d}'

    # ---- discovery ----
    def _equalizer_matches_filter(self, name, site_name):
        flt = Parameters.get('Mode5', '').strip().lower()
        if not flt:
            return True
        return flt in str(name).lower() or flt in str(site_name).lower()

    def _append_equalizer(self, equalizers, seen, eq, ignore_filter=False):
        eid = str(eq.get('id') or '').strip()
        if not eid or eid in seen:
            return False
        if not ignore_filter and not self._equalizer_matches_filter(eq.get('name', ''), eq.get('siteName', '')):
            return False
        equalizers.append(eq)
        seen.add(eid)
        return True

    def _scan_equalizers_in_object(self, obj, found, site_name=''):
        if isinstance(obj, dict):
            marker = ' '.join([
                str(obj.get('name', '')),
                str(obj.get('type', '')),
                str(obj.get('role', '')),
                str(obj.get('deviceType', '')),
                str(obj.get('category', '')),
                str(obj.get('meterType', '')),
            ]).lower()
            eid = obj.get('id') or obj.get('equalizerId') or obj.get('serialNumber')
            is_meter = (
                obj.get('deviceType') in ['HAN', 'P1', 'Equalizer']
                or str(obj.get('role', '')).lower() in ['meter', 'han', 'equalizer']
                or any(x in marker for x in ['equalizer', 'meter', 'han', 'p1', 'energy'])
            )
            site = str(obj.get('siteName') or obj.get('locationName') or obj.get('siteId') or site_name or '')
            if eid and is_meter:
                found[str(eid).strip()] = {
                    'id': str(eid).strip(),
                    'name': str(obj.get('name') or obj.get('serialNumber') or obj.get('id') or 'Equalizer'),
                    'siteName': site,
                    'circuitId': obj.get('circuitId'),
                    'circuitName': obj.get('circuitName') or obj.get('name'),
                    'source': 'sites-scan',
                }
            for value in obj.values():
                self._scan_equalizers_in_object(value, found, site_name=site or site_name)
        elif isinstance(obj, list):
            for item in obj:
                self._scan_equalizers_in_object(item, found, site_name=site_name)

    def _ingest_equalizer_items(self, equalizers, seen, items, source, site_name='', site_id=None, ignore_filter=False):
        added = 0
        if not isinstance(items, list):
            return added
        for item in items:
            if not isinstance(item, dict):
                continue
            eq_id = item.get('id') or item.get('equalizerId') or item.get('serialNumber')
            if not eq_id:
                continue
            eq = {
                'id': str(eq_id).strip(),
                'name': str(item.get('name') or item.get('serialNumber') or eq_id),
                'siteId': site_id if site_id is not None else item.get('siteId'),
                'siteName': str(site_name or item.get('siteName') or item.get('locationName') or ''),
                'circuitId': item.get('circuitId'),
                'circuitName': str(item.get('circuitName') or item.get('name') or ''),
                'source': source,
            }
            if self._append_equalizer(equalizers, seen, eq, ignore_filter=ignore_filter):
                added += 1
        return added

    def discover_equalizers(self):
        equalizers = []
        seen = set()
        sources = []
        probes = {}

        products = self.api_get_optional('/accounts/products')
        if isinstance(products, list):
            probes['accounts_products'] = len(products)
            for product in products:
                if not isinstance(product, dict):
                    continue
                site_id = product.get('id')
                site_name = str(product.get('name') or product.get('siteName') or site_id or 'Site')
                added = self._ingest_equalizer_items(
                    equalizers, seen, product.get('equalizers'), 'accounts-products',
                    site_name=site_name, site_id=site_id,
                )
                if added:
                    sources.append('accounts-products')
        else:
            probes['accounts_products'] = 'leeg of niet beschikbaar'

        sites = self.api_get_optional('/sites')
        if isinstance(sites, list):
            probes['sites'] = len(sites)
            for site in sites:
                if not isinstance(site, dict):
                    continue
                site_id = site.get('id')
                site_name = str(site.get('name') or site.get('siteName') or site_id or 'Site')
                added = self._ingest_equalizer_items(
                    equalizers, seen, site.get('equalizers'), 'sites-list',
                    site_name=site_name, site_id=site_id,
                )
                if added:
                    sources.append('sites-list')
                if site_id:
                    detailed = self.api_get_optional(f'/sites/{site_id}?detailed=true')
                    if isinstance(detailed, dict):
                        added = self._ingest_equalizer_items(
                            equalizers, seen, detailed.get('equalizers'), 'sites-detailed',
                            site_name=site_name, site_id=site_id,
                        )
                        if added:
                            sources.append('sites-detailed')
                    circuits = self.api_get_optional(f'/sites/{site_id}/circuits')
                    if isinstance(circuits, list):
                        probes[f'circuits_{site_id}'] = len(circuits)
                        for circuit in circuits:
                            if not isinstance(circuit, dict):
                                continue
                            eq_id = circuit.get('equalizerId') or circuit.get('equalizer') or circuit.get('equalizer_id')
                            if not eq_id:
                                continue
                            eq = {
                                'id': str(eq_id).strip(),
                                'name': str(circuit.get('name') or circuit.get('id') or 'Equalizer'),
                                'siteId': site_id,
                                'siteName': site_name,
                                'circuitId': circuit.get('id'),
                                'circuitName': str(circuit.get('name') or circuit.get('id') or 'Circuit'),
                                'source': 'sites-circuits',
                            }
                            if self._append_equalizer(equalizers, seen, eq):
                                sources.append('sites-circuits')
        else:
            probes['sites'] = 'leeg of niet beschikbaar'

        list_data = self.api_get_optional('/equalizers')
        if isinstance(list_data, list):
            probes['equalizers_list'] = len(list_data)
            added = self._ingest_equalizer_items(equalizers, seen, list_data, 'equalizers-list')
            if added:
                sources.append('equalizers-list')
        else:
            probes['equalizers_list'] = 'leeg of niet beschikbaar'

        if not equalizers and isinstance(sites, list):
            found = {}
            self._scan_equalizers_in_object(sites, found)
            for eq in found.values():
                if self._append_equalizer(equalizers, seen, eq):
                    sources.append('sites-scan')

        manual_id = self.manual_equalizer_id()
        if manual_id and manual_id not in seen:
            eq = {
                'id': manual_id,
                'name': self.custom_equalizer_name() or 'Equalizer',
                'siteName': '',
                'source': 'manual-id',
            }
            if self._append_equalizer(equalizers, seen, eq, ignore_filter=True):
                sources.append('manual-id')

        self.equalizer_probes = probes
        self.equalizer_source = ','.join(dict.fromkeys(sources)) if sources else 'none'
        equalizers = sorted({e['id']: e for e in equalizers}.values(), key=lambda x: x['id'])
        self.debug(f'Equalizer probes: {probes}')
        self.debug(f'Equalizer discovery: {len(equalizers)} via {self.equalizer_source}')
        return equalizers

    def discover_chargers(self):
        chargers = []
        flt = Parameters.get('Mode5', '').strip().lower()
        try:
            data = self.api_get('/chargers') or []
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    cid = item.get('id') or item.get('chargerId') or item.get('serialNumber')
                    name = str(item.get('name') or item.get('serialNumber') or item.get('id') or 'Lader')
                    site = str(item.get('siteName') or item.get('locationName') or item.get('siteId') or '')
                    if cid and (not flt or flt in name.lower() or flt in site.lower()):
                        chargers.append({'id': str(cid).strip(), 'name': name, 'siteName': site})
        except Exception as e:
            self.error(f'Discovery chargers mislukt: {e}')
        return sorted({c['id']: c for c in chargers}.values(), key=lambda x: x['id'])

    def discover_entities(self):
        self.chargers = self.discover_chargers()
        self.equalizers = self.discover_equalizers()
        return self.chargers, self.equalizers

    # ---- lifecycle sync ----
    def ensure_core_devices(self):
        core = [
            ('Status', 'Text'),
            ('Totaal Laden', 'Energy'),
            ('Totaal kWh', 'CustomkWh'),
            ('LoadBal', 'Switch'),
        ]
        if self.tibber_enabled():
            core.extend([
                ('Kosten & Samenvatting', 'Text'),
                ('Beste laden', 'Text'),
            ])
        for label, typ in core:
            devid = CORE_DEVICE_IDS.get(label)
            legacy = [self.pref(label), f'Easee - {label}', f'Easee - Easee - {label}']
            self.ensure_device_once(label, typ, device_id=devid, legacy_names=legacy)
        if ULTRA_DEBUG:
            self.ensure_device_once(self.pref('Debug'),'Text')
            self.ensure_device_once(self.pref('Counts'),'Text')
            if self.tibber_enabled():
                self.ensure_device_once(self.pref('Tibber prijs'),'Text')
    
    def ensure_charger_devices(self, charger, index):
        display = self.charger_display_name(charger, index)
        cid = charger['id']
        devices = [
            ('Energy', 'Laden'),
            ('CustomkWh', 'Totaal & Sessie'),
            ('Text', 'Status'),
        ]
        if self.tibber_enabled():
            devices.append(('Text', 'Kosten (Sessie/Dag)'))
        for typ, label_key in devices:
            name = self.charger_dev_name(display, label_key)
            devid = self.make_charger_device_id(cid, label_key)
            legacy = [
                self.pref(f'{display} - {label_key}'),
                f'Easee - {display} - {label_key}',
                f'Easee - Easee - {display} - {label_key}',
                f'{self.short_id(cid)} {label_key}',
            ]
            self.ensure_device_once(name, typ, device_id=devid, legacy_names=legacy)

    def ensure_equalizer_devices(self, equalizer, index):
        display = self.equalizer_display_name(equalizer, index)
        eid = equalizer['id']
        devices = [
            ('Text', 'Status'),
            ('Energy', 'Vermogen'),
        ]
        for typ, label_key in devices:
            name = self.equalizer_dev_name(display, label_key)
            devid = self.make_equalizer_device_id(eid, label_key)
            legacy = [
                self.pref(f'{display} - {label_key}'),
                f'Easee - {display} - {label_key}',
                f'Easee - Easee - {display} - {label_key}',
            ]
            self.ensure_device_once(name, typ, device_id=devid, legacy_names=legacy)

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
    
    def poll_charger(self, charger):
        cid = charger['id']
        values = {}
        session = {}
        try:
            state = self.api_get(f'/chargers/{cid}/state') or {}
            if isinstance(state, dict):
                values.update(state)
        except Exception as e:
            self.error(f'State ophalen mislukt voor lader {cid}: {e}')
        try:
            cfg = self.api_get(f'/chargers/{cid}/config') or {}
            if isinstance(cfg, dict):
                values.update(cfg)
        except Exception:
            pass
        try:
            sess = self.api_get(f'/chargers/{cid}/sessions/ongoing') or {}
            if isinstance(sess, dict):
                session = sess
        except Exception:
            pass

        power_w = self.power_watts(values.get('totalPower'))
        total_kwh = self.kwh_value(values.get('lifetimeEnergy'))
        total_wh = self.wh_from_kwh(total_kwh)
        online = values.get('isOnline')
        op_mode = values.get('chargerOpMode')
        status_label = self.op_mode_label(op_mode)
        session_status = session.get('status') or session.get('state') or ''
        if session_status and not str(session_status).strip().isdigit():
            status_label = str(session_status)
        session_active = bool(session) or power_w > 50
        api_session_kwh = self.session_energy_kwh(values, session)

        st = self.charger_state(cid)
        prev_total = st.get('prev_total_kwh')

        if session_active and not st.get('session_active'):
            st['session_active'] = True
            st['session_start_ts'] = self.now_ts()
            st['session_start_kwh'] = total_kwh
            st['prev_session_kwh'] = api_session_kwh if api_session_kwh is not None else None
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0

        ending_session = (not session_active) and st.get('session_active')

        delta_kwh = 0.0
        if session_active and api_session_kwh is not None:
            prev_session = st.get('prev_session_kwh')
            if prev_session is not None:
                delta_kwh = max(0.0, float(api_session_kwh) - float(prev_session))
            st['prev_session_kwh'] = api_session_kwh
        elif prev_total is not None:
            delta_kwh = max(0.0, float(total_kwh) - float(prev_total))
        if delta_kwh <= 0 and session_active and power_w > 50 and api_session_kwh is None:
            delta_kwh = self.power_integrated_kwh(power_w)

        if self.tibber_enabled() and delta_kwh > 0:
            price = self.current_tibber_price()
            p_total = self.safe_float(price.get('total'), 0.0)
            p_energy = self.safe_float(price.get('energy'), 0.0)
            p_tax = self.safe_float(price.get('tax'), 0.0)
            add_total = delta_kwh * p_total
            add_energy = delta_kwh * p_energy
            add_tax = delta_kwh * p_tax
            st['day_cost_total'] = round(self.safe_float(st.get('day_cost_total', 0.0), 0.0) + add_total, 4)
            st['day_cost_energy'] = round(self.safe_float(st.get('day_cost_energy', 0.0), 0.0) + add_energy, 4)
            st['day_cost_tax'] = round(self.safe_float(st.get('day_cost_tax', 0.0), 0.0) + add_tax, 4)
            if st.get('session_active'):
                st['session_cost_total'] = round(self.safe_float(st.get('session_cost_total', 0.0), 0.0) + add_total, 4)
                st['session_cost_energy'] = round(self.safe_float(st.get('session_cost_energy', 0.0), 0.0) + add_energy, 4)
                st['session_cost_tax'] = round(self.safe_float(st.get('session_cost_tax', 0.0), 0.0) + add_tax, 4)

        if ending_session:
            if api_session_kwh is not None:
                st['last_session_kwh'] = api_session_kwh
            elif st.get('session_start_kwh') is not None:
                st['last_session_kwh'] = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
            st['last_session_cost_total'] = self.safe_float(st.get('session_cost_total', 0.0), 0.0)
            st['last_session_cost_energy'] = self.safe_float(st.get('session_cost_energy', 0.0), 0.0)
            st['last_session_cost_tax'] = self.safe_float(st.get('session_cost_tax', 0.0), 0.0)
            st['last_session_duration'] = self.compute_duration_text(st.get('session_start_ts'))
            st['session_active'] = False
            st['session_start_ts'] = None
            st['session_start_kwh'] = None
            st['prev_session_kwh'] = None

        if st.get('session_active'):
            if api_session_kwh is not None:
                session_kwh = api_session_kwh
            elif st.get('session_start_kwh') is not None:
                session_kwh = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
            else:
                session_kwh = 0.0
            laadduur = self.compute_duration_text(st.get('session_start_ts'))
            session_cost = self.safe_float(st.get('session_cost_total', 0.0), 0.0)
            session_cost_energy = self.safe_float(st.get('session_cost_energy', 0.0), 0.0)
            session_cost_tax = self.safe_float(st.get('session_cost_tax', 0.0), 0.0)
        else:
            session_kwh = self.safe_float(st.get('last_session_kwh', 0.0), 0.0)
            laadduur = st.get('last_session_duration', '00:00')
            session_cost = self.safe_float(st.get('last_session_cost_total', 0.0), 0.0)
            session_cost_energy = self.safe_float(st.get('last_session_cost_energy', 0.0), 0.0)
            session_cost_tax = self.safe_float(st.get('last_session_cost_tax', 0.0), 0.0)

        st['prev_total_kwh'] = total_kwh

        # UPDATE DEVICES
        self.update_charger_energy(cid, 'Laden', power_w, total_wh)
        
        totaal_sessie = f'{int(round(total_kwh))} kWh | Sessie: {int(round(session_kwh))} kWh'
        self.update_charger_custom(cid, 'Totaal & Sessie', totaal_sessie)
        
        power_emoji = self.power_emoji(power_w)
        status_emoji = self.status_emoji(online, session_active)
        status_text = f'{status_emoji} {power_emoji} {status_label} | ⏱️ {laadduur}'
        self.update_charger_text(cid, 'Status', status_text)
        
        if self.tibber_enabled():
            day_cost = self.safe_float(st.get('day_cost_total', 0.0), 0.0)
            self.update_charger_costs(cid, session_cost, day_cost, session_kwh, bool(st.get('session_active')))
        
        self.latest_chargers[cid] = {
            'power': power_w,
            'kwh': total_kwh,
            'wh': total_wh,
            'day_cost': self.safe_float(st.get('day_cost_total', 0.0), 0.0),
            'day_energy_cost': self.safe_float(st.get('day_cost_energy', 0.0), 0.0),
            'day_tax_cost': self.safe_float(st.get('day_cost_tax', 0.0), 0.0),
            'online': online,
        }

    def poll_equalizer(self, equalizer):
        eid = equalizer['id']
        site_id = equalizer.get('siteId')
        values = {}
        for path in (f'/equalizers/{eid}', f'/equalizers/{eid}/state', f'/equalizers/{eid}/config'):
            data = self.api_get_optional(path)
            if isinstance(data, dict):
                values.update(data)
                if not site_id:
                    site_id = data.get('siteId')

        obs = self.api_get_optional(f'/state/{eid}/observations?ids=20,31,32,33,40,41,44')
        values.update(self.parse_equalizer_observations(obs))

        site_info = self.fetch_site_fuse_info(
            site_id,
            circuit_id=equalizer.get('circuitId'),
            site_structure=values.get('siteStructure'),
            equalizer_values=values,
            equalizer_id=eid,
        )

        power_w = self.kw_to_watts(
            values.get('currentPower')
            or values.get('power')
            or values.get('activePowerImport')
            or values.get('activePower')
        )
        if power_w <= 0:
            power_w = self.power_watts(values.get('currentPower') or values.get('power') or values.get('activePower'))

        online = values.get('isOnline')
        if online is None:
            online = True
        load_bal = (
            values.get('loadBalancingActive')
            or values.get('loadBalancing')
            or values.get('isLoadBalancingEnabled')
        )
        lb_active = self.truthy(load_bal) if load_bal is not None else False
        max_alloc = self.safe_float(site_info.get('emobility_a'), 0.0)
        emob_src = str(site_info.get('emobility_source', ''))
        site_emob_authoritative = (
            'site.state.maxAllocatedCurrent' in emob_src
            or emob_src.startswith('site.')
        )
        if max_alloc <= 0 or not site_emob_authoritative:
            eq_mac = self.safe_float(values.get('maxAllocatedCurrent'), 0.0)
            if eq_mac > 0 and not site_emob_authoritative:
                max_alloc = eq_mac if max_alloc <= 0 else max(max_alloc, eq_mac)
            elif max_alloc <= 0:
                max_alloc = self.safe_float(values.get('allocatedCurrent'), 0.0)
        main_fuse_a = self.safe_float(site_info.get('main_fuse_a'), 0.0)
        main_fuse_limit_a = self.safe_float(site_info.get('main_fuse_limit_a'), 0.0)
        limit_src = str(site_info.get('main_fuse_limit_source', ''))

        self.log_equalizer_fuse_once(
            eid, main_fuse_limit_a, limit_src,
            probes=site_info.get('fuse_probes_ran'),
            debug_hits=site_info.get('fuse_debug_hits'),
            raw_hits=site_info.get('fuse_raw_hits'),
            rejected=site_info.get('fuse_rejected'),
        )

        status_emoji = '✅' if online else '❌'
        lb_emoji = '⚖️' if lb_active else '⏸️'
        lb_text = 'Aan' if lb_active else 'Uit'
        lines = [
            f'{status_emoji} Equalizer online' if online else f'{status_emoji} Equalizer offline',
            f'{lb_emoji} Load balancing: {lb_text}',
        ]
        if max_alloc > 0:
            lines.append(f'🔌 eMobility limiet: {self.format_amp(max_alloc)}')
        else:
            lines.append('🔌 eMobility limiet: onbekend')
        if main_fuse_a > 0:
            lines.append(f'🏠 Hoofdzekering: {self.format_amp(main_fuse_a)}')
        else:
            lines.append('🏠 Hoofdzekering: onbekend')
        if main_fuse_limit_a > 0:
            lines.append(f'⚡ Hoofdzekering limiet: {self.format_amp(main_fuse_limit_a)}')
        else:
            lines.append('⚡ Hoofdzekering limiet: onbekend')
        max_import_kw = self.safe_float(site_info.get('max_power_import_kw'), 0.0)
        max_import_a = self.safe_float(site_info.get('max_power_import_a'), 0.0)
        if max_import_kw <= 0 and values.get('maxPowerImport') is not None:
            raw_kw = self.safe_float(values.get('maxPowerImport'), 0.0)
            if raw_kw > 0:
                max_import_kw = raw_kw / 1000.0 if raw_kw >= 100 else raw_kw
                power_w_mpi = self.kw_to_watts(raw_kw)
                max_import_a = round(self.amps_balanced_3phase_from_power(power_w_mpi))
        if max_import_kw > 0:
            kw_text = self.format_kw(max_import_kw) or f'{max_import_kw:.1f} kW'
            amp_hint = f' (~{int(max_import_a)} A)' if max_import_a > 0 else ''
            lines.append(f'📈 Max import: {kw_text}{amp_hint}')
        current_line, _load_a = self.actual_current_line(values, power_w)
        if current_line:
            lines.append(current_line)
        if power_w > 0:
            lines.append(f'🔥 Huisvermogen: {int(power_w)} W')
        status_text = '\n'.join(lines)

        self.update_equalizer_energy(eid, 'Vermogen', power_w, 0)
        self.update_equalizer_text(eid, 'Status', status_text)

        self.latest_equalizers[eid] = {
            'power': power_w,
            'online': online,
            'loadbal': lb_active,
        }

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
