"""Provide a service class for the collection management.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import zipfile

from nvlib.controller.sub_controller import SubController
from nvlib.novx_globals import Error
from nvlib.novx_globals import Notification
from nvlib.novx_globals import norm_path
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.snapshot_view import SnapshotView
import tkinter as tk
from tlv.tlv_helper import from_timestamp


class SnapshotService(SubController):
    INI_FILENAME = 'snapshots.ini'
    INI_FILEPATH = '.novx/config'
    SETTINGS = dict(
        last_open='',
        tree_width='260',
        window_size='600x300',
        snapshot_subdir='Snapshots',
    )
    OPTIONS = {}
    ICON = 'snapshot'

    ZIP_EXTENSION = '.zip'
    DESC_EXTENSION = '.txt'

    def __init__(self, model, view, controller):
        self._mdl = model
        self._ui = view
        self._ctrl = controller

        #--- Load configuration.
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/{self.INI_FILEPATH}'
        except:
            configDir = '.'
        self.iniFile = f'{configDir}/{self.INI_FILENAME}'
        self.configuration = self._mdl.nvService.new_configuration(
            settings=self.SETTINGS,
            options=self.OPTIONS
        )
        # self.configuration.read(self.iniFile)
        self.prefs = {}
        self.prefs.update(self.configuration.settings)
        self.prefs.update(self.configuration.options)

        # Set window icon.
        try:
            path = os.path.dirname(sys.argv[0])
            if not path:
                path = '.'
            self.icon = tk.PhotoImage(file=f'{path}/icons/{self.ICON}.png')
        except:
            self.icon = None

        self.snapshotView = None

    def make_snapshot(self):
        self._ui.restore_status()
        self._ui.propertiesView.apply_changes()
        if self._mdl.prjFile is None:
            return

        if self._mdl.prjFile.filePath is None:
            if not self._ctrl.save_project():
                return

        if self._mdl.isModified:
            if self._ui.ask_yes_no(
                message=_('Save changes?')
            ):
                self._ctrl.save_project()
            else:
                # Do not generate a snapshot from an unsaved project.
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return

        #--- Make sure that a project snapshot subdirectory exists.
        projectDir, projectFile = os.path.split(self._mdl.prjFile.filePath)
        snapshotDir = os.path.join(
            projectDir,
            self.prefs['snapshot_subdir']
        )
        os.makedirs(snapshotDir, exist_ok=True)

        prjName, __ = os.path.splitext(projectFile)
        prjFileTimestamp = os.path.getmtime(self._mdl.prjFile.filePath)
        prjFileDate = (datetime.fromtimestamp(prjFileTimestamp))
        isoDate = prjFileDate.replace(microsecond=0).isoformat()
        snapshotId = f"{prjName}.{isoDate.replace(':', '.')}"
        title, desc = self._get_snapshot_description()
        wordCount, totalCount = self._mdl.prjFile.count_words()
        snapshotMetadata = {
            snapshotId: {
                'title': title,
                'description': desc,
                'date': isoDate,
                'work phase': self._mdl.novel.workPhase,
                'words used': wordCount,
                'words total':totalCount,
            }
        }

        #--- Write the snapshot.
        zipPath = os.path.join(
            snapshotDir,
            f'{snapshotId}{self.ZIP_EXTENSION}'
        )
        try:
            with zipfile.ZipFile(zipPath, 'w') as z:

                # Write project file.
                z.write(
                    self._mdl.prjFile.filePath,
                    arcname=projectFile,
                    compress_type=zipfile.ZIP_DEFLATED,
                )

                # Write descriptive text file.
                z.writestr(
                    f'{self._sanitize_filename(title)}{self.DESC_EXTENSION}',
                    f'{title}\n\n{desc}',
                    compress_type=zipfile.ZIP_DEFLATED,
                )

                # Write JSON metadata file.
                z.writestr(
                    'meta.json',
                    json.dumps(snapshotMetadata),
                    compress_type=zipfile.ZIP_DEFLATED,
                )

        except Exception as ex:
            message = f'!{_("Snapshot failed")}: {str(ex)}'
        else:
            message = f'{_("Snapshot generated")} ({isoDate})'
        self._ui.set_status(message)

    def on_quit(self):
        """Write back the configuration file.
        
        Overrides the superclass method.
        """
        if self.snapshotView:
            if self.snapshotView.isOpen:
                self.snapshotView.on_quit()

        #--- Save configuration
        for keyword in self.prefs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self.prefs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self.prefs[keyword]
        # self.configuration.write(self.iniFile)

    def start_manager(self):

        if self.snapshotView:
            if self.snapshotView.isOpen:
                if self.snapshotView.state() == 'iconic':
                    self.snapshotView.state('normal')
                self.snapshotView.lift()
                self.snapshotView.focus()
                return

        __, x, y = self._ui.root.geometry().split('+')
        offset = 100
        windowPosition = f'+{int(x)+offset}+{int(y)+offset}'
        self.snapshotView = SnapshotView(
            self._mdl,
            self._ui,
            self._ctrl,
            windowPosition,
            self.prefs,
        )
        if self.icon:
            self.snapshotView.iconphoto(False, self.icon)

    def _create_document(self, sourcePath, suffix, **kwargs):
        """Create a document from any novx file.
        
        Positional arguments: 
            sourcePath: str -- path to a novx file other than the 
                               project file. 
            suffix: str -- Target file name suffix.

        Keyword arguments:
            filter: str -- element ID for filtering chapters and sections.
            show: Boolean -- If True, open the created document 
                             after creation.
            ask: Boolean -- If True, ask before opening 
                            the created document.
            overwrite: Boolean -- Overwrite existing files 
                                  without confirmation.
            doNotExport: Boolean -- Open existing, if any. Do not export.
        """
        self._ui.restore_status()
        if not os.path.isfile(sourcePath):
            self._ui.set_status(
                (
                    f'!{_("File not found")}: '
                    f'"{norm_path(sourcePath)}".'
                )
            )
            return

        __, extension = os.path.splitext(sourcePath)
        if extension == self._mdl.nvService.get_novx_file_extension():
            novxFile = self._mdl.nvService.new_novx_file(sourcePath)
        elif extension == self._mdl.nvService.get_zipped_novx_file_extension():
            novxFile = self._mdl.nvService.new_zipped_novx_file(sourcePath)
        else:
            self._ui.set_status(f'!{_("File type is not supported")}.')
            return

        novxFile.novel = self._mdl.nvService.new_novel()
        try:
            novxFile.read()
            self._ui.set_status(
                self._ctrl.fileManager.exporter.run(
                    novxFile,
                    suffix,
                )
            )
        except Notification as ex:
            self._ui.set_status(f'#{str(ex)}')
        except Error as ex:
            self._ui.set_status(f'!{str(ex)}')

    def _get_snapshot_description(self):
        title = 'Undocumented snapshot'
        desc = ''
        return title, desc

    def _sanitize_filename(self, filename):
        # Return filename with disallowed characters removed.
        return re.sub(r'[\\|\/|\:|\*|\?|\"|\<|\>|\|]+', '', filename)
