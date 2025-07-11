"""Provide a service class for the collection management.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_snapshots
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from datetime import datetime
import glob
import json
import os
from pathlib import Path
import re
import sys
import zipfile

from nvlib.controller.sub_controller import SubController
from nvlib.novx_globals import Notification
from nvlib.novx_globals import norm_path
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.snapshot_view import SnapshotView
import tkinter as tk
from nvsnapshots.nvsnapshots_help import Nvsnapshotshelp
from nvsnapshots.snapshot_dialog import SnapshotDialog
from nvsnapshots.nvsnapshots_globals import FEATURE
from nvlib.model.file.doc_open import open_document


class SnapshotService(SubController):
    INI_FILENAME = 'snapshots.ini'
    INI_FILEPATH = '.novx/config'
    SETTINGS = dict(
        tree_width='260',
        window_geometry='600x300',
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
        self.configuration.read(self.iniFile)
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
        self.prjSnapshots = {}

        self._snapshotId = None
        self._isoDate = None
        self._prjFile = None
        self._prjDir = None
        self._zipPath = None

        self._ui.root.bind('<<save_snapshot>>', self._save_snapshot)
        self.snapshotTitle = None
        self.snapshotComment = None

    def disable_menu(self):
        self.snapshotView.disable_menu()

    def enable_menu(self):
        self.snapshotView.enable_menu()

    def make_snapshot(self, doNotAsk=False, event=None):
        self._ui.restore_status()
        self._ui.propertiesView.apply_changes()
        if self._mdl.prjFile is None:
            return

        if self._mdl.prjFile.filePath is None:
            if not self._ctrl.save_project():
                return

        if self._mdl.isModified:
            if doNotAsk or self._ui.ask_yes_no(
                message=_('Save changes?')
            ):
                self._ctrl.save_project()
            else:
                # Do not generate a snapshot from an unsaved project.
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return

        #--- Make sure that a project snapshot subdirectory exists.
        os.makedirs(self._get_snapshot_dir(), exist_ok=True)

        #--- Check whether the snapshot already exists.
        self._initialize_snapshot()
        if os.path.isfile(self._zipPath):
            self._ui.set_status(f'#{_("Snapshot already exists")}.')
            return

        #--- Open a dialog for title/comment input.
        SnapshotDialog(self._ui, self)

    def on_close(self):
        self.prjSnapshots.clear()
        self.snapshotView.reset_tree()

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
        self.configuration.write(self.iniFile)

    def refresh(self):
        self._collect_snapshots()
        if self.snapshotView:
            self.snapshotView.snapshots = self.prjSnapshots
            self.snapshotView.build_tree()

    def start_manager(self):

        if self.snapshotView:
            if self.snapshotView.isOpen:
                if self.snapshotView.state() == 'iconic':
                    self.snapshotView.state('normal')
                self.snapshotView.lift()
                self.snapshotView.focus()
                return

        self.snapshotView = SnapshotView(
            self._mdl,
            self._ui,
            self._ctrl,
            self.prefs,
        )
        if self.icon:
            self.snapshotView.iconphoto(False, self.icon)

        self._bind_events()
        self.refresh()

    def _bind_events(self):
        event_callbacks = {
            '<<make_snapshot>>': self.make_snapshot,
            '<<open_help>>': self._open_help,
            '<<remove_snapshot>>': self._remove_snapshot,
            '<<revert>>': self._revert,
            '<<open_folder>>': self._open_folder,
        }
        for sequence, callback in event_callbacks.items():
            self.snapshotView.master.winfo_toplevel().bind(sequence, callback)

    def _collect_snapshots(self):
        projectDir, projectFile = os.path.split(self._mdl.prjFile.filePath)
        snapshotDir = os.path.join(
            projectDir,
            self.prefs['snapshot_subdir']
        )
        if not os.path.isdir(snapshotDir):
            return

        self.prjSnapshots.clear()
        prjName, __ = os.path.splitext(projectFile)
        pattern = f'{prjName}.*{self.ZIP_EXTENSION}'
        prjSnapshotFiles = glob.glob(
            pattern,
            root_dir=snapshotDir,
        )
        prjSnapshotFiles.sort()
        if not prjSnapshotFiles:
            return

        for snapshotFile in prjSnapshotFiles:
            zipPath = os.path.join(snapshotDir, snapshotFile)
            try:
                with zipfile.ZipFile(zipPath, 'r') as z:
                    with z.open('meta.json', 'r') as f:
                        metadata = json.loads(f.read())
            except:
                pass
            else:
                self.prjSnapshots |= metadata

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
        except Exception as ex:
            self._ui.set_status(f'!{str(ex)}')

    def _get_snapshot_dir(self):
        projectDir, __ = os.path.split(self._mdl.prjFile.filePath)
        return os.path.join(
            projectDir,
            self.prefs.get('snapshot_subdir', ''),
        )

    def _get_zipfile_path(self, snapshotId):
        return os.path.join(
            self._get_snapshot_dir(),
            f'{snapshotId}{self.ZIP_EXTENSION}'
        )

    def _initialize_snapshot(self):
        # Set iso date, ID, and path for the next snapshot.
        self._prjDir, self._prjFile = os.path.split(self._mdl.prjFile.filePath)
        prjName, __ = os.path.splitext(self._prjFile)
        prjFileTimestamp = os.path.getmtime(self._mdl.prjFile.filePath)
        prjFileDate = (datetime.fromtimestamp(prjFileTimestamp))
        self._isoDate = prjFileDate.replace(microsecond=0).isoformat()
        self._snapshotId = f"{prjName}.{self._isoDate.replace(':', '.')}"
        self._zipPath = self._get_zipfile_path(self._snapshotId)

    def _open_folder(self, event=None):
        # Open the snapshot folder with the OS file manager.
        snapshotDir = self._get_snapshot_dir()
        os.makedirs(snapshotDir, exist_ok=True)
        open_document(snapshotDir)

    def _open_help(self, event=None):
        Nvsnapshotshelp.open_help_page()

    def _remove_snapshot(self, event=None):
        self._ui.restore_status()
        snapshotId = self.snapshotView.get_selection()
        if snapshotId is None:
            return

        try:
            if self._ui.ask_yes_no(
                message=_('Delete the selected snapshot?'),
                detail=self.prjSnapshots[snapshotId].get('title', ''),
                title=FEATURE,
                parent=self.snapshotView,
            ):
                os.remove(self._get_zipfile_path(snapshotId))
        except ValueError as ex:
            self._ui.set_status(
                (
                    f'!{_("Can not remove snapshot")}: '
                    f'{str(ex)}'
                )
            )
        self.refresh()

    def _revert(self, event=None):
        self._ui.restore_status()
        snapshotIdToRestore = self.snapshotView.get_selection()
        if snapshotIdToRestore is None:
            return

        #--- Check whether an up-to-date snapshot already exists.
        self._initialize_snapshot()
        if (
            not os.path.isfile(self._zipPath)
            or self._mdl.isModified
        ):
            if self._mdl.isModified:
                self._ctrl.save_project()
                self._initialize_snapshot()
            self.snapshotTitle = _('Auto-generated snapshot')
            self.snapshotComment = _('Before reverting to {} \n"{}"').format(
                    snapshotIdToRestore,
                    self.prjSnapshots[snapshotIdToRestore]['title']
                )
            self._save_snapshot()
        zipFileToRestore = self._get_zipfile_path(snapshotIdToRestore)
        try:
            with zipfile.ZipFile(zipFileToRestore, 'r') as z:
                z.extract(
                    self._prjFile,
                    path=self._prjDir,
                )
            self._ctrl.open_project(
                filePath=self._mdl.prjFile.filePath,
                doNotSave=True,
            )
        except Exception as ex:
            message = (
                f'!{_("Can not restore snapshot")}: '
                f'{str(ex)}'
            )
        else:
            message = (
                f'{_("Snapshot restored")}: '
                f'"{snapshotIdToRestore}"'
            )
        finally:
            self._ui.set_status(message)

    def _sanitize_filename(self, filename):
        # Return filename with disallowed characters removed.
        return re.sub(r'[\\|\/|\:|\*|\?|\"|\<|\>|\|]+', '', filename)

    def _save_snapshot(self, event=None):
        #--- Collect project metadata.
        wordCount, totalCount = self._mdl.prjFile.count_words()
        snapshotMetadata = {
            self._snapshotId: {
                'title': self.snapshotTitle,
                'description': self.snapshotComment,
                'date': self._isoDate,
                'work phase': self._mdl.novel.workPhase,
                'words used': wordCount,
                'words total':totalCount,
            }
        }

        #--- Write the snapshot.
        try:
            with zipfile.ZipFile(self._zipPath, 'w') as z:

                # Write project file.
                z.write(
                    self._mdl.prjFile.filePath,
                    arcname=self._prjFile,
                    compress_type=zipfile.ZIP_DEFLATED,
                )

                # Write descriptive text file.
                z.writestr(
                    (
                        f'{self._sanitize_filename(self.snapshotTitle)}'
                        f'{self.DESC_EXTENSION}'
                    ),
                    f'{self.snapshotTitle}\n\n{self.snapshotComment}',
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
            message = f'{_("Snapshot generated")} ({self._isoDate})'
        self._ui.set_status(message)
        self.refresh()

