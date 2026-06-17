# -*- coding: utf-8 -*-

import os
import sys
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
        if label in ('terug & netto', 'terug en netto', 'energie netto'):
            return 'EaseeNet'
        if label in ('teruglevering', 'export'):
            return 'EaseeNet'
        if label in ('netto', 'net'):
            return 'EaseeNet'
        if label in ('vermogen', 'huisvermogen', 'power'):
            return 'EaseeImport'
        if label in ('status',):
            return 'EaseeEqualizer'
        if label in ('spanning', 'voltage'):
            return 'EaseeEqualizer'
        if 'load bal' in label or 'loadbal' in label or 'load balancing' in label:
            return 'EaseeEqualizer'
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
        if label in ('laden',):
            return 'EaseeCharger'
        if label in ('totaal & sessie',):
            return 'EaseePower'
        if label in ('kosten (sessie/dag)',):
            return 'EaseeCost'

    is_eq = 'equalizer' in n or 'meterkast' in n
    if is_eq:
        if 'terug & netto' in n or 'terug en netto' in n or 'energie netto' in n:
            return 'EaseeNet'
        if 'import' in n and 'terug' not in n and 'netto' not in n:
            return 'EaseeImport'
        if 'teruglevering' in n or ('terug' in n and 'netto' not in n) or 'export' in n:
            return 'EaseeNet'
        if 'netto' in n or ' net ' in f' {n} ':
            return 'EaseeNet'
        if 'spanning' in n or 'voltage' in n:
            return 'EaseeEqualizer'
        if 'vermogen' in n or 'huisvermogen' in n:
            return 'EaseeImport'
        if 'load bal' in n or 'loadbal' in n or 'load balancing' in n:
            return 'EaseeEqualizer'
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

def refresh_images_dict(plugin_globals=None):
    """Herlaad Domoticz Images-dict na Image().Create() — anders blijft image_ids leeg."""
    if plugin_globals:
        domoticz_runtime.bind_plugin_globals(plugin_globals)
    else:
        mod = sys.modules.get('plugin')
        if mod is not None:
            domoticz_runtime.bind_plugin_globals(mod.__dict__)

def _easee_image_keys():
    keys = []
    for key in domoticz_runtime.Images:
        if 'easee' in str(key).lower():
            keys.append(str(key))
    return sorted(keys)

def _icon_images_key(plugin, root):
    candidates = (
        root,
        icon_base(plugin, root),
        f'Easee_{root}',
        f'{PLUGIN_KEY}Easee_{root}',
    )
    for key in candidates:
        if key in domoticz_runtime.Images:
            return key
    root_lower = root.lower()
    for key in domoticz_runtime.Images:
        key_str = str(key)
        key_lower = key_str.lower()
        if key_lower == root_lower or key_lower.endswith(root_lower):
            return key_str
    return None

def _collect_image_ids(plugin):
    found = {}
    for r in _ICON_ROOTS:
        key = _icon_images_key(plugin, r)
        if key:
            found[r] = domoticz_runtime.Images[key].ID
    return found

def _log_icon_startup_diagnostic(plugin, zip_path=None, zip_exists=False, zip_size=0,
                                  create_ok=None, create_errors=None, create_method=None):
    refresh_images_dict()
    total_keys = len(domoticz_runtime.Images)
    easee_keys = _easee_image_keys()
    easee_logging.info(
        'domoticz_icons',
        f'Images dict: {total_keys} keys totaal, {len(easee_keys)} met "Easee"',
    )
    if easee_keys:
        preview = ', '.join(easee_keys[:8])
        if len(easee_keys) > 8:
            preview += '...'
        easee_logging.info('domoticz_icons', f'Easee Images-voorbeelden: {preview}')
    elif total_keys:
        easee_logging.info('domoticz_icons', 'Geen Images-keys met "Easee" — handmatige upload waarschijnlijk nodig')

    if zip_path is not None:
        easee_logging.info(
            'domoticz_icons',
            f'Zip: {zip_path} | bestaat: {zip_exists} | grootte: {zip_size} bytes',
        )
    if create_ok is not None:
        if create_ok:
            easee_logging.info('domoticz_icons', f'Zip Create(): succes ({create_method or "onbekend"})')
        else:
            easee_logging.error(
                'domoticz_icons',
                f'Zip Create(): mislukt — {"; ".join(create_errors or ["onbekend"])}',
            )

    mappings = _collect_image_ids(plugin)
    easee_logging.info('domoticz_icons', f'image_ids: {len(mappings)}/{len(_ICON_ROOTS)} sets')
    if mappings:
        sample = ', '.join(f'{k}={v}' for k, v in list(mappings.items())[:3])
        easee_logging.info('domoticz_icons', f'image_ids voorbeeld: {sample}')
    else:
        easee_logging.error(
            'domoticz_icons',
            'image_ids leeg — upload Easee_icons_v2.zip via Instellingen → Meer opties → Aangepaste pictogrammen, herstart hardware-item',
        )
    return mappings

def _try_create_icon_zip(plugin, path, fn):
    errors = []
    attempts = (
        ('Image(path).Create()', lambda: Domoticz.Image(path).Create()),
        ('Image(Filename=path).Create()', lambda: Domoticz.Image(Filename=path).Create()),
        ('Image(fn).Create()', lambda: Domoticz.Image(fn).Create()),
        ('Image(Filename=fn).Create()', lambda: Domoticz.Image(Filename=fn).Create()),
    )
    for label, attempt in attempts:
        try:
            attempt()
            return True, errors, label
        except Exception as e:
            errors.append(f'{label}: {e}')
    return False, errors, None

def load_custom_images(plugin, plugin_globals=None):
    refresh_images_dict(plugin_globals)
    candidates = ['Easee_icons_v2.zip']
    loaded_zip = None
    load_errors = []
    found_zips = []
    zip_loaded = False
    create_ok = None
    create_errors = None
    create_method = None
    diagnostic_zip_path = None
    diagnostic_zip_size = 0
    diagnostic_zip_exists = False

    preloaded = _collect_image_ids(plugin)
    if len(preloaded) == len(_ICON_ROOTS):
        plugin.image_ids = preloaded
        plugin.icons_upload_required = False
        easee_logging.info('domoticz_icons', f'Custom icons uit Domoticz (handmatig geüpload): {len(plugin.image_ids)} sets')
        _log_icon_startup_diagnostic(plugin)
        return

    for fn in candidates:
        path = os.path.join(plugin.plugin_dir, fn)
        diagnostic_zip_path = path
        if not os.path.isfile(path):
            continue
        found_zips.append(fn)
        diagnostic_zip_exists = True
        diagnostic_zip_size = os.path.getsize(path)
        try:
            if any(_icon_images_key(plugin, r) is None for r in _ICON_ROOTS):
                easee_logging.info('domoticz_icons', f'Custom icons laden uit {fn} (map: {plugin.plugin_dir})')
                create_ok, create_errors, create_method = _try_create_icon_zip(plugin, path, fn)
                if create_ok:
                    zip_loaded = True
                    refresh_images_dict(plugin_globals)
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
        easee_logging.warning(
            'domoticz_icons',
            'Zip gevonden maar laden mislukt — upload handmatig via Instellingen → Meer opties → Aangepaste pictogrammen',
        )
        easee_logging.warning('domoticz_icons', f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in found_zips:
            easee_logging.warning('domoticz_icons', f'  {fn}: aanwezig')
        if load_errors:
            easee_logging.warning('domoticz_icons', 'Icon zip laden mislukt: ' + '; '.join(load_errors))
    else:
        easee_logging.warning(
            'domoticz_icons',
            'Geen custom icon zip gevonden — standaard Domoticz iconen worden gebruikt',
        )
        easee_logging.warning('domoticz_icons', f'Icon zip zoekpad: {plugin.plugin_dir}')
        for fn in candidates:
            path = os.path.join(plugin.plugin_dir, fn)
            easee_logging.warning('domoticz_icons', f'  {fn}: {"aanwezig" if os.path.isfile(path) else "ontbreekt"}')

    plugin.icons_upload_required = not bool(plugin.image_ids)
    if not plugin.image_ids:
        easee_logging.error(
            'domoticz_icons',
            'Geen custom icon sets geladen (image_ids leeg) — tegels krijgen standaard Text-iconen tot zip handmatig is geüpload',
        )

    _log_icon_startup_diagnostic(
        plugin,
        zip_path=diagnostic_zip_path,
        zip_exists=diagnostic_zip_exists,
        zip_size=diagnostic_zip_size,
        create_ok=create_ok,
        create_errors=create_errors,
        create_method=create_method,
    )

def _is_easee_device(dev):
    devid = str(getattr(dev, 'DeviceID', '') or '')
    if devid.startswith('EASEE_'):
        return True
    name = str(getattr(dev, 'Name', '') or '').lower()
    return 'easee' in name or 'meterkast' in name or 'equalizer' in name

def _current_image_id(dev):
    try:
        return int(getattr(dev, 'Image', 0) or 0)
    except Exception:
        return 0

def _apply_image_to_unit(unit, dev, img_id):
    """Pas custom icoon toe op bestaande tegel; Update(Image=) met UpdateProperties-fallback."""
    nval = int(getattr(dev, 'nValue', 0) or 0)
    sval = str(getattr(dev, 'sValue', ''))
    img_id = int(img_id)
    attempts = (
        {'nValue': nval, 'sValue': sval, 'Image': img_id, 'UpdateProperties': True, 'SuppressTriggers': True},
        {'nValue': nval, 'sValue': sval, 'Image': img_id, 'UpdateProperties': True},
        {'nValue': nval, 'sValue': sval, 'Image': img_id, 'SuppressTriggers': True},
        {'nValue': nval, 'sValue': sval, 'Image': img_id},
    )
    for kwargs in attempts:
        try:
            dev.Update(**kwargs)
            if _current_image_id(dev) == img_id:
                return True, 'Update(Image=..., UpdateProperties=...)'
        except TypeError:
            safe = {k: v for k, v in kwargs.items() if k != 'SuppressTriggers'}
            try:
                dev.Update(**safe)
                if _current_image_id(dev) == img_id:
                    return True, 'Update(Image=...)'
            except Exception:
                continue
        except Exception:
            continue
    for kwargs in (
        {'nValue': nval, 'sValue': sval, 'UpdateProperties': True, 'SuppressTriggers': True},
        {'nValue': nval, 'sValue': sval, 'UpdateProperties': True},
    ):
        try:
            dev.Image = img_id
            dev.Update(**kwargs)
            if _current_image_id(dev) == img_id:
                return True, 'dev.Image + UpdateProperties'
        except TypeError:
            safe = {k: v for k, v in kwargs.items() if k != 'SuppressTriggers'}
            try:
                dev.Image = img_id
                dev.Update(**safe)
                if _current_image_id(dev) == img_id:
                    return True, 'dev.Image + UpdateProperties'
            except Exception:
                continue
        except Exception:
            continue
    try:
        dev.Image = img_id
        dev.Update(nValue=nval, sValue=sval)
        if _current_image_id(dev) == img_id:
            return True, 'dev.Image + Update'
    except Exception as e:
        return False, str(e)
    return False, f'Update voltooid maar Image={_current_image_id(dev)} (verwacht {img_id})'

def apply_icon_to_unit(plugin, unit, force=False):
    dev = domoticz_runtime.Devices.get(unit)
    if dev is None or not _is_easee_device(dev):
        return False
    if not plugin.image_ids:
        return False
    name = easee_helpers.norm(plugin, dev.Name)
    root = image_root(plugin, name, getattr(dev, 'DeviceID', ''))
    img_id = plugin.image_ids.get(root)
    if not img_id:
        return False
    if not force and _current_image_id(dev) == int(img_id):
        return False
    ok, _method = _apply_image_to_unit(unit, dev, img_id)
    if ok:
        easee_logging.info('domoticz_icons', f'Icoon gezet {name} -> {root} (Image={img_id})')
    return ok

def apply_images_to_devices(plugin, force=False):
    refresh_images_dict()
    if not plugin.image_ids:
        plugin.image_ids = _collect_image_ids(plugin)
    plugin.icons_upload_required = not bool(plugin.image_ids)
    if not plugin.image_ids:
        easee_logging.warning(
            'domoticz_icons',
            'apply_images_to_devices overgeslagen: image_ids leeg — upload Easee_icons_v2.zip via Instellingen → Aangepaste pictogrammen',
        )
        return 0
    updated = 0
    for unit, dev in list(domoticz_runtime.Devices.items()):
        if not _is_easee_device(dev):
            continue
        name = easee_helpers.norm(plugin, dev.Name)
        try:
            root = image_root(plugin, name, getattr(dev, 'DeviceID', ''))
            img_id = plugin.image_ids.get(root)
            if not img_id:
                easee_logging.info('domoticz_icons', f'Icoon overgeslagen {name}: geen mapping (root={root})')
                continue
            cur = _current_image_id(dev)
            if not force and cur == int(img_id):
                easee_logging.info('domoticz_icons', f'Icoon OK {name}: Image={cur} ({root})')
                continue
            ok, method = _apply_image_to_unit(unit, dev, img_id)
            new_cur = _current_image_id(dev)
            if ok:
                updated += 1
                easee_logging.info('domoticz_icons', f'Icoon gezet {name}: {cur} -> {new_cur} ({root}, {method})')
            else:
                easee_logging.warning(
                    'domoticz_icons',
                    f'Icoon mislukt {name}: {method} (root={root}, verwacht Image={img_id}, huidig={new_cur})',
                )
        except Exception as e:
            easee_logging.warning('domoticz_icons', f'Icoon update mislukt unit {unit} ({name}): {e}')
    if updated:
        easee_logging.info('domoticz_icons', f'Custom icons toegepast op {updated} Easee-device(s)')
    elif force:
        easee_logging.info('domoticz_icons', 'Geen icon-updates nodig of alle updates mislukt — zie regels hierboven')
    return updated
