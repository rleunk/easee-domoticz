"""
<plugin key="EaseeCloudAutoDiscoveryV900" name="Easee AutoDiscovery Compact v9.0" author="Rleunk & Copilot" version="9.0"
        wikilink="https://wiki.domoticz.com/Developing_a_Python_plugin"
        externallink="https://developer.easee.com/docs/integrations">
    <description>
        <h2>Easee AutoDiscovery Compact v9.0</h2><br/>
        <p>Complete Easee laadpaal integratie met compacte UI, intelligente emoji indicators en Tibber stroomtarief integratie.</p>
    </description>
    <params>
        <param field="Username" label="Easee Username / telefoonnummer" width="260px" required="true"/>
        <param field="Password" label="Easee Password" width="260px" password="true" required="true"/>
        <group label="Weergave en polling">
            <param field="Mode1" label="Poll interval (sec)" width="80px" default="30"/>
            <param field="Mode4" label="Naam prefix (kern-devices)" width="180px" default="Easee"/>
            <param field="Mode5" label="Optionele site filter (tekst)" width="240px" default=""/>
            <param field="Mode6" label="Debug logging" width="100px">
                <options>
                    <option label="Normaal" value="Normal" default="true"/>
                    <option label="Debug" value="Debug"/>
                </options>
            </param>
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

DEVICE_TYPES = {
    'Text':      {'Type': 243, 'Subtype': 19},
    'Switch':    {'Type': 244, 'Subtype': 73, 'Switchtype': 0},
    'Energy':    {'Type': 243, 'Subtype': 29},
    'CustomkWh': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;kWh'}},
    'CustomEUR': {'Type': 243, 'Subtype': 31, 'Options': {'Custom': '1;€'}},
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
        self.latest_chargers = {}
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))

    # ---- logging ----
    def log(self, msg): Domoticz.Log(f'[Easee v9.0] {msg}')
    def debug(self, msg):
        if Parameters.get('Mode6') == 'Debug':
            Domoticz.Debug(f'[Easee v9.0] {msg}')
    def error(self, msg): Domoticz.Error(f'[Easee v9.0] {msg}')

    # ---- helpers ----
    def norm(self, value):
        return ' '.join(str(value).strip().split())
    def prefix(self):
        return Parameters.get('Mode4', 'Easee').strip() or 'Easee'
    def pref(self, label):
        return f'{self.prefix()} - {label}'
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
    def charger_label(self, charger):
        return self.short_id(charger['id'])
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
    def next_free_unit(self):
        for unit in range(1, 256):
            if unit not in Devices:
                return unit
        self.error('Geen vrije Unit meer beschikbaar (1-255)')
        return None

    # ---- images ----
    def image_root(self, name):
        n = name.lower()
        if 'overzicht' in n:
            return 'EaseeOverview'
        if 'kosten' in n or 'goedkoop' in n or '€' in n or 'sessie' in n:
            return 'EaseeCost'
        if 'status' in n or 'online' in n or 'tijd' in n:
            return 'EaseeStatus'
        if 'loadbal' in n:
            return 'EaseeLoadBal'
        if 'laden' in n or 'totaal' in n or 'w' in n or 'kwh' in n or 'energy' in n:
            return 'EaseePower'
        return 'EaseeCharger'
    def load_custom_images(self):
        roots = ['EaseeCharger','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
        candidates = ['Easee_v9_0_icons.zip','Easee_v8_0_3_icons.zip','Easee_v8_0_2_icons.zip','Easee_v8_0_1_icons.zip','Easee_v8_icons.zip','Easee.zip']
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
    def ensure_device_once(self, name, typename):
        key = self.norm(name)
        devid = self.make_device_id(key)
        unit = self.find_unit_by_devid(devid) or self.find_unit(key)
        if unit is not None:
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
    def discover_entities(self):
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

    # ---- lifecycle sync ----
    def ensure_core_devices(self):
        core = [
            (self.pref('Status'),'Text'),
            (self.pref('Totaal Laden'),'Energy'),
            (self.pref('Totaal kWh'),'CustomkWh'),
            (self.pref('LoadBal'),'Switch')
        ]
        if self.tibber_enabled():
            core.extend([
                (self.pref('Kosten & Samenvatting'),'Text'),
                (self.pref('Beste laden'),'Text')
            ])
        for name, typ in core:
            self.ensure_device_once(name, typ)
        if ULTRA_DEBUG:
            self.ensure_device_once(self.pref('Debug'),'Text')
            self.ensure_device_once(self.pref('Counts'),'Text')
            if self.tibber_enabled():
                self.ensure_device_once(self.pref('Tibber prijs'),'Text')
    
    def ensure_charger_devices(self, base):
        devices = [
            ('Energy','Laden'),
            ('CustomkWh','Totaal & Sessie'),
            ('Text','Status'),
        ]
        if self.tibber_enabled():
            devices.extend([
                ('CustomEUR','Kosten (Sessie/Dag)'),
            ])
        for typ, label in devices:
            self.ensure_device_once(f'{base} {label}', typ)
    
    def initial_sync(self):
        self.chargers = self.discover_entities()
        self.ensure_core_devices()
        for c in self.chargers:
            self.ensure_charger_devices(self.charger_label(c))
        self.write_debug(True)
    
    def refresh_entity_cache_only(self):
        self.chargers = self.discover_entities()
        self.write_debug(False)
    
    def write_debug(self, created=False):
        if ULTRA_DEBUG:
            dbg = {'charger_ids':[c['id'] for c in self.chargers], 'device_count':len(Devices), 'created_cycle':created, 'tibber_enabled': self.tibber_enabled()}
            self.update_text(self.pref('Debug'), json.dumps(dbg, ensure_ascii=False)[:4000])
            self.update_text(self.pref('Counts'), f'chargers={len(self.chargers)}, devices={len(Devices)}')
            if self.tibber_enabled():
                self.update_text(self.pref('Tibber prijs'), json.dumps(self.current_tibber_price(), ensure_ascii=False)[:4000])

    # ---- polling ----
    def poll_all(self):
        self.latest_chargers = {}
        refreshed = self.safe_int(self.state.get('price_cache_refreshed', 0), 0)
        if self.tibber_enabled() and ((self.now_ts() - refreshed) > 900 or not (self.state.get('price_cache') or {})):
            self.refresh_tibber_prices()
        for c in self.chargers:
            self.poll_charger(c)
    
    def poll_charger(self, charger):
        cid = charger['id']
        base = self.charger_label(charger)
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
        status = values.get('chargerOpMode') or ''
        session_status = session.get('status') or session.get('state') or ''
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
        self.update_energy(f'{base} Laden', power_w, total_wh)
        
        # COMPACT: Totaal & Sessie merged
        totaal_sessie = f'{int(round(total_kwh))} kWh | Sessie: {int(round(session_kwh))} kWh'
        self.update_custom(f'{base} Totaal & Sessie', totaal_sessie)
        
        # COMPACT: Status with emoji
        power_emoji = self.power_emoji(power_w)
        status_emoji = self.status_emoji(online, session_active)
        status_text = f'{status_emoji} {power_emoji} {status or session_status or "Standby"} | ⏱️ {laadduur}'
        self.update_text(f'{base} Status', status_text)
        
        if self.tibber_enabled():
            # COMPACT: Kosten merged
            rate = session_cost / session_kwh if session_kwh > 0 else 0.0
            price_emoji = self.price_emoji(rate, self.state.get('price_cache', {}))
            day_cost = self.safe_float(st.get('day_cost_total', 0.0), 0.0)
            costs_text = f'{price_emoji} Sessie: €{self.euro_str(session_cost)} | Dag: €{self.euro_str(day_cost)}'
            self.update_custom(f'{base} Kosten (Sessie/Dag)', costs_text)
        
        self.latest_chargers[cid] = {
            'power': power_w,
            'kwh': total_kwh,
            'wh': total_wh,
            'day_cost': self.safe_float(st.get('day_cost_total', 0.0), 0.0),
            'day_energy_cost': self.safe_float(st.get('day_cost_energy', 0.0), 0.0),
            'day_tax_cost': self.safe_float(st.get('day_cost_tax', 0.0), 0.0),
            'online': online,
        }

    def update_combined(self):
        total_power = sum(v.get('power', 0) for v in self.latest_chargers.values())
        total_kwh = round(sum(v.get('kwh', 0.0) for v in self.latest_chargers.values()), 3)
        total_wh = sum(v.get('wh', 0) for v in self.latest_chargers.values())
        any_online = any(bool(v.get('online')) for v in self.latest_chargers.values())
        
        self.update_energy(self.pref('Totaal Laden'), total_power, total_wh)
        self.update_custom(self.pref('Totaal kWh'), int(round(total_kwh)))
        
        if self.tibber_enabled():
            total_day_cost = round(sum(v.get('day_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_energy = round(sum(v.get('day_energy_cost', 0.0) for v in self.latest_chargers.values()), 2)
            total_day_tax = round(sum(v.get('day_tax_cost', 0.0) for v in self.latest_chargers.values()), 2)
            
            # COMPACT: Kosten & Samenvatting merged
            price_emoji = self.price_status_emoji()
            rate = (total_day_cost / total_kwh) if total_kwh > 0 else 0.0
            currency = self.current_tibber_price().get("currency","EUR")
            kosten_samenvatting = f'{price_emoji} {currency}\nKosten: €{self.euro_str(total_day_cost)} | Tarief: €{self.euro_str(rate)}/kWh\nEnergy: €{self.euro_str(total_day_energy)} | Belasting: €{self.euro_str(total_day_tax)}'
            self.update_text(self.pref('Kosten & Samenvatting'), kosten_samenvatting)
            
            self.update_text(self.pref('Beste laden'), self.cheapest_window_text(3))
            status_msg = ('✅ Online' if any_online else '❌ Offline') + ' | Tibber actief'
            self.update_text(self.pref('Status'), status_msg)
        else:
            self.update_text(self.pref('Status'), '✅ Online' if any_online else '❌ Offline')
        
        self.update_sw(self.pref('LoadBal'), False)

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
                self.update_text(self.pref('Status'), 'Login mislukt')
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
            self.update_text(self.pref('Status'), f'Fout: {e}')

_plugin = BasePlugin()

def onStart(): _plugin.onStart()
def onStop(): _plugin.onStop()
def onHeartbeat(): _plugin.onHeartbeat()
