# -*- coding: utf-8 -*-
"""Central logging for the Easee Domoticz plugin."""

import Domoticz
import domoticz_runtime
from easee_constants import PLUGIN_VERSION, ULTRA_DEBUG


def _format(level, module, context, message):
    ctx = f'[{context}]' if context else ''
    return f'[Easee v{PLUGIN_VERSION}][{level}][{module}]{ctx} {message}'


def is_debug_enabled():
    if ULTRA_DEBUG:
        return True
    return domoticz_runtime.Parameters.get('Mode6') == 'Debug'


def debug(module, message, context=''):
    if not is_debug_enabled():
        return
    Domoticz.Debug(_format('DEBUG', module, context, message))


def info(module, message, context=''):
    Domoticz.Log(_format('INFO', module, context, message))


def warning(module, message, context=''):
    Domoticz.Log(f'⚠ {_format("WARNING", module, context, message)}')


def error(module, message, context=''):
    Domoticz.Error(_format('ERROR', module, context, message))
