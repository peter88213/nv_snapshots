"""A project collection manager plugin for novelibre.

Requires Python 3.6+
Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

from nvsnapshots.nvsnapshots_locale import _
from nvlib.controller.plugin.plugin_base import PluginBase
from nvsnapshots.nvsnapshots_globals import FEATURE
from nvsnapshots.nvsnapshots_help import Nvsnapshotshelp
from nvsnapshots.platform.platform_settings import KEYS
from nvsnapshots.snapshot_service import SnapshotService
from pathlib import Path
import tkinter as tk


class Plugin(PluginBase):
    """novelibre snapshot manager plugin class."""
    VERSION = '@release'
    API_VERSION = '5.29'
    DESCRIPTION = 'A snapshot manager'
    URL = 'https://github.com/peter88213/nv_snapshots'

    def disable_menu(self):
        """Disable menu entries when no project is open.        
        
        Overrides the SubController method.
        """
        self._ui.fileMenu.entryconfig(_('Snapshot'), state='disabled')
        self._ui.toolsMenu.entryconfig(FEATURE, state='disabled')

    def enable_menu(self):
        """Enable menu entries when a project is open.
        
        Overrides the SubController method.
        """
        self._ui.fileMenu.entryconfig(_('Snapshot'), state='normal')
        self._ui.toolsMenu.entryconfig(FEATURE, state='normal')

    def install(self, model, view, controller):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        super().install(model, view, controller)
        self.snapshotService = SnapshotService(model, view, controller)
        self._icon = self._get_icon('snapshot.png')

        # Create an entry to the File menu.
        pos = self._ui.fileMenu.index(_('Save')) - 1
        self._ui.fileMenu.insert_separator(pos)
        pos += 1
        self._ui.fileMenu.insert_command(
            pos,
            label=_('Snapshot'),
            accelerator=KEYS.MAKE_SNAPSHOT[1],
            image=self._icon,
            compound='left',
            command=self.make_snapshot,
            state='disabled',
        )

        # Create an entry to the Tools menu.
        self._ui.toolsMenu.add_command(
            label=FEATURE,
            image=self._icon,
            compound='left',
            command=self.start_manager,
            state='disabled',
        )

        # Add an entry to the Help menu.
        self._ui.helpMenu.add_command(
            label=_('Snapshots plugin Online help'),
            image=self._icon,
            compound='left',
            command=self.open_help,
            )
        self._ui.root.bind(KEYS.MAKE_SNAPSHOT[0], self.make_snapshot)

    def on_close(self):
        self.snapshotService.on_quit()

    def on_quit(self):
        self.snapshotService.on_quit()

    def open_help(self, event=None):
        Nvsnapshotshelp.open_help_page()

    def start_manager(self):
        self.snapshotService.start_manager()

    def make_snapshot(self, event=None):
        self.snapshotService.make_snapshot()

    def _get_icon(self, fileName):
        # Return the icon for the main view.
        if self._ctrl.get_preferences().get('large_icons', False):
            size = 24
        else:
            size = 16
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            iconPath = f'{homeDir}/.novx/icons/{size}'
            icon = tk.PhotoImage(file=f'{iconPath}/{fileName}')
        except:
            icon = None
        return icon

