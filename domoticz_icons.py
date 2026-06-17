# -*- coding: utf-8 -*-

import os
import Domoticz
import domoticz_runtime
from easee_constants import PLUGIN_KEY, CORE_DEVICE_IDS
import easee_logging
import easee_helpers

_ICON_ROOTS = [
    'EaseeCharger', 'EaseeEqualizer', 'EaseePower', 'EaseeStatus', 'EaseeAlert',
    'EaseeLoadBal', 'EaseeCost', 'EaseeOverview',
    'EaseeImport', 'EaseeExport', 'EaseeNet', 'EaseeVoltage',
]

def image_root(plugin, name, device_id=None):
    n = easee_helpers.norm(plugin, name).lower()
    devid = str(device_id or '').upper()

    if devid == CORE_DEVICE_IDS.get('LoadBal', ''):
        return 'EaseeLoadBal'
    if devid.startswith('EASEE_EQ_'):
        label = n.split(' - ')[-1].strip() if ' - ' in n else n
        if label in ('import',):
            return 'EaseeImport'
        if label in ('teruglevering', 'export'):
            return 'EaseeExport'
        if label in ('netto', 'net'):
            return 'EaseeNet'
        if label in ('spanning', 'voltage'):
            return 'EaseeVoltage'
        if label in ('vermogen', 'huisvermogen', 'power'):
            return 'EaseeImport'
        if label in ('status',):
            return 'EaseeEqualizer'
        if 'load bal' in label or 'loadbal' in label or 'load balancing' in label:
            return 'EaseeLoadBal'
        if 'l1' in label or 'l2' in label or 'l3' in label or 'fase' in label:
            return 'EaseePower'
        if 'hoofd' in label or 'zekering' in label or 'huis' in label:
            return 'EaseeEqualizer'
        if 'overzicht' in label or 'overview' in label:
            return 'EaseeOverview'
        return 'EaseeEqualizer'

    if devid.startswith('EASEE_CHG_'):
        label = n.split(' - ')[-1].strip() if ' - ' in n else n
        if label in ('status',):
            return 'EaseeEqualizer'

    is_eq = 'equalizer' in n or 'meterkast' in n
    if is_eq:
        if 'import' in n or 'teruglevering' in n:
            if 'terug' in n or 'export' in n:
                return 'EaseeExport'
            return 'EaseeImport'
        if 'netto' in n or ' net ' in f' {n} ':
            return 'EaseeNet'
        if 'spanning' in n or 'voltage' in n:
            return 'EaseeVoltage'
        if 'vermogen' in n or 'huisvermogen' in n:
            return 'EaseeImport'
        if 'load bal' in n or 'loadbal' in n or 'load balancing' in n:
            return 'EaseeLoadBal'
        if 'l1' in n or 'l2' in n or 'l3' in n or 'fase' in n:
            return 'EaseePower'
        if 'overzicht' in n or 'overview' in n:
            return 'EaseeOverview'
        return 'EaseeEqualizer'

    if 'overzicht' in n or 'beste laden' in n:
        return 'EaseeOverview'
    if 'kosten' in n or 'goedkoop' in n or '€' in n:
        return 'EaseeCost'
    if 'status' in n:
        return 'EaseeStatus'
    if 'loadbal' in n:
        return 'EaseeLoadBal'
    if 'totaal & sessie' in n or ' laden' in n or 'totaal kwh' in n:
        return 'EaseePower'
    return 'EaseeCharger'

def icon_base(plugin, root):
    return f'{PLUGIN_KEY}{root}'

def _icon_images_key(plugin, root):
    if root in domoticz_runtime.Images:
        return root
    prefixed = icon_base(plugin, root)
    if prefixed in domoticz_runtime.Images:
        return prefixed
    return None

def _collect_image_ids(plugin):
    found = {}
    for r in _ICON_ROOTS:
        key = _icon_images_key(plugin, r)
        if key:
            found[r] = domoticz_runtime.Images[key].ID
    return found

def _try_create_icon_zip(plugin, fn):
    errors = []
    for attempt in (lambda: Domoticz.Image(fn).Create(), lambda: Domoticz.Image(Filename=fn).Create()):
        try:
            attempt()
            return True, errors
        except Exception as e:
            errors.append(str(e))
    return False, errors

def load_custom_images(plugin):
    candidates = ['Easee_icons_v2.zip']
    loaded_zip = None
    load_errors = []
    found_zips = []
    zip_loaded = False
    preloaded = _collect_image_ids(plugin)
    if len(preloaded) == len(_ICON_ROOTS):
        plugin.image_ids = preloaded
        easee_logging.info('domoticz_icons', f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
        return
    for fn in candidates:
        path = os.path.join(plugin.plugin_dir, fn)
        if not os.path.isfile(path):
            continue
        found_zips.append(fn)
        try:
            if any(_icon_images_key(plugin, r) is None for r in _ICON_ROOTS):
                easee_logging.info('domoticz_icons', f'Custom icons laden uit {fn} (map: {plugin.plugin_dir})')
                ok, create_errors = _try_create_icon_zip(plugin, fn)
                if ok:
                    zip_loaded = True
                elif create_errors:
                    msg = f'{fn}: Create() mislukt ({"; ".join(create_errors)})'
                    load_errors.append(msg)
                    easee_logging.error('domoticz_icons', msg)
            plugin.image_ids = _collect_image_ids(plugin)
            if plugin.image_ids:
                loaded_zip = fn
                break
            missing = [r for r in _ICON_ROOTS if _icon_images_key(plugin, r) is None]
            if missing:
                load_errors.append(f'{fn}: icons niet in Images ({", ".join(missing[:3])}{"..." if len(missing) > 3 else ""})')
        except Exception as e:
            msg = f'{fn}: {e}'
            load_errors.append(msg)
            easee_logging.error('domoticz_icons', msg)
    if not plugin.image_ids and preloaded:
        plugin.image_ids = preloaded
        easee_logging.info('domoticz_icons', f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
    elif plugin.image_ids:
        if zip_loaded and loaded_zip:
            easee_logging.info('domoticz_icons', f'Custom icons geladen: {len(plugin.image_ids)} sets ({loaded_zip})')
        else:
            easee_logging.info('domoticz_icons', f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
    elif found_zips:
        easee_logging.info('domoticz_icons', 'Waarschuwing: zip gevonden maar laden mislukt — upload handmatig via Instellingen → Meer opties → Aangepaste pictogrammen')
        easee_logging.info('domoticz_icons', f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in found_zips:
            easee_logging.info('domoticz_icons', f'  {fn}: aanwezig')
        if load_errors:
            easee_logging.info('domoticz_icons', 'Icon zip laden mislukt: ' + '; '.join(load_errors))
    else:
        easee_logging.info('domoticz_icons', 'Waarschuwing: geen custom icon zip gevonden — standaard Domoticz iconen worden gebruikt')
        easee_logging.info('domoticz_icons', f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in candidates:
            path = os.path.join(plugin.plugin_dir, fn)
            easee_logging.info('domoticz_icons', f'  {fn}: {"aanwezig" if os.path.isfile(path) else "ontbreekt"}')

def apply_images_to_devices(plugin):
    if not plugin.image_ids:
        return
    updated = 0
    for unit, dev in domoticz_runtime.Devices.items():
        try:
            root = image_root(plugin, easee_helpers.norm(plugin, dev.Name), getattr(dev, 'DeviceID', ''))
            img_id = plugin.image_ids.get(root)
            if not img_id or getattr(dev, 'Image', 0) == img_id:
                continue
            dev.Update(nValue=dev.nValue, sValue=str(dev.sValue), Image=img_id)
            updated += 1
        except Exception as e:
            easee_logging.debug('domoticz_icons', f'icon update failed unit {unit}: {e}')
    if updated:
        easee_logging.info('domoticz_icons', f'Custom icons toegepast op {updated} devices')

    # ---- create/update ----
