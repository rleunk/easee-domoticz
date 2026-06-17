# -*- coding: utf-8 -*-
"""Expose Domoticz-injected globals to plugin submodules.

Submodules must access Devices, Images, and Parameters via this module
(for example domoticz_runtime.Parameters), not via a direct import, because
Domoticz injects those names into plugin.py after submodule import time.
"""

Devices = {}
Images = {}
Parameters = {}

def bind_plugin_globals(plugin_globals):
    """Copy Domoticz globals from plugin.py (injected at load) into this module."""
    global Devices, Images, Parameters
    if 'Devices' in plugin_globals:
        Devices = plugin_globals['Devices']
    if 'Images' in plugin_globals:
        Images = plugin_globals['Images']
    if 'Parameters' in plugin_globals:
        Parameters = plugin_globals['Parameters']
