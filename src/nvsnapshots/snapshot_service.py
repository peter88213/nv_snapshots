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
from nvlib.novx_globals import CHAPTERS_SUFFIX
from nvlib.novx_globals import CHARACTERS_SUFFIX
from nvlib.novx_globals import DATA_SUFFIX
from nvlib.novx_globals import GRID_SUFFIX
from nvlib.novx_globals import ITEMS_SUFFIX
from nvlib.novx_globals import LOCATIONS_SUFFIX
from nvlib.novx_globals import MANUSCRIPT_SUFFIX
from nvlib.novx_globals import PARTS_SUFFIX
from nvlib.novx_globals import PLOTLINES_SUFFIX
from nvlib.novx_globals import SECTIONS_SUFFIX
from nvlib.novx_globals import STAGES_SUFFIX
from nvlib.novx_globals import norm_path
from nvsnapshots.nvsnapshots_globals import FEATURE
from nvsnapshots.nvsnapshots_globals import open_document
from nvsnapshots.nvsnapshots_help import Nvsnapshotshelp
from nvsnapshots.nvsnapshots_locale import _
from nvsnapshots.platform.platform_settings import KEYS
from nvsnapshots.snapshot_dialog import SnapshotDialog
from nvsnapshots.snapshot_view import SnapshotView
import tkinter as tk


class SnapshotService(SubController):
    INI_FILENAME = 'snapshots.ini'
    INI_FILEPATH = '.novx/config'
    SETTINGS = dict(
        snapshot_subdir='Snapshots',
        window_geometry='1270x250',
        right_frame_width=350,
        id_width=160,
        title_width=240,
        date_width=120,
        words_used_width=55,
        words_total_width=100,
        work_phase_width=140,
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

        # -- Set window icon.
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
        self.snapshotView.mainMenu.entryconfig(_('File'), state='disabled')
        self.snapshotView.mainMenu.entryconfig(_('Export'), state='disabled')

    def enable_menu(self):
        self.snapshotView.mainMenu.entryconfig(_('File'), state='normal')
        self.snapshotView.mainMenu.entryconfig(_('Export'), state='normal')

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
        if not self.snapshotView:
            return

        if not self.snapshotView.isOpen:
            return

        self._collect_snapshots()
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
            '<<clean_up>>': self._clean_up_snapshot_dir,
            '<<export_characters>>': self._export_characters,
            '<<export_chapters>>': self._export_chapters,
            '<<export_data>>': self._export_data,
            '<<export_grid>>': self._export_grid,
            '<<export_items>>': self._export_items,
            '<<export_locations>>': self._export_locations,
            '<<export_manuscript>>': self._export_manuscript,
            '<<export_sections>>': self._export_sections,
            '<<export_stages>>': self._export_stages,
            '<<export_parts>>': self._export_parts,
            '<<export_plotlines>>': self._export_plotlines,
            '<<make_snapshot>>': self.make_snapshot,
            '<<open_help>>': self._open_help,
            '<<remove_snapshot>>': self._remove_snapshot,
            '<<revert>>': self._revert,
            '<<open_folder>>': self._open_folder,
        }
        for sequence, callback in event_callbacks.items():
            self.snapshotView.bind(sequence, callback)
        self.snapshotView.bind(KEYS.MAKE_SNAPSHOT[0], self.make_snapshot)
        self.snapshotView.bind(KEYS.OPEN_HELP[0], self._open_help)
        self.snapshotView.bind(KEYS.DELETE[0], self._remove_snapshot)

    def _clean_up_snapshot_dir(self, event=None):
        # Clean up the snapshot folder.
        snapshotDir = self._get_snapshot_dir()
        if not os.path.isdir(snapshotDir):
            return

        for pattern in (
            '*.bak',
            '*.od?',
            '*.xml',
        ):
            for file in glob.iglob(
                pattern,
                root_dir=snapshotDir,
            ):
                try:
                    os.remove(os.path.join(snapshotDir, file))
                except:
                    pass

    def _collect_snapshots(self):
        projectDir, projectFile = os.path.split(self._mdl.prjFile.filePath)
        snapshotDir = os.path.join(projectDir, self.prefs['snapshot_subdir'])
        if not os.path.isdir(snapshotDir):
            return

        self.prjSnapshots.clear()
        prjName, __ = os.path.splitext(projectFile)
        prjSnapshotFiles = glob.glob(
            f'{prjName}.*{self.ZIP_EXTENSION}',
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
                f'!{_("File not found")}: '
                f'"{norm_path(sourcePath)}".'
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
                    **kwargs
                )
            )
        except UserWarning as ex:
            self._ui.set_status(f'#{str(ex)}')
        except Exception as ex:
            self._ui.set_status(f'!{str(ex)}')

    def _export_document(self, suffix, show=True, event=None):
        self._ui.restore_status()
        snapshotId = self.snapshotView.get_selection()
        if snapshotId is None:
            return

        self._create_document(
            self._get_zipfile_path(snapshotId),
            suffix,
            overwrite=True,
            ask=True,
            show=show,
        )

    def _export_characters(self, event=None):
        self._export_document(CHARACTERS_SUFFIX, event=event)

    def _export_chapters(self, event=None):
        self._export_document(CHAPTERS_SUFFIX, event=event)

    def _export_data(self, event=None):
        self._export_document(DATA_SUFFIX, show=False, event=event)

    def _export_grid(self, event=None):
        self._export_document(GRID_SUFFIX, event=event)

    def _export_items(self, event=None):
        self._export_document(ITEMS_SUFFIX, event=event)

    def _export_locations(self, event=None):
        self._export_document(LOCATIONS_SUFFIX, event=event)

    def _export_manuscript(self, event=None):
        self._export_document(MANUSCRIPT_SUFFIX, event=event)

    def _export_parts(self, event=None):
        self._export_document(PARTS_SUFFIX, event=event)

    def _export_plotlines(self, event=None):
        self._export_document(PLOTLINES_SUFFIX, event=event)

    def _export_sections(self, event=None):
        self._export_document(SECTIONS_SUFFIX, event=event)

    def _export_stages(self, event=None):
        self._export_document(STAGES_SUFFIX, event=event)

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
                self.refresh()
        except ValueError as ex:
            self._ui.set_status(
                (
                    f'!{_("Can not remove snapshot")}: '
                    f'{str(ex)}'
                )
            )

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

