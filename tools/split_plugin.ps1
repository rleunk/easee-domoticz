# Split plugin.py into modules (refactor helper)
$ErrorActionPreference = 'Stop'
$Root = 'C:\Users\Richard\Downloads\easee-domoticz'
$PluginPath = Join-Path $Root 'plugin.py'
$src = Get-Content -Path $PluginPath -Raw -Encoding UTF8
$lines = $src -split "`r?`n"

function Get-Methods {
    param([string[]]$Lines)
    $methods = @{}
    $i = 0
    while ($i -lt $Lines.Count) {
        $line = $Lines[$i]
        if ($line -match '^    def (?<name>[a-zA-Z_][a-zA-Z0-9_]*)\((?<methodArgs>[^)]*)\):\s*(?<inline>.*)$') {
            $name = $Matches['name']
            $methodArgs = $Matches['methodArgs'].Trim()
            $inline = $Matches['inline'].Trim()
            $bodyLines = @()
            if ($inline) {
                $bodyLines += "        $inline"
            }
            $i++
            while ($i -lt $Lines.Count) {
                $line = $Lines[$i]
                if ($line -match '^    def [a-zA-Z_]') { break }
                if ($line -match '^class ') { break }
                if ($line -match '^_plugin = ') { break }
                if ($line -match '^def on(Start|Stop|Heartbeat)') { break }
                $bodyLines += $line
                $i++
            }
            $methods[$name] = @{
                MethodArgs = $methodArgs
                Body = ($bodyLines -join "`n").TrimEnd()
            }
            continue
        }
        $i++
    }
    return $methods
}

function StripSelfArg([string]$methodArgs) {
    if (-not $methodArgs) { return '' }
    $a = $methodArgs.Trim()
    if ($a -eq 'self') { return '' }
    if ($a.StartsWith('self,')) { return $a.Substring(5).Trim() }
    if ($a.StartsWith('self ,')) { return $a.Substring(6).Trim() }
    return $a
}

function Convert-BodyToModule($body) {
    if (-not $body) { return '' }
    $out = ($body -split "`r?`n") | ForEach-Object {
        if ($_ -match '^        (.*)$') { "    $($Matches[1])" }
        elseif ($_ -eq '    ') { '' }
        elseif ($_ -eq '') { '' }
        else { $_ }
    }
    $text = ($out -join "`n") -replace '\bself\.', 'plugin.'
    return $text.TrimEnd()
}

function Make-ModuleFunction($name, $methodArgs, $body) {
    $fnArgs = StripSelfArg $methodArgs
    if ($fnArgs) { $sig = "def $name(plugin, $fnArgs):" } else { $sig = "def $name(plugin):" }
    if ($body) { return "$sig`n$body" }
    return "$sig`n    pass"
}

$methods = Get-Methods -Lines $lines
Write-Host "Found $($methods.Count) methods"

$moduleMap = [ordered]@{
    'easee_helpers.py' = @(
        'norm','prefix','extra_charger_names','pref','clean_label','safe_float','safe_int','truthy','euro_str',
        'power_watts','kwh_value','wh_from_kwh','poll_interval_sec','short_id','parse_iso','tibber_token','tibber_enabled',
        'kw_to_watts','format_amp','current_from_power_3phase','amps_balanced_3phase_from_power','phase_currents_from_values',
        'format_phase_amp','actual_current_line','format_kw','first_dict_value'
    )
    'easee_api.py' = @('login','refresh','api_get','api_get_optional')
    'easee_state.py' = @('state_path','load_state','save_state','today_key','now_ts','charger_state')
    'tibber_pricing.py' = @('tibber_query','refresh_tibber_prices','current_tibber_price','price_status_emoji','cheapest_window_text','price_emoji')
    'domoticz_icons.py' = @('image_root','icon_base','_icon_images_key','_collect_image_ids','_try_create_icon_zip','load_custom_images','apply_images_to_devices')
    'domoticz_devices.py' = @(
        'make_charger_device_id','make_equalizer_device_id','make_device_id',
        'rebuild_index','find_unit','find_unit_by_devid','resolve_unit','resolve_charger_unit','resolve_equalizer_unit',
        'resolve_core_unit','sync_device_name','next_free_unit',
        'ensure_device_once','update_core_text','update_core_custom','update_core_energy','update_core_sw',
        'update_text','update_custom','update_energy','update_sw',
        'update_charger_text','update_charger_custom','update_charger_costs','update_charger_energy',
        'update_equalizer_text','update_equalizer_energy',
        'ensure_core_devices','ensure_charger_devices','ensure_equalizer_devices'
    )
    'charger_logic.py' = @(
        'session_energy_kwh','power_integrated_kwh','custom_charger_name','charger_display_name','charger_dev_name',
        'op_mode_label','power_emoji','status_emoji','compute_duration_text','discover_chargers','poll_charger'
    )
    'equalizer_logic.py' = @(
        'amp_value','is_same_as_main_fuse','fuse_limit_keys','emobility_keys','offline_circuit_current_keys',
        'is_offline_circuit_current_key','main_fuse_keys','is_fuse_limit_key','is_main_limit_key','is_emobility_key',
        'fuse_limit_from_dict','emobility_from_dict','root_circuit_ids','_unique_circuits','fuse_limit_from_circuits',
        'fuse_limit_from_circuit_states','parse_site_structure_json','deep_scan_amp_keys','deep_scan_amp_range',
        'is_valid_fuse_limit','pick_best_fuse_candidate','add_fuse_candidate','note_raw_fuse_value',
        'collect_fuse_from_circuits_list','fetch_root_circuit_details','collect_fuse_from_dict','scan_any_fuse_keys',
        'collect_fuse_from_circuit_settings','collect_fuse_from_equalizer_circuit','collect_explicit_circuit_fuses',
        'collect_fuse_from_cloud_loadbalancing','root_circuit_fuse','select_main_fuse_limit','collect_json_key_tree',
        'log_site_structure_once','collect_numeric_values','log_site_structure_numerics_once','log_equalizer_fuse_once',
        'fuse_limit_from_deep_scan','collect_fuse_debug','structure_top_keys','fuse_limit_from_site_structure',
        'emobility_from_site_structure','fuse_limit_from_equalizer_values','fuse_limit_from_products','set_emobility',
        'log_fuse_probe_debug','fetch_site_fuse_info','parse_equalizer_observations',
        'custom_equalizer_name','manual_equalizer_id','equalizer_display_name','equalizer_dev_name',
        '_equalizer_matches_filter','_append_equalizer','_scan_equalizers_in_object','_ingest_equalizer_items',
        'discover_equalizers','poll_equalizer'
    )
}

$moduleImports = @{
    'easee_helpers.py' = @('import math','from datetime import datetime','import hashlib','import Domoticz')
    'easee_api.py' = @('import Domoticz','from easee_constants import BASE_URL, LOGIN_URL, REFRESH_URL')
    'easee_state.py' = @('import os, json, time','from datetime import datetime','from easee_constants import STATE_FILE')
    'tibber_pricing.py' = @('from datetime import datetime','import Domoticz','from easee_constants import TIBBER_GQL')
    'domoticz_icons.py' = @('import os','import Domoticz','from easee_constants import PLUGIN_KEY, CORE_DEVICE_IDS')
    'domoticz_devices.py' = @('import hashlib','import Domoticz','from easee_constants import DEVICE_TYPES, CORE_DEVICE_IDS, ULTRA_DEBUG')
    'charger_logic.py' = @('import Domoticz','from easee_constants import OP_MODE_LABELS')
    'equalizer_logic.py' = @('import json, math','import Domoticz')
}

foreach ($mod in $moduleMap.Keys) {
    $parts = @('# -*- coding: utf-8 -*-', '')
    if ($moduleImports[$mod]) { $parts += $moduleImports[$mod]; $parts += '' }
    foreach ($m in $moduleMap[$mod]) {
        if (-not $methods.ContainsKey($m)) { throw "Missing method $m for $mod" }
        $info = $methods[$m]
        $body = Convert-BodyToModule $info.Body
        $parts += (Make-ModuleFunction $m $info.MethodArgs $body)
        $parts += ''
    }
    $outPath = Join-Path $Root $mod
    [System.IO.File]::WriteAllText($outPath, (($parts -join "`n").TrimEnd() + "`n"))
    Write-Host "Wrote $mod ($((Get-Content $outPath).Count) lines)"
}

$const = @'
# -*- coding: utf-8 -*-

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
'@
[System.IO.File]::WriteAllText((Join-Path $Root 'easee_constants.py'), $const)

$pluginMethods = @{
    'easee_helpers' = $moduleMap['easee_helpers.py']
    'easee_api' = $moduleMap['easee_api.py']
    'easee_state' = $moduleMap['easee_state.py']
    'tibber_pricing' = $moduleMap['tibber_pricing.py']
    'domoticz_icons' = $moduleMap['domoticz_icons.py']
    'domoticz_devices' = $moduleMap['domoticz_devices.py']
    'charger_logic' = $moduleMap['charger_logic.py']
    'equalizer_logic' = $moduleMap['equalizer_logic.py']
}

$logMethods = @('log','debug','error')
$orchestrationMethods = @('discover_entities','initial_sync','refresh_entity_cache_only','write_debug','poll_all','update_combined','onStart','onStop','onHeartbeat')

$headerEnd = 0
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^import ') { $headerEnd = $i; break }
}
$xmlHeader = ($lines[0..($headerEnd-1)] -join "`n")

$initBody = ($methods['__init__'].Body -split "`r?`n") | ForEach-Object { $_ }
$initText = "    def __init__(self):`n" + ($initBody -join "`n")

$bindLines = @()
foreach ($modName in @('equalizer_logic','charger_logic','easee_api','tibber_pricing','domoticz_devices','domoticz_icons','easee_state','easee_helpers')) {
    foreach ($m in $pluginMethods[$modName]) {
        $bindLines += "    def $m(self, *args, **kwargs): return ${modName}.$m(self, *args, **kwargs)"
    }
}

function Format-PluginMethods($names) {
    $out = @()
    foreach ($m in $names) {
        $info = $methods[$m]
        $fnArgs = StripSelfArg $info.MethodArgs
        if ($fnArgs) { $sig = "    def $m(self, $fnArgs):" } else { $sig = "    def $m(self):" }
        $out += $sig
        if ($info.Body) { $out += ($info.Body -split "`r?`n") }
        $out += ''
    }
    return $out
}
$logFns = Format-PluginMethods $logMethods
$orchFns = Format-PluginMethods $orchestrationMethods

$pluginContent = @"
$xmlHeader

import Domoticz
import os, json, time
try:
    import requests
except Exception:
    requests = None

import easee_helpers
import easee_api
import easee_state
import tibber_pricing
import domoticz_icons
import domoticz_devices
import charger_logic
import equalizer_logic
from easee_constants import ULTRA_DEBUG

class BasePlugin:
$initText

    # ---- logging ----
$($logFns -join "`n")

$($bindLines -join "`n")

    # ---- orchestration ----
$($orchFns -join "`n")

_plugin = BasePlugin()

def onStart(): _plugin.onStart()
def onStop(): _plugin.onStop()
def onHeartbeat(): _plugin.onHeartbeat()
"@

[System.IO.File]::WriteAllText((Join-Path $Root 'plugin.py'), $pluginContent)
Write-Host 'Wrote plugin.py'
