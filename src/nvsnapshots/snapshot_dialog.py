"""Provide a class for a snapshot description dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshot
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from tkinter import ttk

from nvlib.gui.widgets.index_card import IndexCard
from nvlib.gui.widgets.modal_dialog import ModalDialog
from nvsnapshots.nvsnapshots_help import Nvsnapshotshelp
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS


class SnapshotDialog(ModalDialog):

    def __init__(self, view, service, **kw):
        super().__init__(view, **kw)
        self._ui = view
        self._service = service

        self.title(_('Snapshot description'))
        mainWindow = ttk.Frame(self)
        mainWindow.pack(
            fill='both',
            padx=5,
            pady=5
        )
        #--- "Index card" in the right frame.
        self._indexCard = IndexCard(mainWindow, bd=2, relief='ridge')
        self._indexCard.bodyBox['height'] = 13
        self._indexCard.bodyBox['width'] = 40
        self._indexCard.pack()

        buttons_frame = ttk.Frame(mainWindow)
        buttons_frame.pack(fill='both')

        # Button: Change backup directory.
        ttk.Button(
            buttons_frame,
            text=_('Ok'),
            command=self._set_description,
        ).pack(padx=5, pady=5, side='left')

        # Button: Cancel.
        ttk.Button(
            buttons_frame,
            text=_('Cancel'),
            command=self.destroy,
        ).pack(padx=5, pady=5, side='right')

        # "Help" button.
        ttk.Button(
            buttons_frame,
            text=_('Online help'),
            command=self._open_help
        ).pack(padx=5, pady=5, side='right')

        self.resizable(False, False)

        # Set Key bindings.
        self.bind(KEYS.OPEN_HELP[0], self._open_help)

    def _open_help(self, event=None):
        Nvsnapshotshelp.open_help_page()

    def _set_description(self, event=None):
        self._service.snapshotTitle = self._indexCard.title.get()
        self._service.snapshotComment = self._indexCard.bodyBox.get_text()
        self.destroy()
        self._ui.root.event_generate('<<save_snapshot>>')

