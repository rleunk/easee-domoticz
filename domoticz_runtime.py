# -*- coding: utf-8 -*-
"""Expose Domoticz-injected globals to plugin submodules."""

try:
    from Domoticz import Devices, Images, Parameters
except ImportError:
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
