"""Provide global variables and functions.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os

from nvsnapshots.nvsnapshots_locale import _
from nvlib.novx_globals import norm_path
from nvsnapshots.platform.platform_settings import PLATFORM

FEATURE = _('Snapshots')

icons = {
    'snapshot': None,
}


def open_document(document):
    """Open a document with the operating system's standard application."""
    if PLATFORM == 'win':
        os.startfile(norm_path(document))
        return

    if PLATFORM == 'ix':
        os.system('xdg-open "%s"' % norm_path(document))
        return

    if PLATFORM == 'mac':
        os.system('open "%s"' % norm_path(document))
