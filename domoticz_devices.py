# -*- coding: utf-8 -*-

import hashlib
import traceback
import Domoticz
import domoticz_runtime
import easee_logging
from easee_constants import DEVICE_TYPES, CORE_DEVICE_IDS, ULTRA_DEBUG
import charger_logic
import domoticz_icons
import easee_helpers
import equalizer_logic
import tibber_pricing

_DEVICE_LOG_FIELDS = frozenset({
    'Name', 'Unit', 'DeviceID', 'Type', 'TypeName', 'Subtype', 'Switchtype', 'Options', 'Image',
})
_SENSITIVE_KWARG_KEYS = frozenset({'Password', 'password', 'Token', 'token'})


def _device_kwargs_for_log(kwargs):
    safe = {k: kwargs[k] for k in _DEVICE_LOG_FIELDS if k in kwargs}
    for k in kwargs:
        if k in _SENSITIVE_KWARG_KEYS:
            safe[k] = '***'
    return safe


def _exc_summary(exc):
    return ''.join(traceback.format_exception_only(type(exc), exc)).strip()


def _traceback_summary():
    return traceback.format_exc().strip()

def make_charger_device_id(plugin, cid, label_key):
    raw = f'{cid}|{label_key}'.encode('utf-8', errors='ignore')
    return 'EASEE_CHG_' + hashlib.sha1(raw).hexdigest()[:24].upper()

def make_equalizer_device_id(plugin, eid, label_key):
    raw = f'{eid}|{label_key}'.encode('utf-8', errors='ignore')
    return 'EASEE_EQ_' + hashlib.sha1(raw).hexdigest()[:24].upper()

def make_device_id(plugin, name):
    raw = easee_helpers.norm(plugin, name).encode('utf-8', errors='ignore')
    return 'EASEE_' + hashlib.sha1(raw).hexdigest()[:28].upper()

def rebuild_index(plugin):
    plugin.units_by_name = {}
    plugin.units_by_devid = {}
    for unit, dev in domoticz_runtime.Devices.items():
        plugin.units_by_name[easee_helpers.norm(plugin, dev.Name)] = unit
        devid = getattr(dev, 'DeviceID', '') or ''
        if devid:
            plugin.units_by_devid[str(devid)] = unit

def find_unit(plugin, name):
    return plugin.units_by_name.get(easee_helpers.norm(plugin, name))

def find_unit_by_devid(plugin, devid):
    return plugin.units_by_devid.get(str(devid))

def resolve_unit(plugin, name):
    return find_unit(plugin, name) or find_unit_by_devid(plugin, make_device_id(plugin, name))

def resolve_charger_unit(plugin, cid, label_key):
    return find_unit_by_devid(plugin, make_charger_device_id(plugin, cid, label_key))

def resolve_equalizer_unit(plugin, eid, label_key):
    devid = make_equalizer_device_id(plugin, eid, label_key)
    unit = find_unit_by_devid(plugin, devid)
    if unit is not None:
        return unit
    if label_key == 'Vermogen':
        for legacy_key in ('Import', 'Terug & netto', 'Netto', 'Teruglevering'):
            unit = find_unit_by_devid(plugin, make_equalizer_device_id(plugin, eid, legacy_key))
            if unit is not None:
                return unit
    return None

def resolve_core_unit(plugin, label):
    label = easee_helpers.clean_label(plugin, label)
    devid = CORE_DEVICE_IDS.get(label)
    if devid:
        u = find_unit_by_devid(plugin, devid)
        if u is not None:
            return u
    return find_unit(plugin, label)

def sync_device_name(plugin, unit, name):
    key = easee_helpers.clean_label(plugin, name)
    try:
        current = easee_helpers.norm(plugin, domoticz_runtime.Devices[unit].Name)
        if current == key:
            return
        if 'import' in current.lower() and key.lower().endswith('vermogen'):
            easee_logging.info(
                'domoticz_devices',
                f'Legacy Import-tegel hernoemd: {current} -> {key}',
            )
        domoticz_runtime.Devices[unit].Name = key
        rebuild_index(plugin)
    except Exception as e:
        easee_logging.debug('domoticz_devices', f'device rename failed unit {unit}: {e}')

def _device_subtype(unit):
    try:
        return int(domoticz_runtime.Devices[unit].SubType)
    except Exception:
        return None

def _device_matches_typename(unit, typename):
    spec = DEVICE_TYPES.get(typename, DEVICE_TYPES['Text'])
    try:
        dev = domoticz_runtime.Devices[unit]
        return int(dev.SubType) == spec['Subtype'] and int(dev.Type) == spec['Type']
    except Exception:
        return False

def _delete_device(plugin, unit):
    try:
        dev = domoticz_runtime.Devices[unit]
        name = getattr(dev, 'Name', str(unit))
        dev.Delete()
        rebuild_index(plugin)
        easee_logging.info('domoticz_devices', f'Legacy device verwijderd voor migratie: {name} (unit {unit})')
        return True
    except Exception as e:
        easee_logging.warning('domoticz_devices', f'Device delete mislukt unit {unit}: {e}')
        return False

def _recreate_device_at_unit(plugin, unit, name, typename, device_id):
    """Verwijder legacy tegel (bijv. Energy Import) en maak opnieuw aan als Text Vermogen."""
    key = easee_helpers.clean_label(plugin, name)
    if unit in domoticz_runtime.Devices and not _delete_device(plugin, unit):
        return None
    spec = DEVICE_TYPES.get(typename, DEVICE_TYPES['Text'])
    kwargs = {'Name': key, 'Unit': int(unit), 'DeviceID': device_id}
    if 'TypeName' in spec:
        kwargs['TypeName'] = spec['TypeName']
    else:
        kwargs['Type'] = spec['Type']
        kwargs['Subtype'] = spec['Subtype']
        if 'Switchtype' in spec:
            kwargs['Switchtype'] = spec['Switchtype']
        if 'Options' in spec:
            kwargs['Options'] = spec['Options']
    root = domoticz_icons.image_root(plugin, key, device_id)
    if root in plugin.image_ids:
        kwargs['Image'] = plugin.image_ids[root]
    try:
        Domoticz.Device(**kwargs).Create()
    except Exception as e:
        easee_logging.warning('domoticz_devices', f'Migratie Create() failed for {key}: {_exc_summary(e)}')
        kwargs.pop('Image', None)
        try:
            Domoticz.Device(**kwargs).Create()
        except Exception as e2:
            easee_logging.error('domoticz_devices', f'Migratie Create() definitief mislukt voor {key}: {_exc_summary(e2)}')
            return None
    rebuild_index(plugin)
    easee_logging.info('domoticz_devices', f'Legacy tegel gemigreerd naar {key} ({typename}) op unit {unit}')
    return find_unit_by_devid(plugin, device_id) or find_unit(plugin, key)

def _equalizer_label_from_name(plugin, display, name):
    display_key = easee_helpers.clean_label(plugin, display).lower()
    clean = easee_helpers.clean_label(plugin, name).lower()
    if not clean.startswith(display_key):
        return ''
    suffix = clean[len(display_key):].strip()
    if suffix.startswith('-'):
        suffix = suffix[1:].strip()
    return suffix

def _find_equalizer_legacy_unit(plugin, display, eid, label_key):
    display_key = easee_helpers.clean_label(plugin, display).lower()
    legacy_suffixes = {
        'Vermogen': (
            'import', 'vermogen', 'terug & netto', 'terug en netto',
            'teruglevering', 'netto', 'huisvermogen', 'power',
        ),
    }
    patterns = legacy_suffixes.get(label_key, ())
    for unit, dev in domoticz_runtime.Devices.items():
        devid = str(getattr(dev, 'DeviceID', '') or '')
        if not devid.startswith('EASEE_'):
            continue
        suffix = _equalizer_label_from_name(plugin, display, dev.Name)
        if suffix and any(suffix == p or p in suffix for p in patterns):
            return unit
        name = easee_helpers.clean_label(plugin, dev.Name).lower()
        if name.startswith(display_key) and 'import' in name and label_key == 'Vermogen':
            return unit
    if label_key == 'Vermogen':
        for legacy_key in ('Import', 'Vermogen', 'Terug & netto', 'Netto', 'Teruglevering'):
            unit = find_unit_by_devid(plugin, make_equalizer_device_id(plugin, eid, legacy_key))
            if unit is not None:
                return unit
    return None

def next_free_unit(plugin):
    for unit in range(1, 256):
        if unit not in domoticz_runtime.Devices:
            return unit
    easee_logging.error('domoticz_devices', 'Geen vrije Unit meer beschikbaar (1-255)')
    return None

    # ---- images ----

def ensure_device_once(plugin, name, typename, device_id=None, legacy_names=None):
    key = easee_helpers.clean_label(plugin, name)
    devid = device_id or make_device_id(plugin, key)
    unit = find_unit_by_devid(plugin, devid) if device_id else None
    if unit is None:
        for legacy in (legacy_names or []):
            legacy_key = easee_helpers.clean_label(plugin, legacy)
            unit = find_unit_by_devid(plugin, make_device_id(plugin, legacy_key)) or find_unit(plugin, legacy_key)
            if unit is not None:
                break
    if unit is None and not device_id:
        unit = find_unit_by_devid(plugin, devid) or find_unit(plugin, key)
    if unit is not None:
        sync_device_name(plugin, unit, key)
        domoticz_icons.apply_icon_to_unit(plugin, unit)
        return unit
    unit = next_free_unit(plugin)
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
    root = domoticz_icons.image_root(plugin, key, devid)
    if root in plugin.image_ids:
        kwargs['Image'] = plugin.image_ids[root]
    try:
        Domoticz.Device(**kwargs).Create()
    except Exception as e:
        easee_logging.warning(
            'domoticz_devices',
            f'Device.Create() failed for {key}: {_exc_summary(e)} | '
            f'traceback={_traceback_summary()} | kwargs={_device_kwargs_for_log(kwargs)}',
            'ensure_device_once',
        )
        kwargs.pop('Image', None)
        easee_logging.warning(
            'domoticz_devices',
            f'Retrying Device.Create() without Image for {key} | kwargs={_device_kwargs_for_log(kwargs)}',
            'ensure_device_once',
        )
        try:
            Domoticz.Device(**kwargs).Create()
        except Exception as e2:
            easee_logging.error(
                'domoticz_devices',
                f'Device creation failed for {key} after retry without Image: {_exc_summary(e2)} | '
                f'traceback={_traceback_summary()} | kwargs={_device_kwargs_for_log(kwargs)}',
                'ensure_device_once',
            )
            return None
    rebuild_index(plugin)
    return resolve_unit(plugin, key)

def update_core_text(plugin, label, value):
    u = resolve_core_unit(plugin, easee_helpers.clean_label(plugin, label))
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value)[:4000])

def update_core_custom(plugin, label, value):
    u = resolve_core_unit(plugin, easee_helpers.clean_label(plugin, label))
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value))

def update_core_energy(plugin, label, power_w, total_wh):
    u = resolve_core_unit(plugin, easee_helpers.clean_label(plugin, label))
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')

def update_core_sw(plugin, label, value):
    u = resolve_core_unit(plugin, easee_helpers.clean_label(plugin, label))
    if u is not None:
        state = easee_helpers.truthy(plugin, value)
        domoticz_runtime.Devices[u].Update(nValue=1 if state else 0, sValue='Aan' if state else 'Uit')

def update_text(plugin, name, value):
    u = resolve_unit(plugin, name)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value)[:4000])

def update_custom(plugin, name, value):
    u = resolve_unit(plugin, name)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value))

def update_energy(plugin, name, power_w, total_wh):
    u = resolve_unit(plugin, name)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')

def update_sw(plugin, name, value):
    u = resolve_unit(plugin, name)
    if u is not None:
        state = easee_helpers.truthy(plugin, value)
        domoticz_runtime.Devices[u].Update(nValue=1 if state else 0, sValue='Aan' if state else 'Uit')

def update_charger_text(plugin, cid, label_key, value):
    u = resolve_charger_unit(plugin, cid, label_key)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value)[:4000])

def update_charger_custom(plugin, cid, label_key, value):
    u = resolve_charger_unit(plugin, cid, label_key)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value))

def update_charger_costs(plugin, cid, session_cost, day_cost, session_kwh, session_active):
    u = resolve_charger_unit(plugin, cid, 'Kosten (Sessie/Dag)')
    if u is None:
        return
    tibber_rate = easee_helpers.safe_float(plugin, tibber_pricing.current_tibber_price(plugin).get('total'), 0.0)
    rate = session_cost / session_kwh if session_kwh > 0 else tibber_rate
    price_emoji = tibber_pricing.price_emoji(plugin, rate, plugin.state.get('price_cache', {}))
    session_label = 'Sessie' if session_active else 'Laatste sessie'
    text = f'{price_emoji} {session_label}: €{easee_helpers.euro_str(plugin, session_cost)} | Dag: €{easee_helpers.euro_str(plugin, day_cost)}'
    try:
        is_text = int(domoticz_runtime.Devices[u].SubType) == DEVICE_TYPES['Text']['Subtype']
    except Exception:
        is_text = False
    if is_text:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=text[:4000])
    else:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=easee_helpers.euro_str(plugin, session_cost))

def update_charger_energy(plugin, cid, label_key, power_w, total_wh):
    u = resolve_charger_unit(plugin, cid, label_key)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')

def update_equalizer_text(plugin, eid, label_key, value):
    u = resolve_equalizer_unit(plugin, eid, label_key)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(value)[:4000])

_EQUALIZER_VERMOGEN_ENERGY_WARNED = set()

def update_equalizer_vermogen(plugin, eid, text_value, power_w=0, import_wh=0):
    u = resolve_equalizer_unit(plugin, eid, 'Vermogen')
    if u is None:
        return
    try:
        is_energy = int(domoticz_runtime.Devices[u].SubType) == DEVICE_TYPES['Energy']['Subtype']
    except Exception:
        is_energy = False
    if is_energy:
        key = str(eid)
        if key not in _EQUALIZER_VERMOGEN_ENERGY_WARNED:
            _EQUALIZER_VERMOGEN_ENERGY_WARNED.add(key)
            easee_logging.warning(
                'domoticz_devices',
                f'Equalizer {eid}: legacy Energy-tegel hernoemd naar Vermogen — verwijder wees-tegels en herstart hardware-item voor Text-weergave',
            )
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(import_wh)}')
        return
    domoticz_runtime.Devices[u].Update(nValue=0, sValue=str(text_value)[:4000])

def update_equalizer_energy(plugin, eid, label_key, power_w, total_wh=0):
    u = resolve_equalizer_unit(plugin, eid, label_key)
    if u is not None:
        domoticz_runtime.Devices[u].Update(nValue=0, sValue=f'{int(power_w)};{int(total_wh)}')

    # ---- Easee API ----

def ensure_core_devices(plugin):
    core = [
        ('Status', 'Text'),
        ('Totaal Laden', 'Energy'),
        ('Totaal kWh', 'CustomkWh'),
        ('LoadBal', 'Switch'),
    ]
    if easee_helpers.tibber_enabled(plugin):
        core.extend([
            ('Kosten & Samenvatting', 'Text'),
            ('Beste laden', 'Text'),
        ])
    for label, typ in core:
        devid = CORE_DEVICE_IDS.get(label)
        legacy = [easee_helpers.pref(plugin, label), f'Easee - {label}', f'Easee - Easee - {label}']
        ensure_device_once(plugin, label, typ, device_id=devid, legacy_names=legacy)
    if ULTRA_DEBUG:
        ensure_device_once(plugin, easee_helpers.pref(plugin, 'Debug'),'Text')
        ensure_device_once(plugin, easee_helpers.pref(plugin, 'Counts'),'Text')
        if easee_helpers.tibber_enabled(plugin):
            ensure_device_once(plugin, easee_helpers.pref(plugin, 'Tibber prijs'),'Text')

def ensure_charger_devices(plugin, charger, index):
    display = charger_logic.charger_display_name(plugin, charger, index)
    cid = charger['id']
    devices = [
        ('Energy', 'Laden'),
        ('CustomkWh', 'Totaal & Sessie'),
        ('Text', 'Status'),
    ]
    if easee_helpers.tibber_enabled(plugin):
        devices.append(('Text', 'Kosten (Sessie/Dag)'))
    for typ, label_key in devices:
        name = charger_logic.charger_dev_name(plugin, display, label_key)
        devid = make_charger_device_id(plugin, cid, label_key)
        legacy = [
            easee_helpers.pref(plugin, f'{display} - {label_key}'),
            f'Easee - {display} - {label_key}',
            f'Easee - Easee - {display} - {label_key}',
            f'{easee_helpers.short_id(plugin, cid)} {label_key}',
        ]
        ensure_device_once(plugin, name, typ, device_id=devid, legacy_names=legacy)

def _device_subtype(dev):
    try:
        return int(getattr(dev, 'Subtype', 0) or 0)
    except Exception:
        return 0

def _name_contains_import(plugin, name):
    label = easee_helpers.clean_label(plugin, name).lower()
    return 'import' in label and 'terug' not in label and 'netto' not in label

def _find_legacy_vermogen_unit(plugin, eid, display):
    for legacy_key in ('Import', 'Vermogen', 'Terug & netto', 'Netto', 'Teruglevering'):
        unit = find_unit_by_devid(plugin, make_equalizer_device_id(plugin, eid, legacy_key))
        if unit is not None:
            return unit
    import_name = equalizer_logic.equalizer_dev_name(plugin, display, 'Import')
    unit = find_unit(plugin, import_name)
    if unit is not None:
        return unit
    unit = find_unit_by_devid(plugin, make_device_id(plugin, import_name))
    if unit is not None:
        return unit
    display_l = easee_helpers.norm(plugin, display).lower()
    for unit, dev in domoticz_runtime.Devices.items():
        name = easee_helpers.norm(plugin, dev.Name)
        name_l = name.lower()
        if display_l and display_l not in name_l:
            continue
        if _name_contains_import(plugin, name):
            return unit
    return None

def _recreate_equalizer_text_device(plugin, unit, name, devid):
    old_name = ''
    try:
        old_name = easee_helpers.norm(plugin, domoticz_runtime.Devices[unit].Name)
        domoticz_runtime.Devices[unit].Delete()
        easee_logging.info(
            'domoticz_devices',
            f'Legacy Energy-tegel verwijderd voor Text-migratie: {old_name} (unit {unit})',
        )
    except Exception as e:
        easee_logging.warning(
            'domoticz_devices',
            f'Verwijderen legacy Energy-tegel mislukt unit {unit} ({old_name or name}): {e}',
        )
        return unit
    rebuild_index(plugin)
    new_unit = ensure_device_once(plugin, name, 'Text', device_id=devid)
    if new_unit is not None:
        domoticz_icons.apply_images_to_devices(plugin)
    return new_unit

def ensure_equalizer_devices(plugin, equalizer, index):
    display = equalizer_logic.equalizer_display_name(plugin, equalizer, index)
    eid = equalizer['id']
    devices = [
        ('Text', 'Status'),
        ('Text', 'Vermogen'),
    ]
    for typ, label_key in devices:
        name = equalizer_logic.equalizer_dev_name(plugin, display, label_key)
        devid = make_equalizer_device_id(plugin, eid, label_key)
        legacy = [
            easee_helpers.pref(plugin, f'{display} - {label_key}'),
            f'Easee - {display} - {label_key}',
            f'Easee - Easee - {display} - {label_key}',
        ]
        if label_key == 'Vermogen':
            legacy.extend([
                easee_helpers.pref(plugin, f'{display} - Import'),
                f'Easee - {display} - Import',
                f'Easee - Easee - {display} - Import',
                easee_helpers.pref(plugin, f'{display} - Terug & netto'),
                f'Easee - {display} - Terug & netto',
                f'Easee - Easee - {display} - Terug & netto',
                easee_helpers.pref(plugin, f'{display} - Teruglevering'),
                f'Easee - {display} - Teruglevering',
                f'Easee - Easee - {display} - Teruglevering',
                easee_helpers.pref(plugin, f'{display} - Netto'),
                f'Easee - {display} - Netto',
                f'Easee - Easee - {display} - Netto',
            ])
        unit = find_unit_by_devid(plugin, devid)
        if unit is None and label_key == 'Vermogen':
            unit = _find_legacy_vermogen_unit(plugin, eid, display)
        if unit is not None:
            dev = domoticz_runtime.Devices.get(unit)
            if label_key == 'Vermogen' and dev is not None:
                if _device_subtype(dev) == DEVICE_TYPES['Energy']['Subtype']:
                    easee_logging.info(
                        'domoticz_devices',
                        f'Equalizer {display}: legacy Import Energy → Text Vermogen (unit {unit})',
                    )
                    _recreate_equalizer_text_device(plugin, unit, name, devid)
                    continue
                if _name_contains_import(plugin, dev.Name):
                    easee_logging.info(
                        'domoticz_devices',
                        f'Equalizer {display}: Import-naam → Vermogen (unit {unit})',
                    )
            sync_device_name(plugin, unit, name)
            continue
        ensure_device_once(plugin, name, typ, device_id=devid, legacy_names=legacy)
