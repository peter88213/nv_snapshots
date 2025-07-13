"""Provide a menu class for the snapshots manager.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvsnapshots.nvsnapshots_globals import icons
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS
import tkinter as tk


class NvsnapshotsMenu(tk.Menu):

    def __init__(self, master, cnf={}, **kw):
        super().__init__(master=master, cnf=cnf, **kw)

        # File menu.
        self._fileMenu = tk.Menu(self, tearoff=0)
        self.add_cascade(
            label=_('File'),
            menu=self._fileMenu,
        )
        self._fileMenu.add_command(
            label=_('Open Snapshot folder'),
            command=self._event('<<open_folder>>'),
        )
        self._fileMenu.add_command(
            label=_('Clean up Snapshot folder'),
            command=self._event('<<clean_up>>'),
        )
        self._fileMenu.add_separator()
        self._fileMenu.add_command(
            label=_('Snapshot'),
            accelerator=KEYS.MAKE_SNAPSHOT[1],
            image=icons.get('snapshot', None),
            compound='left',
            command=self._event('<<make_snapshot>>'),
        )
        self._fileMenu.add_separator()
        self._fileMenu.add_command(
            label=_('Remove'),
            accelerator=KEYS.DELETE[1],
            command=self._event('<<remove_snapshot>>'),
        )
        self._fileMenu.add_command(
            label=_('Revert'),
            command=self._event('<<revert>>'),
        )
        self._fileMenu.add_separator()
        self._fileMenu.add_command(
            label=_('Close'),
            accelerator=KEYS.QUIT_PROGRAM[1],
            command=self._event(KEYS.QUIT_PROGRAM[0]),
        )

        # Export menu.
        self._exportMenu = tk.Menu(self, tearoff=0)
        self.add_cascade(
            label=_('Export'),
            menu=self._exportMenu,
        )
        self._exportMenu.add_command(
            label=_('Manuscript'),
            command=self._event('<<export_manuscript>>'),
        )
        self._exportMenu.add_separator()
        self._exportMenu.add_command(
            label=_('Part descriptions'),
            command=self._event('<<export_parts>>'),
        )
        self._exportMenu.add_command(
            label=_('Chapter descriptions'),
            command=self._event('<<export_chapters>>'),
        )
        self._exportMenu.add_command(
            label=_('Section descriptions'),
            command=self._event('<<export_sections>>'),
        )
        self._exportMenu.add_separator()
        self._exportMenu.add_command(
            label=_('Story structure'),
            command=self._event('<<export_stages>>'),
        )
        self._exportMenu.add_command(
            label=_('Plot line descriptions'),
            command=self._event('<<export_plotlines>>'),
        )
        self._exportMenu.add_command(
            label=_('Plot grid'),
            command=self._event('<<export_grid>>'),
        )
        self._exportMenu.add_separator()
        self._exportMenu.add_command(
            label=_('Character descriptions'),
            command=self._event('<<export_characters>>'),
        )
        self._exportMenu.add_command(
            label=_('Location descriptions'),
            command=self._event('<<export_locations>>'),
        )
        self._exportMenu.add_command(
            label=_('Item descriptions'),
            command=self._event('<<export_items>>'),
        )
        self._exportMenu.add_separator()
        self._exportMenu.add_command(
            label=_('XML data files'),
            command=self._event('<<export_data>>'),
        )

        # Help menu.
        self._helpMenu = tk.Menu(self, tearoff=0)
        self.add_cascade(
            label=_('Help'),
            menu=self._helpMenu,
        )
        self._helpMenu.add_command(
            label=_('Online help'),
            accelerator=KEYS.OPEN_HELP[1],
            command=self._event('<<open_help>>'),
        )

    def _event(self, sequence):

        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)

        return callback

