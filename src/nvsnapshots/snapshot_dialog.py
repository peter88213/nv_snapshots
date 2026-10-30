"""Provide a class for a snapshot description dialog.

Copyright (c) 2025-2026 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshot
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from tkinter import ttk

from nvlib.gui.widgets.index_card import IndexCard
from nvlib.gui.widgets.modal_dialog import ModalDialog
from nvsnapshots.nvsnapshots_globals import HELP_PAGE
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS
import tkinter as tk


class SnapshotDialog(ModalDialog):

    def __init__(self, view, controller, service, **kw):
        super().__init__(view, **kw)
        self._ui = view
        self._ctrl = controller
        self._service = service

        self.title(_('Snapshot description'))

        # "Index card".
        prefs = self._ctrl.get_preferences()
        self._indexCard = IndexCard(
            self,
            bd=2,
            fg=prefs['color_text_fg'],
            bg=prefs['color_text_bg'],
            relief='ridge'
        )
        self._indexCard.bodyBox['height'] = 13
        self._indexCard.bodyBox['width'] = 40
        self._indexCard.pack()

        footer = tk.Frame(self)
        footer.pack(fill='both')

        # Button: Change backup directory.
        ttk.Button(
            footer,
            text=_('Ok'),
            command=self._set_description,
        ).pack(padx=5, pady=5, side='left')

        # Button: Cancel.
        ttk.Button(
            footer,
            text=_('Cancel'),
            command=self.destroy,
        ).pack(padx=5, pady=5, side='right')

        # "Help" button.
        ttk.Button(
            footer,
            text=_('Help'),
            command=self._open_help
        ).pack(padx=5, pady=5, side='right')

        # Set Key bindings.
        self.bind(KEYS.OPEN_HELP[0], self._open_help)

    def _open_help(self, event=None):
        self._ctrl.open_help(page=HELP_PAGE)

    def _set_description(self, event=None):
        snapshotTitle = self._indexCard.title.get()
        if not snapshotTitle:
            snapshotTitle = _('Undefined')
        self._service.snapshotTitle = snapshotTitle
        snapshotComment = self._indexCard.bodyBox.get_text()
        if snapshotComment is None:
            snapshotComment = ''
        self._service.snapshotComment = snapshotComment
        self.destroy()
        self._ui.root.event_generate('<<save_snapshot>>')

