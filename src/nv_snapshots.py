"""A project collection manager plugin for novelibre.

Requires Python 3.7+
Copyright (c) 2025-2026 Peter Triesberger
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
from nvsnapshots.nvsnapshots_globals import HELP_PAGE
from nvsnapshots.platform.platform_settings import KEYS
from nvsnapshots.snapshot_service import SnapshotService
from nvsnapshots.nvsnapshots_globals import icons


class Plugin(PluginBase):
    """novelibre snapshot manager plugin class."""
    VERSION = '@release'
    API_VERSION = '5.63'
    DESCRIPTION = 'A snapshot manager'
    URL = 'https://github.com/peter88213/nv_snapshots'
    HELP_PAGE = HELP_PAGE

    def disable_menu(self):
        self.snapshotService.disable_menu()

    def enable_menu(self):
        self.snapshotService.enable_menu()

    def install(self, model, view, controller):
        """Install the plugin at runtime.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        super().install(model, view, controller)
        self.snapshotService = SnapshotService(model, view, controller)
        icons['snapshot'] = self._icon = self._get_icon('snapshot.png')

        #--- Configure the user interface.

        # Add an entry to the File menu.
        pos = self._ui.fileMenu.index(_('Save')) - 1
        self._ui.fileMenu.insert_separator(pos)
        pos += 1

        label = _('Snapshot')
        self._ui.fileMenu.insert_command(
            pos,
            label=label,
            accelerator=KEYS.MAKE_SNAPSHOT[1],
            image=self._icon,
            compound='left',
            command=self.snapshotService.make_snapshot,
            state='disabled',
        )
        self._ui.fileMenu.disableOnClose.append(label)

        # Create an entry to the Tools menu.
        label = FEATURE
        self._ui.toolsMenu.add_command(
            label=label,
            image=self._icon,
            compound='left',
            command=self.snapshotService.start_manager,
            state='disabled',
        )
        self._ui.toolsMenu.disableOnClose.append(label)

        self._add_help_menu_entry(_('Snapshots plugin help'))

        # Hotkey to create a snapshot.
        self._ui.root.bind(
            KEYS.MAKE_SNAPSHOT[0],
            self.snapshotService.make_snapshot
        )

    def on_close(self):
        """Actions to be performed before a project is closed."""
        self.snapshotService.on_close()

    def on_open(self):
        """Actions to be performed after a project is opened."""
        self.snapshotService.refresh()

    def on_quit(self):
        """Actions to be performed before the application is closed."""
        self.snapshotService.on_quit()

