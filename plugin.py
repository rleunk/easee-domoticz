"""
<plugin key="EaseeCloudAutoDiscoveryV1000" name="Easee AutoDiscovery Compact v10.2.1" author="Richard Leunk" version="10.2.1"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://developer.easee.com/docs/integrations">
    <description>
        <h2>Easee AutoDiscovery Compact v10.2.1</h2><br/>
        <p>Stabiele Easee laadpaal integratie met compacte UI, emoji indicators, Tibber stroomtarief integratie en Equalizer (stap 1).</p>
    </description>
    <params>
        <param field="Username" label="Easee Username / telefoonnummer" width="260px" required="true"/>
        <param field="Password" label="Easee Password" width="260px" password="true" required="true"/>
        <group label="Weergave en polling">
            <param field="Mode1" label="Poll interval (sec)" width="80px" default="30"/>
            <param field="Mode4" label="Niet gebruikt (hardwarenaam telt)" width="180px" default="Easee"/>
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
import os, json, time, hashlib
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
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))

    # ---- logging ----
    def log(self, msg): Domoticz.Log(f'[Easee v10.2.1] {msg}')
    def debug(self, msg):
        if Parameters.get('Mode6') == 'Debug':
            Domoticz.Debug(f'[Easee v10.2.1] {msg}')
    def error(self, msg): Domoticz.Error(f'[Easee v10.2.1] {msg}')

    # ---- helpers ----
    def norm(self, value):
        return ' '.join(str(value).strip().split())
    def prefix(self):
        return Parameters.get('Mode4', 'Easee').strip() or 'Easee'
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
    def short_id(self, full_id):
        s = str(full_id).strip()
        return s[-8:] if len(s) > 8 else s
    def custom_charger_name(self, index):
        if index == 0:
            return self.clean_label(Parameters.get('Mode2', '') or '')
        if index == 1:
            return self.clean_label(Parameters.get('Mode3', '') or '')
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
    def load_custom_images(self):
        roots = ['EaseeCharger','EaseeEqualizer','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
        candidates = ['Easee_v10_0_icons.zip','Easee_v9_0_icons.zip','Easee_v8_0_3_icons.zip','Easee_v8_0_2_icons.zip','Easee_v8_0_1_icons.zip','Easee_v8_icons.zip','Easee.zip']
        for fn in candidates:
            if not os.path.isfile(os.path.join(self.plugin_dir, fn)):
                continue
            try:
                if any(r not in Images for r in roots):
                    try:
                        Domoticz.Image(fn).Create()
                    except Exception:
                        pass
                for r in roots:
                    if r in Images:
                        self.image_ids[r] = Images[r].ID
                if self.image_ids:
                    break
            except Exception:
                pass

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
            devices.append(('CustomEUR', 'Kosten (Sessie/Dag)'))
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
        self.discover_entities()
        self.charger_names = {c['id']: self.charger_display_name(c, i) for i, c in enumerate(self.chargers)}
        self.equalizer_names = {e['id']: self.equalizer_display_name(e, i) for i, e in enumerate(self.equalizers)}
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

        st = self.charger_state(cid)
        prev_total = st.get('prev_total_kwh')
        delta_kwh = 0.0
        if prev_total is not None:
            delta_kwh = max(0.0, float(total_kwh) - float(prev_total))

        if session_active and not st.get('session_active'):
            st['session_active'] = True
            st['session_start_ts'] = self.now_ts()
            st['session_start_kwh'] = total_kwh
            st['session_cost_total'] = 0.0
            st['session_cost_energy'] = 0.0
            st['session_cost_tax'] = 0.0
        elif (not session_active) and st.get('session_active'):
            if st.get('session_start_kwh') is not None:
                st['last_session_kwh'] = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
            st['last_session_cost_total'] = self.safe_float(st.get('session_cost_total', 0.0), 0.0)
            st['last_session_cost_energy'] = self.safe_float(st.get('session_cost_energy', 0.0), 0.0)
            st['last_session_cost_tax'] = self.safe_float(st.get('session_cost_tax', 0.0), 0.0)
            st['last_session_duration'] = self.compute_duration_text(st.get('session_start_ts'))
            st['session_active'] = False
            st['session_start_ts'] = None
            st['session_start_kwh'] = None

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

        if st.get('session_active') and st.get('session_start_kwh') is not None:
            session_kwh = max(0.0, float(total_kwh) - float(st.get('session_start_kwh')))
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
            rate = session_cost / session_kwh if session_kwh > 0 else 0.0
            price_emoji = self.price_emoji(rate, self.state.get('price_cache', {}))
            day_cost = self.safe_float(st.get('day_cost_total', 0.0), 0.0)
            costs_text = f'{price_emoji} Sessie: €{self.euro_str(session_cost)} | Dag: €{self.euro_str(day_cost)}'
            self.update_charger_custom(cid, 'Kosten (Sessie/Dag)', costs_text)
        
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
        values = {}
        for path in (f'/equalizers/{eid}', f'/equalizers/{eid}/state', f'/equalizers/{eid}/config'):
            data = self.api_get_optional(path)
            if isinstance(data, dict):
                values.update(data)

        obs = self.api_get_optional(f'/state/{eid}/observations?ids=40,41,42,43,44')
        if isinstance(obs, dict):
            observations = obs.get('observations') or obs.get('data') or []
            if isinstance(observations, list):
                for item in observations:
                    if not isinstance(item, dict):
                        continue
                    obs_id = item.get('id')
                    obs_val = item.get('value')
                    if obs_id == 40:
                        values['activePowerImport'] = obs_val
                    elif obs_id == 41:
                        values['activePowerExport'] = obs_val

        power_w = self.power_watts(
            values.get('currentPower')
            or values.get('power')
            or values.get('activePowerImport')
            or values.get('activePower')
        )
        online = values.get('isOnline')
        if online is None:
            online = True
        load_bal = (
            values.get('loadBalancingActive')
            or values.get('loadBalancing')
            or values.get('isLoadBalancingEnabled')
        )
        lb_active = self.truthy(load_bal) if load_bal is not None else False
        max_alloc = self.safe_float(values.get('maxAllocatedCurrent') or values.get('allocatedCurrent'), 0.0)

        power_emoji = self.power_emoji(power_w)
        status_emoji = '✅' if online else '❌'
        lb_text = 'Aan' if lb_active else 'Uit'
        status_text = f'{status_emoji} {power_emoji} LB {lb_text}'
        if max_alloc > 0:
            status_text += f' | Max {max_alloc:.0f} A'

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
            rate = (total_day_cost / total_kwh) if total_kwh > 0 else 0.0
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
