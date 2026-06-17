# -*- coding: utf-8 -*-

import os
import Domoticz
import domoticz_runtime
from easee_constants import PLUGIN_KEY, CORE_DEVICE_IDS

def image_root(plugin, name, device_id=None):
    n = plugin.norm(name).lower()
    devid = str(device_id or '').upper()

    if devid == CORE_DEVICE_IDS.get('LoadBal', ''):
        return 'EaseeLoadBal'
    if devid.startswith('EASEE_EQ_'):
        label = n.split(' - ')[-1].strip() if ' - ' in n else n
        if label in ('vermogen', 'huisvermogen', 'power'):
            return 'EaseePower'
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
        if 'vermogen' in n or 'huisvermogen' in n:
            return 'EaseePower'
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
    prefixed = plugin.icon_base(root)
    if prefixed in domoticz_runtime.Images:
        return prefixed
    return None

def _collect_image_ids(plugin):
    roots = ['EaseeCharger','EaseeEqualizer','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
    found = {}
    for r in roots:
        key = plugin._icon_images_key(r)
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
    roots = ['EaseeCharger','EaseeEqualizer','EaseePower','EaseeStatus','EaseeAlert','EaseeLoadBal','EaseeCost','EaseeOverview']
    candidates = ['Easee_icons_v2.zip']
    loaded_zip = None
    load_errors = []
    found_zips = []
    zip_loaded = False
    preloaded = plugin._collect_image_ids()
    if len(preloaded) == len(roots):
        plugin.image_ids = preloaded
        plugin.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
        return
    for fn in candidates:
        path = os.path.join(plugin.plugin_dir, fn)
        if not os.path.isfile(path):
            continue
        found_zips.append(fn)
        try:
            if any(plugin._icon_images_key(r) is None for r in roots):
                plugin.log(f'Custom icons laden uit {fn} (map: {plugin.plugin_dir})')
                ok, create_errors = plugin._try_create_icon_zip(fn)
                if ok:
                    zip_loaded = True
                elif create_errors:
                    msg = f'{fn}: Create() mislukt ({"; ".join(create_errors)})'
                    load_errors.append(msg)
                    plugin.error(msg)
            plugin.image_ids = plugin._collect_image_ids()
            if plugin.image_ids:
                loaded_zip = fn
                break
            missing = [r for r in roots if plugin._icon_images_key(r) is None]
            if missing:
                load_errors.append(f'{fn}: icons niet in Images ({", ".join(missing[:3])}{"..." if len(missing) > 3 else ""})')
        except Exception as e:
            msg = f'{fn}: {e}'
            load_errors.append(msg)
            plugin.error(msg)
    if not plugin.image_ids and preloaded:
        plugin.image_ids = preloaded
        plugin.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
    elif plugin.image_ids:
        if zip_loaded and loaded_zip:
            plugin.log(f'Custom icons geladen: {len(plugin.image_ids)} sets ({loaded_zip})')
        else:
            plugin.log(f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
    elif found_zips:
        plugin.log('Waarschuwing: zip gevonden maar laden mislukt — upload handmatig via Instellingen → Meer opties → Aangepaste pictogrammen')
        plugin.log(f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in found_zips:
            plugin.log(f'  {fn}: aanwezig')
        if load_errors:
            plugin.log('Icon zip laden mislukt: ' + '; '.join(load_errors))
    else:
        plugin.log('Waarschuwing: geen custom icon zip gevonden — standaard Domoticz iconen worden gebruikt')
        plugin.log(f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in candidates:
            path = os.path.join(plugin.plugin_dir, fn)
            plugin.log(f'  {fn}: {"aanwezig" if os.path.isfile(path) else "ontbreekt"}')

def apply_images_to_devices(plugin):
    if not plugin.image_ids:
        return
    updated = 0
    for unit, dev in domoticz_runtime.Devices.items():
        try:
            root = plugin.image_root(plugin.norm(dev.Name), getattr(dev, 'DeviceID', ''))
            img_id = plugin.image_ids.get(root)
            if not img_id or getattr(dev, 'Image', 0) == img_id:
                continue
            dev.Update(nValue=dev.nValue, sValue=str(dev.sValue), Image=img_id)
            updated += 1
        except Exception as e:
            plugin.debug(f'icon update failed unit {unit}: {e}')
    if updated:
        plugin.log(f'Custom icons toegepast op {updated} devices')

    # ---- create/update ----
