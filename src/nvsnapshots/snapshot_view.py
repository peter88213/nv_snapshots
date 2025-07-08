"""Provide a class for project collection management dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from tkinter import filedialog
from tkinter import ttk

from nvsnapshots.nvsnapshots_globals import FEATURE
from nvsnapshots.nvsnapshots_help import Nvsnapshotshelp
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS
from nvsnapshots.platform.platform_settings import MOUSE
from nvsnapshots.platform.platform_settings import PLATFORM
from nvlib.controller.sub_controller import SubController
from nvlib.gui.widgets.index_card import IndexCard
from nvlib.novx_globals import Error
from nvlib.novx_globals import norm_path
import tkinter as tk


class SnapshotView(tk.Toplevel, SubController):
    HEIGHT_BIAS = 20

    def __init__(self, model, view, controller, windowPosition, prefs):
        super().__init__()
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self.prefs = prefs
        windowSize = self.prefs['window_size'].split('+')[0]
        self.geometry(f"{windowSize}{windowPosition}")

        self.title(FEATURE)
        self.statusText = ''

        self.lift()
        self.focus()

        #--- Main menu.
        self._mainMenu = tk.Menu(self)
        self.config(menu=self._mainMenu)

        #--- Main window.
        self._mainWindow = ttk.Frame(self)
        self._mainWindow.pack(fill='both', padx=2, pady=2, expand=True)

        #--- Paned window displaying the tree and an "index card".
        self._treeWindow = ttk.Panedwindow(
            self._mainWindow,
            orient='horizontal',
        )
        self._treeWindow.pack(fill='both', expand=True)

        #--- Tree for snapshot selection.
        self._treeView = ttk.Treeview(self._treeWindow, selectmode='browse')
        scrollY = ttk.Scrollbar(
            self._treeView,
            orient='vertical',
            command=self._treeView.yview,
        )
        self._treeView.configure(yscrollcommand=scrollY.set)
        scrollY.pack(side='right', fill='y')
        self._treeView.pack(side='left')
        self._treeWindow.add(self._treeView)
        self._treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self._treeView.bind('<Delete>', self._remove_node)

        #--- "Index card" in the right frame.
        self._indexCard = IndexCard(self._treeWindow, bd=2, relief='ridge')
        self._indexCard.pack(side='right')
        self._treeWindow.add(self._indexCard)

        # Adjust the tree width.
        self._treeWindow.update()
        self._treeWindow.sashpos(0, self.prefs['tree_width'])

        #--- Add menu entries.
        # File menu.
        self._fileMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('File'),
            menu=self._fileMenu,
        )
        #--- Event bindings.
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        if PLATFORM != 'win':
            self.bind(KEYS.QUIT_PROGRAM[0], self.on_quit)
        self.bind(KEYS.OPEN_HELP[0], self._open_help)

        # Restore last window size.
        self.update_idletasks()
        self.geometry(f"{windowSize}{windowPosition}")

        self.isOpen = True

    def on_quit(self, event=None):
        self.prefs['tree_width'] = self._treeWindow.sashpos(0)
        self.prefs['window_size'] = self.winfo_geometry().split('+')[0]
        self.destroy()
        self.isOpen = False

    def _on_select_node(self, event=None):
        self._apply_changes()
        try:
            self.nodeId = self.tree.selection()[0]
            self.element = self.snapshots[self.nodeId]
        except IndexError:
            pass
        except AttributeError:
            pass
        else:
            self._set_element_view()

    def _open_help(self, event=None):
        Nvsnapshotshelp.open_help_page()

    def _remove_node(self, event=None):
        try:
            nodeId = self.tree.selection()[0]
        except IndexError:
            return

        try:
            if self._ui.ask_yes_no(
                message=_('Delete the selected snapshot?'),
                detail=self.snapshots[nodeId].title,
                title=FEATURE,
                parent=self,
            ):
                if self.tree.prev(nodeId):
                    self.tree.selection_set(
                        self.tree.prev(nodeId)
                    )
        except Error as ex:
            self._ui.set_status(str(ex))

    def _set_element_view(self, event=None):
        # View the selected element's title and description.
        self._indexCard.bodyBox.clear()
        if self.element.desc:
            self._indexCard.bodyBox.set_text(self.element.desc)
        if self.element.title:
            self._indexCard.title.set(self.element.title)

    def _set_title(self):
        if self.title:
            collectionTitle = self.title
        else:
            collectionTitle = _('Untitled collection')
        self.title(f'{collectionTitle} - {FEATURE}')

