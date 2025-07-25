"""Provide a service class for the help function.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import webbrowser

from nvsnapshots.nvsnapshots_locale import _


class Nvsnapshotshelp:

    HELP_URL = f'{_("https://peter88213.github.io/nvhelp-en")}/nv_snapshots/'

    @classmethod
    def open_help_page(cls):
        """Show the online help page specified by page."""
        webbrowser.open(cls.HELP_URL)

