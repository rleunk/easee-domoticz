# -*- coding: utf-8 -*-

import json, math
import domoticz_runtime
import easee_api_keys as ak
import easee_logging
import easee_api
import easee_helpers
import easee_state
import charger_logic
import domoticz_devices
from easee_api_keys import (
    EQUALIZER_KEYS,
    FUSE_KEYS,
    OBSERVATION_ID_TO_FIELD,
    OBSERVATION_KEYS,
    SITE_STATE_PATHS,
    SITE_STRUCTURE_KEYS,
    SITE_STRUCTURE_PATHS,
    emobility_fallback_key_tuple,
    emobility_key_tuple,
    fuse_limit_key_tuple,
    is_emobility_key_name,
    is_fuse_limit_key_name,
    is_offline_circuit_current_key_name,
    main_fuse_key_tuple,
    offline_circuit_key_tuple,
    first_power_value,
    first_export_power_value,
    phase_voltage_keys,
    phase_available_current_keys,
    phase_equalized_charge_keys,
)

def amp_value(plugin, value):
    x = easee_helpers.safe_float(plugin, value, 0.0)
    if x <= 0 or x > 200:
        return 0.0
    return x

def is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
    return main_fuse_a > 0 and fuse_a > 0 and abs(fuse_a - main_fuse_a) < 0.5

def fuse_limit_keys(plugin):
    return fuse_limit_key_tuple()

def emobility_keys(plugin):
    return emobility_key_tuple()

def offline_circuit_current_keys(plugin):
    return offline_circuit_key_tuple()

def is_offline_circuit_current_key(plugin, key):
    return is_offline_circuit_current_key_name(key)

def main_fuse_keys(plugin):
    return main_fuse_key_tuple()

def is_fuse_limit_key(plugin, key):
    return is_fuse_limit_key_name(key)

def is_main_limit_key(plugin, key):
    if not isinstance(key, str):
        return False
    if is_fuse_limit_key(plugin, key):
        return True
    kl = key.lower()
    if kl in ('limit', 'maxlimit', 'currentlimit', 'importlimit'):
        return True
    return kl.endswith('limit') and 'circuit' not in kl and 'emobility' not in kl and 'charger' not in kl

def is_emobility_key(plugin, key):
    return is_emobility_key_name(key)

def fuse_limit_from_dict(plugin, data):
    val = easee_helpers.first_dict_value(plugin, data, fuse_limit_keys(plugin))
    return amp_value(plugin, val) if val is not None else 0.0

def emobility_from_dict(plugin, data):
    val = easee_helpers.first_dict_value(plugin, data, emobility_keys(plugin))
    return amp_value(plugin, val) if val is not None else 0.0

def root_circuit_ids(plugin, circuits):
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

def _unique_circuits(plugin, circuits):
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

def fuse_limit_from_circuits(plugin, circuits, circuit_id=None, main_fuse_a=0.0):
    if not isinstance(circuits, list):
        return 0.0, ''
    preferred = None
    root = None
    fallback = None
    target_id = str(circuit_id) if circuit_id is not None else None
    root_ids = root_circuit_ids(plugin, circuits)
    for circuit in circuits:
        if not isinstance(circuit, dict):
            continue
        fuse_a = fuse_limit_from_dict(plugin, circuit)
        if fuse_a <= 0 or is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
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

def fuse_limit_from_circuit_states(plugin, circuit_states, circuit_id=None, main_fuse_a=0.0):
    if not isinstance(circuit_states, list):
        return 0.0, ''
    circuits = []
    for item in circuit_states:
        if not isinstance(item, dict):
            continue
        circuit = item.get('circuit')
        if isinstance(circuit, dict):
            circuits.append(circuit)
    fuse_a, path = fuse_limit_from_circuits(plugin, circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
    if fuse_a > 0 and path:
        return fuse_a, f'circuitStates.{path}'
    return fuse_a, path

def parse_site_structure_json(plugin, raw):
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

def deep_scan_amp_keys(plugin, obj, key_matcher, path=''):
    found = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            p = f'{path}.{key}' if path else str(key)
            if key_matcher(key):
                amps = amp_value(plugin, val)
                if amps > 0:
                    found.append((p, amps))
            if isinstance(val, (dict, list)):
                found.extend(deep_scan_amp_keys(plugin, val, key_matcher, p))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(deep_scan_amp_keys(plugin, item, key_matcher, f'{path}[{idx}]'))
    return found

def deep_scan_amp_range(plugin, obj, path='', min_a=15.0, max_a=30.0, depth=0, max_depth=14):
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
                found.extend(deep_scan_amp_range(plugin, val, p, min_a, max_a, depth + 1, max_depth))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj[:32]):
            found.extend(deep_scan_amp_range(plugin, item, f'{path}[{idx}]', min_a, max_a, depth + 1, max_depth))
    return found

def is_valid_fuse_limit(plugin, val, main_fuse_a=0.0):
    if val <= 0 or val > 63:
        return False
    if is_same_as_main_fuse(plugin, val, main_fuse_a):
        return False
    if main_fuse_a > 0 and val >= main_fuse_a - 0.4:
        return False
    return True

def pick_best_fuse_candidate(plugin, candidates, main_fuse_a=0.0):
    if not candidates:
        return 0.0, ''
    candidates = {
        path: val for path, val in candidates.items()
        if is_valid_fuse_limit(plugin, val, main_fuse_a)
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

def add_fuse_candidate(plugin, candidates, amps, source, main_fuse_a=0.0, rejected=None):
    val = amp_value(plugin, amps)
    if not source or val <= 0:
        return
    if not is_valid_fuse_limit(plugin, val, main_fuse_a):
        if rejected is not None:
            reason = 'gelijk aan hoofdzekering' if is_same_as_main_fuse(plugin, val, main_fuse_a) else 'gefilterd'
            rejected.append(f'{source}={int(round(val))}A ({reason})')
        return
    existing = candidates.get(source)
    if existing is None or val > existing:
        candidates[source] = val

def note_raw_fuse_value(plugin, raw_hits, amps, source):
    val = amp_value(plugin, amps)
    if source and val > 0:
        raw_hits.append(f'{source}={int(round(val))}A')

def collect_fuse_from_circuits_list(plugin, circuits, prefix, candidates, main_fuse_a=0.0, rejected=None, raw_hits=None):
    if not isinstance(circuits, list):
        return 0.0, ''
    if raw_hits is not None:
        for circuit in circuits:
            if not isinstance(circuit, dict):
                continue
            cid = circuit.get('id')
            if circuit.get('fuse') is not None:
                note_raw_fuse_value(plugin, raw_hits, circuit.get('fuse'), f'{prefix}circuit[{cid}].fuse')
            for key, val in circuit.items():
                if isinstance(key, str) and 'fuse' in key.lower() and key.lower() not in ('fusegroup', 'fuseid'):
                    note_raw_fuse_value(plugin, raw_hits, val, f'{prefix}circuit[{cid}].{key}')
    collect_explicit_circuit_fuses(plugin, 
        circuits, prefix, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    rf, rs = root_circuit_fuse(plugin, circuits, main_fuse_a=main_fuse_a, rejected=rejected, raw_hits=raw_hits)
    return rf, rs

def fetch_root_circuit_details(plugin, site_id, circuits, candidates, main_fuse_a=0.0, probes=None, rejected=None, raw_hits=None):
    if not site_id or not isinstance(circuits, list):
        return 0.0, ''
    root_ids = sorted(root_circuit_ids(plugin, circuits))
    best = 0.0
    best_src = ''
    for cid in root_ids:
        path = f'/sites/{site_id}/circuits/{cid}'
        if probes is not None:
            probes.append(path)
        circuit = easee_api.api_get_optional(plugin, path)
        if isinstance(circuit, dict):
            if raw_hits is not None and circuit.get('fuse') is not None:
                note_raw_fuse_value(plugin, raw_hits, circuit.get('fuse'), f'circuit[{cid}].fuse')
            collect_fuse_from_dict(plugin, 
                circuit, f'circuit[{cid}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            fuse_a = fuse_limit_from_dict(plugin, circuit)
            if fuse_a > 0:
                add_fuse_candidate(plugin, 
                    candidates, fuse_a, f'circuit[{cid}].fuse(detail)',
                    main_fuse_a=main_fuse_a, rejected=rejected)
                if is_valid_fuse_limit(plugin, fuse_a, main_fuse_a) and fuse_a > best:
                    best = fuse_a
                    best_src = f'circuit[{cid}].fuse(detail)'
        collect_fuse_from_circuit_settings(plugin, 
            site_id, cid, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    return best, best_src

def collect_fuse_from_dict(plugin, data, prefix, candidates, main_fuse_a=0.0, rejected=None):
    if not isinstance(data, dict):
        return
    fuse_a = fuse_limit_from_dict(plugin, data)
    if fuse_a > 0:
        add_fuse_candidate(plugin, candidates, fuse_a, f'{prefix}.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
    rated = amp_value(plugin, data.get('ratedCurrent'))
    if rated > 0:
        for key, val in data.items():
            if not isinstance(key, str):
                continue
            kl = key.lower()
            if 'fuse' not in kl or kl in ('fusegroup', 'fuseid', 'ratedcurrent'):
                continue
            fuse_val = amp_value(plugin, val)
            if fuse_val > 0 and not is_same_as_main_fuse(plugin, fuse_val, rated):
                add_fuse_candidate(plugin, 
                    candidates, fuse_val, f'{prefix}.{key}', main_fuse_a=main_fuse_a, rejected=rejected)

def scan_any_fuse_keys(plugin, obj, prefix, candidates, main_fuse_a=0.0, rejected=None):
    if isinstance(obj, dict):
        for key, val in obj.items():
            p = f'{prefix}.{key}' if prefix else str(key)
            if isinstance(key, str) and 'fuse' in key.lower():
                kl = key.lower()
                if kl not in ('fusegroup', 'fuseid'):
                    add_fuse_candidate(plugin, candidates, val, p, main_fuse_a=main_fuse_a, rejected=rejected)
            if isinstance(val, (dict, list)):
                scan_any_fuse_keys(plugin, val, p, candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            scan_any_fuse_keys(plugin, item, f'{prefix}[{idx}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)

def collect_fuse_from_circuit_settings(plugin, site_id, circuit_id, candidates, main_fuse_a=0.0, rejected=None):
    if not site_id or circuit_id is None:
        return
    settings = easee_api.api_get_optional(plugin, f'/sites/{site_id}/circuits/{circuit_id}/settings')
    if not isinstance(settings, dict):
        return
    collect_fuse_from_dict(plugin, settings, f'circuit[{circuit_id}].settings', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    scan_any_fuse_keys(plugin, settings, f'circuit[{circuit_id}].settings', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    phase_vals = []
    max_phase_vals = []
    for key in ('maxCircuitCurrentP1', 'maxCircuitCurrentP2', 'maxCircuitCurrentP3'):
        val = amp_value(plugin, settings.get(key))
        if val > 0:
            phase_vals.append(val)
            max_phase_vals.append(val)
            add_fuse_candidate(plugin, 
                candidates, val, f'circuit[{circuit_id}].settings.{key}',
                main_fuse_a=main_fuse_a, rejected=rejected)
    for key in offline_circuit_current_keys(plugin):
        val = amp_value(plugin, settings.get(key))
        if val > 0 and rejected is not None:
            rejected.append(
                f'circuit[{circuit_id}].settings.{key}={int(round(val))}A (offline fallback)')
    if max_phase_vals:
        add_fuse_candidate(plugin, 
            candidates, min(max_phase_vals), f'circuit[{circuit_id}].settings.maxCircuitCurrentPhasesMin',
            main_fuse_a=main_fuse_a, rejected=rejected)
    elif phase_vals:
        add_fuse_candidate(plugin, 
            candidates, min(phase_vals), f'circuit[{circuit_id}].settings.circuitCurrentMin',
            main_fuse_a=main_fuse_a, rejected=rejected)

def collect_fuse_from_equalizer_circuit(plugin, site_id, circuit_id, candidates, main_fuse_a=0.0, rejected=None):
    if not site_id or circuit_id is None:
        return
    circuit = easee_api.api_get_optional(plugin, f'/sites/{site_id}/circuits/{circuit_id}')
    if not isinstance(circuit, dict):
        return
    collect_fuse_from_dict(plugin, 
        circuit, f'equalizerCircuit[{circuit_id}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    scan_any_fuse_keys(plugin, 
        circuit, f'equalizerCircuit[{circuit_id}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
    fuse_a = fuse_limit_from_dict(plugin, circuit)
    if fuse_a > 0:
        add_fuse_candidate(plugin, 
            candidates, fuse_a, f'equalizerCircuit[{circuit_id}].fuse',
            main_fuse_a=main_fuse_a, rejected=rejected)

def collect_explicit_circuit_fuses(plugin, circuits, prefix, candidates, main_fuse_a=0.0, root_only=False, rejected=None):
    if not isinstance(circuits, list):
        return
    root_ids = root_circuit_ids(plugin, circuits) if root_only else None
    for circuit in circuits:
        if not isinstance(circuit, dict):
            continue
        cid = circuit.get('id')
        cid_s = str(cid) if cid is not None else ''
        if root_only and cid_s not in root_ids:
            continue
        if circuit.get('fuse') is not None:
            fuse_val = amp_value(plugin, circuit.get('fuse'))
            tag = '(root)' if root_only else ''
            add_fuse_candidate(plugin, 
                candidates, fuse_val, f'{prefix}circuit[{cid}].fuse{tag}',
                main_fuse_a=main_fuse_a, rejected=rejected)
        collect_fuse_from_dict(plugin, 
            circuit, f'{prefix}circuit[{cid}]', candidates, main_fuse_a=main_fuse_a, rejected=rejected)

def collect_fuse_from_cloud_loadbalancing(plugin, equalizer_id, candidates, main_fuse_a=0.0, probes=None):
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
        data = easee_api.api_get_optional(plugin, path)
        if not isinstance(data, dict):
            continue
        prefix = path.strip('/').replace('/', '.')
        collect_fuse_from_dict(plugin, data, prefix, candidates, main_fuse_a=main_fuse_a)
        scan_any_fuse_keys(plugin, data, prefix, candidates, main_fuse_a=main_fuse_a)
        for path2, amps in deep_scan_amp_keys(plugin, data, lambda key: is_main_limit_key(plugin, key)):
            add_fuse_candidate(plugin, candidates, amps, f'{prefix}.{path2}', main_fuse_a=main_fuse_a)

def root_circuit_fuse(plugin, circuits, main_fuse_a=0.0, rejected=None, raw_hits=None):
    if not isinstance(circuits, list):
        return 0.0, ''
    root_ids = root_circuit_ids(plugin, circuits)
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
            fuse_a = amp_value(plugin, circuit.get('fuse'))
        if fuse_a <= 0:
            fuse_a = fuse_limit_from_dict(plugin, circuit)
        if fuse_a <= 0:
            for key, val in circuit.items():
                if isinstance(key, str) and 'fuse' in key.lower():
                    kl = key.lower()
                    if kl in ('fusegroup', 'fuseid'):
                        continue
                    fuse_a = max(fuse_a, amp_value(plugin, val))
        if raw_hits is not None and fuse_a > 0:
            note_raw_fuse_value(plugin, raw_hits, fuse_a, f'circuit[{cid}].fuse(root-scan)')
        if not is_valid_fuse_limit(plugin, fuse_a, main_fuse_a):
            if rejected is not None and fuse_a > 0:
                reason = 'gelijk aan hoofdzekering' if is_same_as_main_fuse(plugin, fuse_a, main_fuse_a) else 'gefilterd'
                rejected.append(f'circuit[{cid}].fuse(root)={int(round(fuse_a))}A ({reason})')
            continue
        if fuse_a > best:
            best = fuse_a
            best_src = f'circuit[{cid}].fuse(root)'
    return best, best_src

def select_main_fuse_limit(plugin, candidates, main_fuse_a=0.0, root_fuse=0.0, root_source=''):
    if root_fuse > 0 and root_source and is_valid_fuse_limit(plugin, root_fuse, main_fuse_a):
        return root_fuse, root_source
    if root_fuse > 0 and root_source:
        add_fuse_candidate(plugin, candidates, root_fuse, root_source, main_fuse_a=main_fuse_a)
    mcc_src = ak.SITE_STRUCTURE_KEYS['source_max_continuous']
    if mcc_src in candidates and is_valid_fuse_limit(plugin, candidates[mcc_src], main_fuse_a):
        return candidates[mcc_src], mcc_src
    if not candidates:
        return 0.0, ''
    filtered = {
        src: val for src, val in candidates.items()
        if is_valid_fuse_limit(plugin, val, main_fuse_a)
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

def collect_json_key_tree(plugin, obj, path='', depth=0, max_depth=6):
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
                parts.extend(collect_json_key_tree(plugin, val, p, depth + 1, max_depth))
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                parts.extend(collect_json_key_tree(plugin, val[0], f'{p}[0]', depth + 1, max_depth))
    return parts

def log_site_structure_once(plugin, site_id, raw, candidates):
    key = str(site_id or 'unknown')
    if key in plugin.fuse_structure_logged:
        return
    plugin.fuse_structure_logged.add(key)
    keys = structure_top_keys(plugin, raw)
    cand_parts = [f'{src}={int(round(v))}A' for src, v in sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:16]]
    cand_text = ', '.join(cand_parts) if cand_parts else 'geen'
    key_text = ', '.join(keys[:14]) if keys else 'leeg'
    easee_logging.info('equalizer_logic', f'Equalizer siteStructure (site {key}): keys={key_text} | fuse kandidaten: {cand_text}')
    data = parse_site_structure_json(plugin, raw)
    if data:
        mcc = amp_value(plugin, data.get(ak.SITE_STRUCTURE_KEYS['max_continuous_current']))
        rated = amp_value(plugin, data.get(ak.SITE_STRUCTURE_KEYS['rated_current']))
        if mcc > 0:
            if rated > 0 and mcc < rated - 0.4:
                easee_logging.info('equalizer_logic', f'siteStructure maxContinuousCurrent (site {key}): {int(round(mcc))}A (hoofdzekering limiet kandidaat)')
            else:
                easee_logging.info('equalizer_logic', f'siteStructure maxContinuousCurrent (site {key}): {int(round(mcc))}A')
        tree = collect_json_key_tree(plugin, data, ak.SITE_STRUCTURE_KEYS['root'])
        if tree:
            tree_text = ' | '.join(tree[:12])
            if len(tree_text) > 900:
                tree_text = tree_text[:900] + '...'
            easee_logging.info('equalizer_logic', f'siteStructure structuur (site {key}): {tree_text}')
    log_site_structure_numerics_once(plugin, site_id, raw)

def collect_numeric_values(plugin, obj, path='', depth=0, max_depth=12):
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
                found.extend(collect_numeric_values(plugin, val, p, depth + 1, max_depth))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj[:24]):
            found.extend(collect_numeric_values(plugin, item, f'{path}[{idx}]', depth + 1, max_depth))
    return found

def log_site_structure_numerics_once(plugin, site_id, raw):
    key = str(site_id or 'unknown')
    if key in plugin.site_structure_numerics_logged:
        return
    plugin.site_structure_numerics_logged.add(key)
    data = parse_site_structure_json(plugin, raw)
    if not data:
        return
    amp_range = deep_scan_amp_range(plugin, 
        data, ak.SITE_STRUCTURE_KEYS['root'], min_a=15.0, max_a=30.0)
    if amp_range:
        chunk_size = 20
        for i in range(0, len(amp_range), chunk_size):
            chunk = amp_range[i:i + chunk_size]
            easee_logging.info('equalizer_logic', f'siteStructure amp-range 15-30 (site {key}): ' + '; '.join(chunk))
    if domoticz_runtime.Parameters.get('Mode6') == 'Debug':
        numerics = collect_numeric_values(plugin, data, ak.SITE_STRUCTURE_KEYS['root'])
        if numerics:
            chunk_size = 40
            for i in range(0, len(numerics), chunk_size):
                chunk = numerics[i:i + chunk_size]
                easee_logging.debug('equalizer_logic', f'siteStructure numerics (site {key}) [{i // chunk_size + 1}]: ' + '; '.join(chunk))

def log_equalizer_fuse_once(plugin, eid, limit_a, source, probes=None, debug_hits=None, raw_hits=None, rejected=None):
    key = str(eid or '')
    if not key or key in plugin.fuse_first_poll_logged:
        return
    plugin.fuse_first_poll_logged.add(key)
    if limit_a > 0:
        easee_logging.info('equalizer_logic', f'Equalizer fuse: limit={int(round(limit_a))}A src={source}', 'poll')
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
        easee_logging.warning(
            'equalizer_logic',
            'Equalizer fuse: limit=onbekend | ' + (' | '.join(parts) if parts else 'geen fuse-data'),
            'poll',
        )

def fuse_limit_from_deep_scan(plugin, obj, source_prefix='', main_fuse_a=0.0):
    candidates = {}
    for path, amps in deep_scan_amp_keys(plugin, obj, lambda key: is_fuse_limit_key(plugin, key)):
        full = f'{source_prefix}.{path}' if source_prefix else path
        candidates[full] = amps
    for path, amps in deep_scan_amp_keys(plugin, obj, lambda key: is_main_limit_key(plugin, key)):
        full = f'{source_prefix}.{path}' if source_prefix else path
        if full not in candidates:
            candidates[full] = amps
    if not candidates:
        return 0.0, ''
    val, path = pick_best_fuse_candidate(plugin, candidates, main_fuse_a=main_fuse_a)
    return val, path

def collect_fuse_debug(plugin, obj, path=''):
    found = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            p = f'{path}.{key}' if path else str(key)
            kl = str(key).lower()
            if (is_fuse_limit_key(plugin, key) or is_emobility_key(plugin, key)
                    or is_main_limit_key(plugin, key)
                    or kl in ('ratedcurrent', 'maxallocatedcurrent', 'limit')):
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    found.append(f'{p}={val}')
                elif isinstance(val, str) and val.strip().replace('.', '', 1).replace('-', '', 1).isdigit():
                    found.append(f'{p}={val.strip()}')
            if isinstance(val, (dict, list)):
                found.extend(collect_fuse_debug(plugin, val, p))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj[:8]):
            found.extend(collect_fuse_debug(plugin, item, f'{path}[{idx}]'))
    return found

def structure_top_keys(plugin, raw):
    data = parse_site_structure_json(plugin, raw)
    if not data:
        return []
    keys = list(data.keys())[:20]
    for nest_key in SITE_STRUCTURE_KEYS['nested_roots']:
        nested = data.get(nest_key)
        if isinstance(nested, dict):
            keys.append(f'{nest_key}:{{{",".join(list(nested.keys())[:12])}}}')
    return keys

def fuse_limit_from_site_structure(plugin, raw, main_fuse_a=0.0, candidates=None):
    data = parse_site_structure_json(plugin, raw)
    if not data:
        return 0.0, ''
    mcc = amp_value(plugin, data.get(ak.SITE_STRUCTURE_KEYS['max_continuous_current']))
    if mcc > 0 and is_valid_fuse_limit(plugin, mcc, main_fuse_a):
        if candidates is not None:
            add_fuse_candidate(plugin, 
                candidates, mcc, ak.SITE_STRUCTURE_KEYS['source_max_continuous'],
                main_fuse_a=main_fuse_a)
    ss_root = ak.SITE_STRUCTURE_KEYS['root']
    if candidates is not None:
        collect_fuse_from_dict(plugin, data, ss_root, candidates, main_fuse_a=main_fuse_a)
        scan_any_fuse_keys(plugin, data, ss_root, candidates, main_fuse_a=main_fuse_a)
    direct = fuse_limit_from_dict(plugin, data)
    if direct > 0 and not is_same_as_main_fuse(plugin, direct, main_fuse_a):
        if candidates is not None:
            add_fuse_candidate(plugin, candidates, direct, ak.SITE_STRUCTURE_PATHS['fuse'], main_fuse_a=main_fuse_a)
        return direct, ak.SITE_STRUCTURE_PATHS['fuse']
    for key in ak.SITE_STRUCTURE_KEYS['nested_roots']:
        nested = data.get(key)
        if isinstance(nested, dict):
            if candidates is not None:
                collect_fuse_from_dict(plugin, nested, f'{ss_root}.{key}', candidates, main_fuse_a=main_fuse_a)
            nested_val = fuse_limit_from_dict(plugin, nested)
            if nested_val > 0 and not is_same_as_main_fuse(plugin, nested_val, main_fuse_a):
                if candidates is not None:
                    add_fuse_candidate(plugin, candidates, nested_val, f'{ss_root}.{key}.fuse', main_fuse_a=main_fuse_a)
                return nested_val, f'{ss_root}.{key}.fuse'
    circuits = data.get(ak.SITE_STRUCTURE_KEYS['circuits'])
    if isinstance(circuits, list):
        if candidates is not None:
            collect_explicit_circuit_fuses(plugin, 
                circuits, f'{ss_root}.', candidates, main_fuse_a=main_fuse_a)
        fuse_a, path = fuse_limit_from_circuits(plugin, circuits, main_fuse_a=main_fuse_a)
        if fuse_a > 0 and not is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
            if candidates is not None:
                add_fuse_candidate(plugin, candidates, fuse_a, f'{ss_root}.{path}', main_fuse_a=main_fuse_a)
            return fuse_a, f'{ss_root}.{path}'
    panels = data.get(ak.SITE_STRUCTURE_KEYS['panels'])
    if isinstance(panels, list):
        if candidates is not None:
            for panel in panels:
                if isinstance(panel, dict):
                    pid = panel.get('id', panel.get('circuitPanelId', ''))
                    collect_fuse_from_dict(plugin, 
                        panel, f'{ss_root}.panel[{pid}]', candidates, main_fuse_a=main_fuse_a)
        fuse_a, path = fuse_limit_from_circuits(plugin, panels, main_fuse_a=main_fuse_a)
        if fuse_a > 0 and not is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
            if candidates is not None:
                add_fuse_candidate(plugin, candidates, fuse_a, f'{ss_root}.{path}', main_fuse_a=main_fuse_a)
            return fuse_a, f'{ss_root}.{path}'
    fuse_a, path = fuse_limit_from_deep_scan(plugin, data, ss_root, main_fuse_a=main_fuse_a)
    if fuse_a > 0:
        if candidates is not None:
            add_fuse_candidate(plugin, candidates, fuse_a, path, main_fuse_a=main_fuse_a)
        return fuse_a, path
    return 0.0, ''

def emobility_from_site_structure(plugin, raw):
    data = parse_site_structure_json(plugin, raw)
    if not data:
        return 0.0
    direct = emobility_from_dict(plugin, data)
    if direct > 0:
        return direct
    for key in ak.SITE_STRUCTURE_KEYS['nested_emobility']:
        nested = data.get(key)
        if isinstance(nested, dict):
            nested_val = emobility_from_dict(plugin, nested)
            if nested_val > 0:
                return nested_val
    for _, amps in deep_scan_amp_keys(plugin, data, lambda key: is_emobility_key(plugin, key)):
        if amps > 0:
            return amps
    return 0.0

def fuse_limit_from_equalizer_values(plugin, values, main_fuse_a=0.0):
    if not isinstance(values, dict):
        return 0.0, ''
    direct = fuse_limit_from_dict(plugin, values)
    if direct > 0 and not is_same_as_main_fuse(plugin, direct, main_fuse_a):
        return direct, 'equalizer.fuse'
    for key in ('config', 'state', 'settings', 'loadBalancing', 'limits'):
        nested = values.get(key)
        if isinstance(nested, dict):
            nested_val = fuse_limit_from_dict(plugin, nested)
            if nested_val > 0 and not is_same_as_main_fuse(plugin, nested_val, main_fuse_a):
                return nested_val, f'equalizer.{key}.fuse'
    fuse_a, path = fuse_limit_from_deep_scan(plugin, values, 'equalizer', main_fuse_a=main_fuse_a)
    return fuse_a, path

def fuse_limit_from_products(plugin, site_id, circuit_id=None, main_fuse_a=0.0):
    products = easee_api.api_get_optional(plugin, '/accounts/products')
    if not isinstance(products, list):
        return 0.0, ''
    target = str(site_id)
    for product in products:
        if not isinstance(product, dict):
            continue
        pid = product.get('id') or product.get('siteId')
        if pid is None or str(pid) != target:
            continue
        fuse_a = fuse_limit_from_dict(plugin, product)
        if fuse_a > 0 and not is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
            return fuse_a, 'accounts/products.fuse'
        circuits = product.get('circuits')
        fuse_a, path = fuse_limit_from_circuits(plugin, circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            return fuse_a, f'accounts/products.{path}'
        equalizers = product.get('equalizers')
        if isinstance(equalizers, list):
            for eq in equalizers:
                if isinstance(eq, dict):
                    fuse_a = fuse_limit_from_dict(plugin, eq)
                    if fuse_a > 0 and not is_same_as_main_fuse(plugin, fuse_a, main_fuse_a):
                        return fuse_a, 'accounts/products.equalizer.fuse'
    return 0.0, ''

def set_emobility(plugin, info, amps, source):
    if amps <= 0:
        return
    existing = info.get('emobility_a', 0.0)
    existing_src = str(info.get('emobility_source', ''))
    src_text = str(source)
    site_state_mac = SITE_STATE_PATHS['site_state_mac']
    emob_primary = FUSE_KEYS['emobility_primary']
    if site_state_mac in src_text:
        info['emobility_a'] = amps
        info['emobility_source'] = source
        return
    if site_state_mac in existing_src:
        return
    prefer_new = emob_primary in src_text
    prefer_existing = emob_primary in existing_src
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

def log_fuse_probe_debug(plugin, site_id, info, debug_hits, candidates=None, site_structure=None, raw_hits=None, rejected=None):
    if domoticz_runtime.Parameters.get('Mode6') != 'Debug':
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
        keys = structure_top_keys(plugin, site_structure)
        if keys:
            parts.append('siteStructure keys=' + ', '.join(keys))
    easee_logging.debug('equalizer_logic', 'Fuse probes: ' + ' | '.join(parts))

def fetch_site_fuse_info(plugin, site_id, circuit_id=None, site_structure=None, equalizer_values=None, equalizer_id=None):
    if not site_id:
        return {}
    cache_key = f'{site_id}:{circuit_id or ""}'
    if cache_key in plugin.site_fuse_cache:
        return plugin.site_fuse_cache[cache_key]
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
    state = easee_api.api_get_optional(plugin, state_path)
    if isinstance(state, dict):
        site = state.get('site') or {}
        if isinstance(site, dict):
            debug_hits.extend(collect_fuse_debug(plugin, site, 'site.state'))
            main_fuse = easee_helpers.first_dict_value(plugin, site, main_fuse_keys(plugin))
            if main_fuse is not None:
                main_fuse_a = amp_value(plugin, main_fuse)
                info['main_fuse_a'] = main_fuse_a
            if site.get(FUSE_KEYS['fuse_raw'][0]) is not None:
                note_raw_fuse_value(plugin, raw_hits, site.get(FUSE_KEYS['fuse_raw'][0]), 'site.state.fuse')
                add_fuse_candidate(plugin, 
                    candidates, site.get(FUSE_KEYS['fuse_raw'][0]), 'site.state.fuse',
                    main_fuse_a=main_fuse_a, rejected=rejected)
            collect_fuse_from_dict(plugin, site, 'site.state', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            scan_any_fuse_keys(plugin, site, 'site.state', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
            for path, amps in deep_scan_amp_keys(plugin, site, lambda key: is_main_limit_key(plugin, key)):
                add_fuse_candidate(plugin, 
                    candidates, amps, f'site.state.{path}', main_fuse_a=main_fuse_a, rejected=rejected)
            fuse_limit = easee_helpers.first_dict_value(plugin, site, fuse_limit_keys(plugin))
            if fuse_limit is not None:
                note_raw_fuse_value(plugin, raw_hits, fuse_limit, 'site.state.fuseLimit')
                add_fuse_candidate(plugin, 
                    candidates, fuse_limit, 'site.state.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
            mac = site.get(FUSE_KEYS['emobility_primary'])
            if mac is not None:
                set_emobility(plugin, info, amp_value(plugin, mac), SITE_STATE_PATHS['site_state_mac'])
            else:
                emobility = easee_helpers.first_dict_value(plugin, site, emobility_fallback_key_tuple())
                if emobility is not None:
                    set_emobility(plugin, info, amp_value(plugin, emobility), SITE_STATE_PATHS['site_state_emobility'])
            site_circuits = site.get('circuits')
            if isinstance(site_circuits, list):
                all_circuits.extend(site_circuits)
                debug_hits.extend(collect_fuse_debug(plugin, site_circuits, 'site.state.circuits'))
                rf, rs = collect_fuse_from_circuits_list(plugin, 
                    site_circuits, 'site.state.circuits.', candidates, main_fuse_a=main_fuse_a,
                    rejected=rejected, raw_hits=raw_hits)
                remember_root(rf, f'site.state.circuits.{rs}')
        mac_root = state.get(FUSE_KEYS['emobility_primary'])
        if mac_root is not None:
            set_emobility(plugin, info, amp_value(plugin, mac_root), SITE_STATE_PATHS['site_state_mac'])
        circuit_states = state.get('circuitStates')
        debug_hits.extend(collect_fuse_debug(plugin, circuit_states, 'circuitStates'))
        if isinstance(circuit_states, list):
            circuits = []
            for item in circuit_states:
                if not isinstance(item, dict):
                    continue
                circuit = item.get('circuit')
                if isinstance(circuit, dict):
                    circuits.append(circuit)
                    all_circuits.append(circuit)
                mac = item.get(FUSE_KEYS['emobility_primary'])
                if mac is not None:
                    set_emobility(plugin, info, amp_value(plugin, mac), SITE_STATE_PATHS['circuit_states_mac'])
            rf, rs = collect_fuse_from_circuits_list(plugin, 
                circuits, 'circuitStates.', candidates, main_fuse_a=main_fuse_a,
                rejected=rejected, raw_hits=raw_hits)
            remember_root(rf, f'circuitStates.{rs}')
            if circuit_id is not None:
                fuse_a, src = fuse_limit_from_circuits(plugin, 
                    circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
                if fuse_a > 0:
                    add_fuse_candidate(plugin, 
                        candidates, fuse_a, f'circuitStates.{src}',
                        main_fuse_a=main_fuse_a, rejected=rejected)

    if site_structure is not None:
        probes.append('equalizer.observations.siteStructure')
        debug_hits.extend(collect_fuse_debug(plugin, parse_site_structure_json(plugin, site_structure), ak.SITE_STRUCTURE_KEYS['root']))
        fuse_limit_from_site_structure(plugin, 
            site_structure, main_fuse_a=main_fuse_a, candidates=candidates)
        emob = emobility_from_site_structure(plugin, site_structure)
        if emob > 0:
            set_emobility(plugin, info, emob, SITE_STATE_PATHS['site_structure_mac'])
        log_site_structure_once(plugin, site_id, site_structure, candidates)

    site_path = f'/sites/{site_id}'
    probes.append(site_path)
    site_basic = easee_api.api_get_optional(plugin, site_path)
    if isinstance(site_basic, dict):
        debug_hits.extend(collect_fuse_debug(plugin, site_basic, 'site.basic'))
        if main_fuse_a <= 0:
            main_fuse = easee_helpers.first_dict_value(plugin, site_basic, main_fuse_keys(plugin))
            if main_fuse is not None:
                main_fuse_a = amp_value(plugin, main_fuse)
                info['main_fuse_a'] = main_fuse_a
        collect_fuse_from_dict(plugin, site_basic, 'site.basic', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        if isinstance(site_basic.get('circuits'), list):
            all_circuits.extend(site_basic.get('circuits'))
        rf, rs = collect_fuse_from_circuits_list(plugin, 
            site_basic.get('circuits'), 'site.basic.', candidates, main_fuse_a=main_fuse_a,
            rejected=rejected, raw_hits=raw_hits)
        remember_root(rf, f'site.basic.{rs}')

    detailed_path = f'/sites/{site_id}?detailed=true'
    probes.append(detailed_path)
    detailed = easee_api.api_get_optional(plugin, detailed_path)
    if isinstance(detailed, dict):
        debug_hits.extend(collect_fuse_debug(plugin, detailed, 'site.detailed'))
        if main_fuse_a <= 0:
            main_fuse = easee_helpers.first_dict_value(plugin, detailed, main_fuse_keys(plugin))
            if main_fuse is not None:
                main_fuse_a = amp_value(plugin, main_fuse)
                info['main_fuse_a'] = main_fuse_a
        collect_fuse_from_dict(plugin, detailed, 'site.detailed', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        fuse_limit = easee_helpers.first_dict_value(plugin, detailed, fuse_limit_keys(plugin))
        if fuse_limit is not None:
            note_raw_fuse_value(plugin, raw_hits, fuse_limit, 'site.detailed.fuseLimit')
            add_fuse_candidate(plugin, 
                candidates, fuse_limit, 'site.detailed.fuse', main_fuse_a=main_fuse_a, rejected=rejected)
        if isinstance(detailed.get('circuits'), list):
            all_circuits.extend(detailed.get('circuits'))
        rf, rs = collect_fuse_from_circuits_list(plugin, 
            detailed.get('circuits'), 'site.detailed.', candidates, main_fuse_a=main_fuse_a,
            rejected=rejected, raw_hits=raw_hits)
        remember_root(rf, f'site.detailed.{rs}')
        fuse_a, src = fuse_limit_from_circuits(plugin, 
            detailed.get('circuits'), circuit_id=circuit_id, main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            add_fuse_candidate(plugin, 
                candidates, fuse_a, f'site.detailed.{src}', main_fuse_a=main_fuse_a, rejected=rejected)
        mac = detailed.get(FUSE_KEYS['emobility_primary'])
        if mac is not None:
            set_emobility(plugin, info, amp_value(plugin, mac), SITE_STATE_PATHS['site_detailed_mac'])
        elif info.get('emobility_a', 0.0) <= 0:
            emobility = easee_helpers.first_dict_value(plugin, detailed, emobility_fallback_key_tuple())
            if emobility is not None:
                set_emobility(plugin, info, amp_value(plugin, emobility), SITE_STATE_PATHS['site_detailed_emobility'])

    circuits_path = f'/sites/{site_id}/circuits'
    probes.append(circuits_path)
    circuits = easee_api.api_get_optional(plugin, circuits_path)
    debug_hits.extend(collect_fuse_debug(plugin, circuits, 'circuits'))
    if isinstance(circuits, list):
        all_circuits.extend(circuits)
        rf, rs = collect_fuse_from_circuits_list(plugin, 
            circuits, 'circuits.', candidates, main_fuse_a=main_fuse_a,
            rejected=rejected, raw_hits=raw_hits)
        remember_root(rf, f'circuits.{rs}')
        fuse_a, src = fuse_limit_from_circuits(plugin, 
            circuits, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            add_fuse_candidate(plugin, 
                candidates, fuse_a, f'circuits.{src}', main_fuse_a=main_fuse_a, rejected=rejected)

    rf, rs = fetch_root_circuit_details(plugin, 
        site_id, _unique_circuits(plugin, all_circuits), candidates, main_fuse_a=main_fuse_a,
        probes=probes, rejected=rejected, raw_hits=raw_hits)
    remember_root(rf, rs)

    if circuit_id is not None:
        settings_path = f'/sites/{site_id}/circuits/{circuit_id}/settings'
        probes.append(settings_path)
    collect_fuse_from_circuit_settings(plugin, 
        site_id, circuit_id, candidates, main_fuse_a=main_fuse_a, rejected=rejected)

    if circuit_id is not None:
        eq_circuit_path = f'/sites/{site_id}/circuits/{circuit_id}'
        probes.append(eq_circuit_path)
    collect_fuse_from_equalizer_circuit(plugin, 
        site_id, circuit_id, candidates, main_fuse_a=main_fuse_a, rejected=rejected)

    collect_fuse_from_cloud_loadbalancing(plugin, 
        equalizer_id, candidates, main_fuse_a=main_fuse_a, probes=probes)

    probes.append('/accounts/products')
    fuse_a, src = fuse_limit_from_products(plugin, 
        site_id, circuit_id=circuit_id, main_fuse_a=main_fuse_a)
    if fuse_a > 0:
        add_fuse_candidate(plugin, 
            candidates, fuse_a, f'accounts/products.{src}', main_fuse_a=main_fuse_a, rejected=rejected)

    if equalizer_values:
        debug_hits.extend(collect_fuse_debug(plugin, equalizer_values, 'equalizer'))
        collect_fuse_from_dict(plugin, 
            equalizer_values, 'equalizer', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        scan_any_fuse_keys(plugin, 
            equalizer_values, 'equalizer', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        for key in ('config', 'state', 'settings', 'loadBalancing', 'limits'):
            nested = equalizer_values.get(key)
            if isinstance(nested, dict):
                collect_fuse_from_dict(plugin, 
                    nested, f'equalizer.{key}', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
                scan_any_fuse_keys(plugin, 
                    nested, f'equalizer.{key}', candidates, main_fuse_a=main_fuse_a, rejected=rejected)
        fuse_a, src = fuse_limit_from_equalizer_values(plugin, 
            equalizer_values, main_fuse_a=main_fuse_a)
        if fuse_a > 0:
            add_fuse_candidate(plugin, 
                candidates, fuse_a, src or 'equalizer.fuse', main_fuse_a=main_fuse_a, rejected=rejected)

    limit_a, limit_src = select_main_fuse_limit(plugin, 
        candidates, main_fuse_a=main_fuse_a,
        root_fuse=root_fuse, root_source=root_source)
    if limit_a > 0:
        info['main_fuse_limit_a'] = limit_a
        info['main_fuse_limit_source'] = limit_src

    info['fuse_raw_hits'] = raw_hits
    info['fuse_rejected'] = rejected
    info['fuse_debug_hits'] = debug_hits

    if equalizer_values:
        mpi = equalizer_values.get(EQUALIZER_KEYS['max_power_import'][0])
        if mpi is not None:
            power_w = easee_helpers.kw_to_watts(plugin, mpi)
            if power_w > 0:
                info['max_power_import_kw'] = easee_helpers.safe_float(plugin, mpi, 0.0)
                if abs(info['max_power_import_kw']) >= 100:
                    info['max_power_import_kw'] /= 1000.0
                info['max_power_import_w'] = power_w
                info['max_power_import_a'] = round(easee_helpers.amps_balanced_3phase_from_power(plugin, power_w))

    log_fuse_probe_debug(plugin, 
        site_id, info, debug_hits, candidates=candidates, site_structure=site_structure,
        raw_hits=raw_hits, rejected=rejected)
    plugin.site_fuse_cache[cache_key] = info
    return info

def parse_equalizer_observations(plugin, obs):
    values = {}
    if not isinstance(obs, dict):
        return values
    observations = obs.get(OBSERVATION_KEYS['container'][0]) or obs.get(OBSERVATION_KEYS['container'][1]) or []
    if not isinstance(observations, list):
        return values
    for item in observations:
        if not isinstance(item, dict):
            continue
        obs_id = item.get('id')
        obs_val = item.get('value')
        field = OBSERVATION_ID_TO_FIELD.get(obs_id)
        if field is not None:
            values[field] = obs_val
    return values

    # ---- Tibber API ----

def custom_equalizer_name(plugin):
    return easee_helpers.clean_label(plugin, domoticz_runtime.Parameters.get('Address', '') or '')

def manual_equalizer_id(plugin):
    return str(domoticz_runtime.Parameters.get('IP', '') or '').strip()

def equalizer_display_name(plugin, equalizer, index):
    custom = custom_equalizer_name(plugin)
    if custom and index == 0:
        return custom
    api_name = easee_helpers.clean_label(plugin, str(equalizer.get('name') or '').strip())
    eid = str(equalizer.get('id') or '').strip()
    if api_name and api_name.lower() not in (eid.lower(), easee_helpers.short_id(plugin, eid).lower(), 'circuit', 'equalizer'):
        return api_name
    return 'Equalizer' if index == 0 else f'Equalizer {index + 1}'

def equalizer_dev_name(plugin, display, label):
    return easee_helpers.clean_label(plugin, f'{display} - {label}')

def _phase_values_from_keys(plugin, values, key_groups):
    phases = []
    any_val = False
    for keys in key_groups:
        val = easee_helpers.first_dict_value(plugin, values, keys)
        if val is not None:
            any_val = True
            phases.append(easee_helpers.safe_float(plugin, val, 0.0))
        else:
            phases.append(None)
    return phases, any_val

def _format_phase_triple(plugin, phases, unit, decimals=1):
    parts = []
    for val in phases:
        if val is None:
            parts.append('—')
        elif val <= 0 and unit == 'A':
            parts.append('0.0')
        elif unit == 'V':
            parts.append(f'{int(round(val))}' if abs(val - round(val)) < 0.5 else f'{val:.1f}')
        elif abs(val - round(val)) < 0.05:
            parts.append(f'{int(round(val))}.0')
        else:
            parts.append(f'{val:.{decimals}f}')
    return ' / '.join(parts)

def _energy_wh_from_field(plugin, eid, values, field_name, state_key, power_w):
    if field_name in values:
        kwh = easee_helpers.kwh_value(plugin, values.get(field_name))
        total_wh = easee_helpers.wh_from_kwh(plugin, kwh)
        easee_logging.debug(
            'equalizer_logic',
            f'Equalizer {eid} {state_key} kWh: {field_name} {kwh} kWh → {total_wh} Wh',
            'energy',
        )
        return total_wh
    st = easee_state.equalizer_state(plugin, eid)
    integrated_key = f'integrated_{state_key}_kwh'
    st[integrated_key] = round(
        easee_helpers.safe_float(plugin, st.get(integrated_key), 0.0)
        + charger_logic.power_integrated_kwh(plugin, power_w),
        6,
    )
    total_wh = easee_helpers.wh_from_kwh(plugin, st[integrated_key])
    easee_logging.debug(
        'equalizer_logic',
        f'Equalizer {eid} {state_key} kWh: fallback integrated {st[integrated_key]} kWh → {total_wh} Wh',
        'energy',
    )
    return total_wh

def _import_power_w(plugin, values):
    raw = first_power_value(values)
    power_w = easee_helpers.kw_to_watts(plugin, raw)
    if power_w <= 0 and raw is not None:
        power_w = easee_helpers.power_watts(plugin, raw)
    return power_w

def _export_power_w(plugin, values):
    raw = first_export_power_value(values)
    power_w = easee_helpers.kw_to_watts(plugin, raw)
    if power_w <= 0 and raw is not None:
        power_w = easee_helpers.power_watts(plugin, raw)
    return max(0, power_w)

def _voltage_lines(plugin, values):
    phases, has = _phase_values_from_keys(plugin, values, phase_voltage_keys())
    if not has:
        return '⚡ Spanning: onbekend'
    return f'⚡ L1/L2/L3: {_format_phase_triple(plugin, phases, "V")} V'

def _phase_values_from_key_list(plugin, values, keys):
    phases = []
    any_val = False
    for key in keys:
        if key in values and values.get(key) is not None:
            any_val = True
            phases.append(easee_helpers.safe_float(plugin, values.get(key), 0.0))
        else:
            phases.append(None)
    return phases, any_val

def _load_balancing_detail_text(plugin, values, lb_active):
    avail, has_avail = _phase_values_from_key_list(plugin, values, phase_available_current_keys())
    eq, has_eq = _phase_values_from_key_list(plugin, values, phase_equalized_charge_keys())
    lines = []
    lb_emoji = '⚖️' if lb_active else '⏸️'
    lines.append(f'{lb_emoji} Load balancing: {"Aan" if lb_active else "Uit"}')
    if has_avail:
        lines.append(f'🔋 Vrij L1/L2/L3: {_format_phase_triple(plugin, avail, "A")} A')
    else:
        lines.append('🔋 Vrij L1/L2/L3: onbekend')
    if has_eq:
        lines.append(f'🔌 Gelijkstroom L1/L2/L3: {_format_phase_triple(plugin, eq, "A")} A')
    else:
        lines.append('🔌 Gelijkstroom L1/L2/L3: onbekend')
    return '\n'.join(lines)

def _netto_text(plugin, net_w, import_kwh, export_kwh):
    sign = '+' if net_w >= 0 else '−'
    lines = [f'📊 Netto: {sign}{abs(int(net_w))} W']
    if import_kwh is not None and export_kwh is not None:
        net_kwh = round(import_kwh - export_kwh, 3)
        lines.append(f'📈 Totaal netto: {net_kwh:.3f} kWh')
    return '\n'.join(lines)

def _equalizer_matches_filter(plugin, name, site_name):
    flt = domoticz_runtime.Parameters.get('Mode5', '').strip().lower()
    if not flt:
        return True
    return flt in str(name).lower() or flt in str(site_name).lower()

def _append_equalizer(plugin, equalizers, seen, eq, ignore_filter=False):
    eid = str(eq.get('id') or '').strip()
    if not eid or eid in seen:
        return False
    if not ignore_filter and not _equalizer_matches_filter(plugin, eq.get('name', ''), eq.get('siteName', '')):
        return False
    equalizers.append(eq)
    seen.add(eid)
    return True

def _scan_equalizers_in_object(plugin, obj, found, site_name=''):
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
            _scan_equalizers_in_object(plugin, value, found, site_name=site or site_name)
    elif isinstance(obj, list):
        for item in obj:
            _scan_equalizers_in_object(plugin, item, found, site_name=site_name)

def _ingest_equalizer_items(plugin, equalizers, seen, items, source, site_name='', site_id=None, ignore_filter=False):
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
        if _append_equalizer(plugin, equalizers, seen, eq, ignore_filter=ignore_filter):
            added += 1
    return added

def discover_equalizers(plugin):
    equalizers = []
    seen = set()
    sources = []
    probes = {}

    products = easee_api.api_get_optional(plugin, '/accounts/products')
    if isinstance(products, list):
        probes['accounts_products'] = len(products)
        for product in products:
            if not isinstance(product, dict):
                continue
            site_id = product.get('id')
            site_name = str(product.get('name') or product.get('siteName') or site_id or 'Site')
            added = _ingest_equalizer_items(plugin, 
                equalizers, seen, product.get('equalizers'), 'accounts-products',
                site_name=site_name, site_id=site_id,
            )
            if added:
                sources.append('accounts-products')
    else:
        probes['accounts_products'] = 'leeg of niet beschikbaar'

    sites = easee_api.api_get_optional(plugin, '/sites')
    if isinstance(sites, list):
        probes['sites'] = len(sites)
        for site in sites:
            if not isinstance(site, dict):
                continue
            site_id = site.get('id')
            site_name = str(site.get('name') or site.get('siteName') or site_id or 'Site')
            added = _ingest_equalizer_items(plugin, 
                equalizers, seen, site.get('equalizers'), 'sites-list',
                site_name=site_name, site_id=site_id,
            )
            if added:
                sources.append('sites-list')
            if site_id:
                detailed = easee_api.api_get_optional(plugin, f'/sites/{site_id}?detailed=true')
                if isinstance(detailed, dict):
                    added = _ingest_equalizer_items(plugin, 
                        equalizers, seen, detailed.get('equalizers'), 'sites-detailed',
                        site_name=site_name, site_id=site_id,
                    )
                    if added:
                        sources.append('sites-detailed')
                circuits = easee_api.api_get_optional(plugin, f'/sites/{site_id}/circuits')
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
                        if _append_equalizer(plugin, equalizers, seen, eq):
                            sources.append('sites-circuits')
    else:
        probes['sites'] = 'leeg of niet beschikbaar'

    list_data = easee_api.api_get_optional(plugin, '/equalizers')
    if isinstance(list_data, list):
        probes['equalizers_list'] = len(list_data)
        added = _ingest_equalizer_items(plugin, equalizers, seen, list_data, 'equalizers-list')
        if added:
            sources.append('equalizers-list')
    else:
        probes['equalizers_list'] = 'leeg of niet beschikbaar'

    if not equalizers and isinstance(sites, list):
        found = {}
        _scan_equalizers_in_object(plugin, sites, found)
        for eq in found.values():
            if _append_equalizer(plugin, equalizers, seen, eq):
                sources.append('sites-scan')

    manual_id = manual_equalizer_id(plugin)
    if manual_id and manual_id not in seen:
        eq = {
            'id': manual_id,
            'name': custom_equalizer_name(plugin) or 'Equalizer',
            'siteName': '',
            'source': 'manual-id',
        }
        if _append_equalizer(plugin, equalizers, seen, eq, ignore_filter=True):
            sources.append('manual-id')

    plugin.equalizer_probes = probes
    plugin.equalizer_source = ','.join(dict.fromkeys(sources)) if sources else 'none'
    equalizers = sorted({e['id']: e for e in equalizers}.values(), key=lambda x: x['id'])
    easee_logging.debug('equalizer_logic', f'Equalizer probes: {probes}', 'discovery')
    easee_logging.info('equalizer_logic', f'Equalizer discovery: {len(equalizers)} via {plugin.equalizer_source}', 'discovery')
    return equalizers

def poll_equalizer(plugin, equalizer):
    eid = equalizer['id']
    site_id = equalizer.get('siteId')
    values = {}
    for path in (f'/equalizers/{eid}', f'/equalizers/{eid}/state', f'/equalizers/{eid}/config'):
        data = easee_api.api_get_optional(plugin, path)
        if isinstance(data, dict):
            values.update(data)
            if not site_id:
                site_id = data.get('siteId')

    obs = easee_api.api_get_optional(plugin, f'/state/{eid}/observations?ids={OBSERVATION_KEYS["query_ids"]}')
    values.update(parse_equalizer_observations(plugin, obs))

    site_info = fetch_site_fuse_info(plugin, 
        site_id,
        circuit_id=equalizer.get('circuitId'),
        site_structure=values.get(ak.SITE_STRUCTURE_KEYS['root']),
        equalizer_values=values,
        equalizer_id=eid,
    )

    power_w = _import_power_w(plugin, values)
    export_w = _export_power_w(plugin, values)
    net_w = power_w - export_w

    online = values.get(EQUALIZER_KEYS['online'][0])
    if online is None:
        online = True
    load_bal = easee_helpers.first_dict_value(plugin, values, EQUALIZER_KEYS['load_balancing'])
    lb_active = easee_helpers.truthy(plugin, load_bal) if load_bal is not None else False
    max_alloc = easee_helpers.safe_float(plugin, site_info.get('emobility_a'), 0.0)
    emob_src = str(site_info.get('emobility_source', ''))
    site_emob_authoritative = (
        SITE_STATE_PATHS['site_state_mac'] in emob_src
        or emob_src.startswith('site.')
    )
    if max_alloc <= 0 or not site_emob_authoritative:
        eq_mac = easee_helpers.safe_float(plugin, values.get(FUSE_KEYS['emobility_primary']), 0.0)
        if eq_mac > 0 and not site_emob_authoritative:
            max_alloc = eq_mac if max_alloc <= 0 else max(max_alloc, eq_mac)
        elif max_alloc <= 0:
            max_alloc = easee_helpers.safe_float(plugin, values.get(FUSE_KEYS['allocated'][0]), 0.0)
    main_fuse_a = easee_helpers.safe_float(plugin, site_info.get('main_fuse_a'), 0.0)
    main_fuse_limit_a = easee_helpers.safe_float(plugin, site_info.get('main_fuse_limit_a'), 0.0)
    limit_src = str(site_info.get('main_fuse_limit_source', ''))

    log_equalizer_fuse_once(plugin, 
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
        lines.append(f'🔌 eMobility limiet: {easee_helpers.format_amp(plugin, max_alloc)}')
    else:
        lines.append('🔌 eMobility limiet: onbekend')
    if main_fuse_a > 0:
        lines.append(f'🏠 Hoofdzekering: {easee_helpers.format_amp(plugin, main_fuse_a)}')
    else:
        lines.append('🏠 Hoofdzekering: onbekend')
    if main_fuse_limit_a > 0:
        lines.append(f'⚡ Hoofdzekering limiet: {easee_helpers.format_amp(plugin, main_fuse_limit_a)}')
    else:
        lines.append('⚡ Hoofdzekering limiet: onbekend')
    max_import_kw = easee_helpers.safe_float(plugin, site_info.get('max_power_import_kw'), 0.0)
    max_import_a = easee_helpers.safe_float(plugin, site_info.get('max_power_import_a'), 0.0)
    if max_import_kw <= 0 and values.get(EQUALIZER_KEYS['max_power_import'][0]) is not None:
        raw_kw = easee_helpers.safe_float(plugin, values.get(EQUALIZER_KEYS['max_power_import'][0]), 0.0)
        if raw_kw > 0:
            max_import_kw = raw_kw / 1000.0 if raw_kw >= 100 else raw_kw
            power_w_mpi = easee_helpers.kw_to_watts(plugin, raw_kw)
            max_import_a = round(easee_helpers.amps_balanced_3phase_from_power(plugin, power_w_mpi))
    if max_import_kw > 0:
        kw_text = easee_helpers.format_kw(plugin, max_import_kw) or f'{max_import_kw:.1f} kW'
        amp_hint = f' (~{int(max_import_a)} A)' if max_import_a > 0 else ''
        lines.append(f'📈 Max import: {kw_text}{amp_hint}')
    current_line, _load_a = easee_helpers.actual_current_line(plugin, values, power_w)
    if current_line:
        lines.append(current_line)
    status_text = '\n'.join(lines)

    import_field = EQUALIZER_KEYS['cumulative_import'][0]
    export_field = EQUALIZER_KEYS['cumulative_export'][0]
    import_wh = _energy_wh_from_field(plugin, eid, values, import_field, 'import', power_w)
    export_wh = _energy_wh_from_field(plugin, eid, values, export_field, 'export', export_w)

    import_kwh = easee_helpers.kwh_value(plugin, values.get(import_field)) if import_field in values else None
    export_kwh = easee_helpers.kwh_value(plugin, values.get(export_field)) if export_field in values else None

    domoticz_devices.update_equalizer_energy(plugin, eid, 'Import', power_w, import_wh)
    domoticz_devices.update_equalizer_energy(plugin, eid, 'Teruglevering', export_w, export_wh)
    domoticz_devices.update_equalizer_text(plugin, eid, 'Netto', _netto_text(plugin, net_w, import_kwh, export_kwh))
    domoticz_devices.update_equalizer_text(plugin, eid, 'Spanning', _voltage_lines(plugin, values))
    domoticz_devices.update_equalizer_text(plugin, eid, 'Load balancing', _load_balancing_detail_text(plugin, values, lb_active))
    domoticz_devices.update_equalizer_text(plugin, eid, 'Status', status_text)

    plugin.latest_equalizers[eid] = {
        'power': power_w,
        'export': export_w,
        'net': net_w,
        'online': online,
        'loadbal': lb_active,
    }
