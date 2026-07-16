import os
import subprocess
import sys
import urllib.request

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from events import UserActionEvent, __event_emitter__
from helpers.configuration import ConfigService
from helpers.logger import logger
from helpers.resolve_path import resolve_path
from helpers.version import (
    fetch_latest_version,
    get_update_directory,
    is_development_environment,
    load_version_info,
)
from i18n import I18nContext, I18nService, Language, __languages__
from themes.colors import Theme, get_color
from themes.theme_manager import theme_manager
from widgets.settings_dialog import AppSettingsDialog


class UpdaterDownloadWorker(QObject):
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    download_finished = pyqtSignal(str, str)
    download_failed = pyqtSignal(str)
    download_canceled = pyqtSignal()

    def __init__(self, version_candidates: list[str], download_dir: str):
        super().__init__()
        self.version_candidates = version_candidates
        self.download_dir = download_dir
        self._is_canceled = False

    @pyqtSlot()
    def run(self):
        last_error = None
        for candidate in self.version_candidates:
            if self._is_canceled:
                self.download_canceled.emit()
                return

            updater_url = (
                "https://github.com/quanghiep03198/epc_combiner_tool/releases/"
                f"download/{candidate}/epc-ic-{candidate}-windows-updater-x64.exe"
            )
            updater_file = os.path.join(
                self.download_dir, f"epc-ic-{candidate}-windows-updater-x64.exe"
            )

            try:
                self.status_changed.emit(f"Downloading updater {candidate}...")
                self.progress_changed.emit(0)

                with urllib.request.urlopen(updater_url, timeout=30) as response:
                    total_header = response.headers.get("Content-Length")
                    total_size = int(total_header) if total_header else 0
                    downloaded = 0

                    with open(updater_file, "wb") as output_file:
                        while True:
                            if self._is_canceled:
                                output_file.close()
                                if os.path.exists(updater_file):
                                    os.remove(updater_file)
                                self.download_canceled.emit()
                                return

                            chunk = response.read(1024 * 128)
                            if not chunk:
                                break

                            output_file.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                progress = min(int(downloaded * 100 / total_size), 100)
                                self.progress_changed.emit(progress)

                if not os.path.exists(updater_file):
                    raise RuntimeError("Updater downloaded but file was not found.")

                self.progress_changed.emit(100)
                self.download_finished.emit(updater_file, candidate)
                return

            except Exception as ex:
                last_error = ex
                if os.path.exists(updater_file):
                    os.remove(updater_file)

        self.download_failed.emit(f"Failed to download updater: {last_error}")

    @pyqtSlot()
    def cancel(self):
        self._is_canceled = True


class SideToolbar(QToolBar, I18nContext):
    def __init__(self, root):
        super().__init__()

        self.root = root
        self.download_thread = None
        self.download_worker = None
        self.download_progress_dialog = None

        self.setObjectName("side_toolbar")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setFloatable(False)
        self.setFixedWidth(50)

        # region File actions
        open_file_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/folder-open.svg"))

        open_file_icon.addPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.open_folder_action = QAction(icon=open_file_icon, parent=self)
        self.open_folder_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_folder_action.setObjectName("open_folder_action")
        self.open_folder_action.setToolTip("Ctrl + O")
        self.open_folder_action.triggered.connect(self.handle_reveal_data_folder)
        self.addAction(self.open_folder_action)

        # region Language actions
        language_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/languages.svg"))
        language_icon.addPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )

        self.language_setting_action = QAction(icon=language_icon, parent=self)

        self.language_setting_action.setShortcut(QKeySequence("Ctrl+L"))
        self.language_setting_action.setToolTip("Ctrl + L")
        self.language_setting_action.triggered.connect(self.open_language_options)
        self.addAction(self.language_setting_action)

        # region Settings actions
        self.setting_window = AppSettingsDialog(self.root)
        setting_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/settings.svg"))
        setting_icon.addPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.setting_action = QAction(icon=setting_icon, parent=self)
        self.setting_action.triggered.connect(self.open_setting_dialog)
        self.addAction(self.setting_action)

        # region Check for update actions
        # self.setting_window = AppSettingsDialog(self.root)
        check_for_update_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/history.svg"))
        check_for_update_icon.addPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.check_update_action = QAction(icon=check_for_update_icon, parent=self)
        self.check_update_action.triggered.connect(self.check_update_latest_version)
        self.addAction(self.check_update_action)

        # region Help actions
        help_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/circle-help.svg"))
        help_icon.addPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.help_action = QAction(icon=help_icon, parent=self)
        self.help_action.setShortcut(QKeySequence("Ctrl+H"))
        self.addAction(self.help_action)

        self.menu = QMenu(self)
        self.menu.setFixedWidth(150)
        self.menu.setContentsMargins(4, 8, 4, 8)
        self.menu.setStyleSheet("""
            QMenu::item {
                padding-left: 8px;
            }
        """)

        for language in __languages__:
            action = QAction(language["label"], self)
            action.triggered.connect(
                lambda _, lang=language: self.on_language_change(lang["value"])
            )
            self.menu.addAction(action)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(
            self.update_theme_styles
        )

        # Apply initial theme styles after all widgets are created
        self.update_theme_styles()

    def __translate__(self):
        self.open_folder_action.setToolTip(
            I18nService.t("actions.open_folder") + " (Ctrl+O)"
        )
        self.language_setting_action.setToolTip(
            I18nService.t("actions.change_languague") + " (Ctrl+L)"
        )
        self.setting_action.setToolTip(I18nService.t("actions.settings") + " (Ctrl+S)")
        self.help_action.setToolTip(I18nService.t("actions.help") + " (Ctrl+H)")
        self.check_update_action.setToolTip(I18nService.t("actions.check_for_update"))

    def update_theme_styles(self, theme: Theme = None):
        """Update side toolbar colors based on current theme"""
        if theme is None:
            theme = theme_manager.current_theme

        bg_color = get_color(theme, "secondary")
        self.setStyleSheet(f"""
            QToolBar{{
                padding-left: 4px;
                padding-right: 4px;
                spacing: 18px;
                background-color: {bg_color};
            }}
        """)

        # Force update to apply new styles
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def open_setting_dialog(self):
        self.setting_window.exec()

    def handle_reveal_data_folder(self):
        folder_path = resolve_path("data")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if os.name == "nt":
            # Windows
            os.startfile(folder_path)
        if os.name == "posix":
            # macOS or Linux
            subprocess.call(
                ["open", folder_path]
                if sys.platform == "darwin"
                else ["xdg-open", folder_path]
            )

    def open_language_options(self):
        action_geometry = self.actionGeometry(self.language_setting_action)
        self.menu.exec(self.mapToGlobal(action_geometry.topRight() + QPoint(8, 0)))

    def on_language_change(self, lang: Language):
        try:
            I18nService.set_language(lang)
            I18nService.emit()
        except Exception as e:
            logger.error(e)

        # Add your logic to handle language change here

    def check_update_latest_version(self):
        try:
            latest_version = fetch_latest_version()
            current_version = load_version_info().version

            # Clean version strings for comparison
            clean_current = current_version.lstrip("v")
            clean_latest = latest_version.lstrip("v")

            # Use packaging library for proper version comparison
            try:
                from packaging import version

                current_ver = version.parse(clean_current)
                latest_ver = version.parse(clean_latest)
                has_update = latest_ver > current_ver
            except ImportError:
                # Fallback comparison
                has_update = clean_current != clean_latest

            if has_update:
                # Prepare update message based on environment
                if is_development_environment():
                    update_msg = (
                        f"A new version is available!\n\n"
                        f"Current version: {current_version}\n"
                        f"Latest version: {latest_version}\n\n"
                        f"[Development Mode]\n"
                        f"The update will be downloaded to '{get_update_directory()}' folder.\n"
                        f"Do you want to download the update now?"
                    )
                else:
                    update_msg = (
                        f"A new version is available!\n\n"
                        f"Current version: {current_version}\n"
                        f"Latest version: {latest_version}\n\n"
                        f"Do you want to download and install the update now?\n"
                        f"The application will restart automatically after the update."
                    )

                # Show update available dialog
                reply = QMessageBox.question(
                    self.root,
                    "Update Available",
                    update_msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.start_update_process(latest_version)
            else:
                # No update available
                QMessageBox.information(
                    self.root,
                    "No Updates",
                    f"You are already running the latest version ({current_version}).",
                    QMessageBox.StandardButton.Ok,
                )

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            QMessageBox.warning(
                self.root,
                "Update Check Failed",
                f"Failed to check for updates:\n{str(e)}\n\n"
                f"Please check your internet connection and try again.",
                QMessageBox.StandardButton.Ok,
            )

    def start_update_process(self, version: str):
        """Download updater from release assets, launch it, then close the app."""
        try:
            if self.download_thread and self.download_thread.isRunning():
                QMessageBox.information(
                    self.root,
                    "Update",
                    "Update download is already in progress.",
                    QMessageBox.StandardButton.Ok,
                )
                return

            version_tag = (version or "").strip()
            if not version_tag:
                raise RuntimeError("Invalid update version.")

            version_candidates = [version_tag]
            if not version_tag.startswith("v"):
                version_candidates.insert(0, f"v{version_tag}")

            download_dir = get_update_directory() or resolve_path("release")
            os.makedirs(download_dir, exist_ok=True)

            self.download_progress_dialog = QProgressDialog(
                "Downloading updater...", None, 0, 100, self.root
            )
            self.download_progress_dialog.setMinimumWidth(400)
            self.download_progress_dialog.setMinimumHeight(100)
            self.download_progress_dialog.setWindowTitle("Update Download")
            self.download_progress_dialog.setWindowModality(
                Qt.WindowModality.ApplicationModal
            )
            self.download_progress_dialog.setAutoClose(False)
            self.download_progress_dialog.setAutoReset(False)
            self.download_progress_dialog.setMinimumDuration(0)
            self.download_progress_dialog.setValue(0)

            self.download_thread = QThread(self)
            self.download_worker = UpdaterDownloadWorker(
                version_candidates, download_dir
            )
            self.download_worker.moveToThread(self.download_thread)

            self.download_thread.started.connect(self.download_worker.run)
            self.download_progress_dialog.canceled.connect(self.download_worker.cancel)

            self.download_worker.progress_changed.connect(self._on_download_progress)
            self.download_worker.status_changed.connect(self._on_download_status)
            self.download_worker.download_finished.connect(self._on_download_finished)
            self.download_worker.download_failed.connect(self._on_download_failed)
            self.download_worker.download_canceled.connect(self._on_download_canceled)

            self.download_worker.download_finished.connect(self.download_thread.quit)
            self.download_worker.download_failed.connect(self.download_thread.quit)
            self.download_worker.download_canceled.connect(self.download_thread.quit)
            self.download_thread.finished.connect(self._cleanup_download_worker)

            self.download_thread.start()
            self.download_progress_dialog.show()

        except Exception as e:
            logger.error(f"Failed to start update process: {e}")
            QMessageBox.critical(
                self.root,
                "Update Error",
                f"Failed to start update process:\n{str(e)}\n\n"
                f"Please try updating manually.",
                QMessageBox.StandardButton.Ok,
            )

    def _on_download_progress(self, value: int):
        if self.download_progress_dialog:
            self.download_progress_dialog.setValue(value)

    def _on_download_status(self, message: str):
        if self.download_progress_dialog:
            self.download_progress_dialog.setLabelText(message)

    def _on_download_finished(self, updater_file: str, downloaded_version: str):
        if self.download_progress_dialog:
            self.download_progress_dialog.setValue(100)
            self.download_progress_dialog.close()

        logger.info(f"Updater downloaded to: {updater_file}")

        try:
            if os.name == "nt":
                subprocess.Popen(
                    [updater_file],
                    cwd=os.path.dirname(updater_file),
                    creationflags=(
                        subprocess.DETACHED_PROCESS
                        | subprocess.CREATE_NEW_PROCESS_GROUP
                    ),
                )
            else:
                subprocess.Popen([updater_file], cwd=os.path.dirname(updater_file))

            logger.info(f"Updater launch started for version: {downloaded_version}")
            self._shutdown_application()
        except Exception as e:
            logger.error(f"Failed to launch updater: {e}")
            QMessageBox.critical(
                self.root,
                "Update Error",
                f"Failed to launch updater:\n{str(e)}\n\nPlease try again.",
                QMessageBox.StandardButton.Ok,
            )

    def _on_download_failed(self, message: str):
        if self.download_progress_dialog:
            self.download_progress_dialog.close()

        logger.error(message)
        QMessageBox.critical(
            self.root,
            "Update Error",
            f"{message}\n\nPlease try updating manually.",
            QMessageBox.StandardButton.Ok,
        )

    def _on_download_canceled(self):
        if self.download_progress_dialog:
            self.download_progress_dialog.close()

        QMessageBox.information(
            self.root,
            "Update",
            "Update download was canceled.",
            QMessageBox.StandardButton.Ok,
        )

    def _cleanup_download_worker(self):
        if self.download_worker:
            self.download_worker.deleteLater()
            self.download_worker = None
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None
        self.download_progress_dialog = None

    def _shutdown_application(self):
        """Close all windows and terminate the current application process."""
        try:
            for widget in QApplication.allWidgets():
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    widget.close()
                    widget.deleteLater()

            QApplication.processEvents()

            if self.root:
                self.root.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                self.root.close()
                self.root.deleteLater()

            QApplication.processEvents()
            QApplication.closeAllWindows()
            QApplication.quit()
            if ConfigService.get_env("ENV") != "development":
                os._exit(0)
            sys.exit(0)

        except Exception as e:
            logger.error(f"Failed to shutdown app cleanly: {e}")
            os._exit(0)
