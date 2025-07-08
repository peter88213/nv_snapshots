"""Provide a class with key definitions for the Mac OS.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvsnapshots.platform.generic_keys import GenericKeys


class MacKeys(GenericKeys):

    QUIT_PROGRAM = ('<Command-q>', 'Cmd-Q')
    MAKE_SNAPSHOT = ('<Command-Alt-s>', 'Cmd-Alt-S')
