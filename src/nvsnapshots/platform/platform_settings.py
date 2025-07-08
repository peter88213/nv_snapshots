"""Provide platform specific key definitions for the nv_snapshots plugin.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import platform

from nvsnapshots.platform.generic_keys import GenericKeys
from nvsnapshots.platform.generic_mouse import GenericMouse
from nvsnapshots.platform.mac_keys import MacKeys
from nvsnapshots.platform.windows_keys import WindowsKeys

if platform.system() == 'Windows':
    PLATFORM = 'win'
    KEYS = WindowsKeys()
    MOUSE = GenericMouse
elif platform.system() in ('Linux', 'FreeBSD'):
    PLATFORM = 'ix'
    KEYS = GenericKeys()
    MOUSE = GenericMouse
elif platform.system() == 'Darwin':
    PLATFORM = 'mac'
    KEYS = MacKeys()
    MOUSE = GenericMouse
else:
    PLATFORM = ''
    KEYS = GenericKeys()
    MOUSE = GenericMouse

