"""Provide a class for project collection management dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from datetime import datetime
from tkinter import ttk

from nvlib.controller.sub_controller import SubController
from nvlib.gui.widgets.index_card import IndexCard
from nvlib.novx_globals import STATUS
from nvsnapshots.nvsnapshots_globals import FEATURE
from nvsnapshots.nvsnapshots_globals import icons
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS
from nvsnapshots.platform.platform_settings import PLATFORM
import tkinter as tk


class SnapshotView(tk.Toplevel, SubController):

    _COLUMNS = {
        'id':('ID', 'id_width'),
        'title':(_('Title'), 'title_width'),
        'date':(_('Date'), 'date_width'),
        'words_used':(_('Words'), 'words_used_width'),
        'words_total':(_('With unused'), 'words_total_width'),
        'work_phase':(_('Work phase'), 'work_phase_width'),
    }

    def __init__(self, model, view, controller, prefs):
        super().__init__()
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self.prefs = prefs
        self.geometry(f"{self.prefs['window_geometry']}")

        self.title(FEATURE)
        self.statusText = ''

        self.lift()
        self.focus()

        #--- Main menu.
        self._mainMenu = tk.Menu(self)
        self.config(menu=self._mainMenu)

        #--- Main window.
        self._mainWindow = ttk.Frame(self)
        self._mainWindow.pack(
            fill='both',
            padx=2,
            pady=2,
            expand=True,
        )

        #--- Tree for snapshot selection.
        self._treeView = ttk.Treeview(
            self._mainWindow,
            columns=tuple(self._COLUMNS),
            show='headings',
            selectmode='browse',
        )
        scrollY = ttk.Scrollbar(
            self._treeView,
            orient='vertical',
            command=self._treeView.yview,
        )
        self._treeView.configure(yscrollcommand=scrollY.set)
        scrollY.pack(side='right', fill='y')
        self._treeView.pack(
            side='left',
            expand=True,
            fill='both',
        )
        self._treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        for colId in self._COLUMNS:
            colText, colWidth = self._COLUMNS[colId]
            self._treeView.column(
                colId,
                width=int(self.prefs.get(colWidth, 100)),
            )
            self._treeView.heading(
                colId,
                text=colText,
                anchor='w',
            )

        #--- "Index card" in the right frame.
        self._indexCard = IndexCard(
            self._mainWindow,
            bd=2,
            relief='ridge',
            width=prefs['right_frame_width'],
        )
        self._indexCard.pack(
            side='right',
            expand=False,
            fill='both',
        )
        self._indexCard.pack_propagate(0)

        #--- Add menu entries.
        # File menu.
        self._fileMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('File'),
            menu=self._fileMenu,
        )
        self._fileMenu.add_command(
            label=_('Open Snapshot folder'),
            command=self._event('<<open_folder>>'),
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
            command=self.on_quit,
        )

        # Help menu.
        self._helpMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('Help'),
            menu=self._helpMenu,
        )
        self._helpMenu.add_command(
            label=_('Online help'),
            accelerator=KEYS.OPEN_HELP[1],
            command=self._event('<<open_help>>'),
        )

        #--- Event bindings.
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        if PLATFORM != 'win':
            self.bind(KEYS.QUIT_PROGRAM[0], self.on_quit)
        self.bind(KEYS.MAKE_SNAPSHOT[0], self._event('<<make_snapshot>>'))
        self.bind(KEYS.OPEN_HELP[0], self._event('<<open_help>>'))
        self.bind(KEYS.DELETE[0], self._event('<<remove_snapshot>>'))

        self.isOpen = True
        self.element = {}

    def disable_menu(self):
        self._mainMenu.entryconfig(_('File'), state='disabled')

    def enable_menu(self):
        self._mainMenu.entryconfig(_('File'), state='normal')

    def get_selection(self):
        try:
            nodeId = self._treeView.selection()[0]
        except IndexError:
            return None
        else:
            return nodeId

    def reset_tree(self):
        for node in self._treeView.get_children(''):
            self._treeView.delete(node)

    def build_tree(self):
        self.reset_tree()
        for snapshotId in self.snapshots:
            try:
                displayDate = datetime.fromisoformat(
                    self.snapshots[snapshotId]['date']
                ).strftime('%c')
                status = self.snapshots[snapshotId]['work phase']
                if status is not None:
                    workPhase = STATUS[status]
                else:
                    workPhase = _('Undefined')
            except:
                displayDate = self.snapshots[snapshotId]['date']
            columns = [
                snapshotId,
                self.snapshots[snapshotId]['title'],
                displayDate,
                self.snapshots[snapshotId]['words used'],
                self.snapshots[snapshotId]['words total'],
                workPhase,
            ]
            self._treeView.insert(
                '',
                'end',
                snapshotId,
                values=columns,
            )
        self._indexCard.bodyBox.config(state='normal')
        self._indexCard.bodyBox.clear()
        self._indexCard.bodyBox.config(state='disabled')
        self._indexCard.titleEntry.config(state='normal')
        self._indexCard.title.set('')
        self._indexCard.titleEntry.config(state='disabled')

    def on_quit(self, event=None):
        self.update_idletasks()
        self.prefs['window_geometry'] = self.winfo_geometry()
        for i, colId in enumerate(self._COLUMNS):
            width = self._COLUMNS[colId][1]
            self.prefs[width] = self._treeView.column(i, 'width')
        self.destroy()
        self.isOpen = False

    def _event(self, sequence):

        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)

        return callback

    def _on_select_node(self, event=None):
        try:
            self.nodeId = self._treeView.selection()[0]
        except IndexError:
            return

        self.element = self.snapshots[self.nodeId]
        self._set_element_view()

    def _set_element_view(self, event=None):
        # View the selected element's title and description.
        self._indexCard.bodyBox.config(state='normal')
        self._indexCard.bodyBox.clear()
        self._indexCard.bodyBox.set_text(self.element.get('description', ''))
        self._indexCard.bodyBox.config(state='disabled')
        self._indexCard.titleEntry.config(state='normal')
        self._indexCard.title.set(self.element.get('title', ''))
        self._indexCard.titleEntry.config(state='disabled')

