import os
import sys
import subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from widgets.settings_dialog import AppSettingsDialog
from i18n import I18nService, I18nContext, Language, __languages__
from events import __event_emitter__, UserActionEvent
from helpers.resolve_path import resolve_path
from helpers.logger import logger
from helpers.configuration import ConfigService
from helpers.version import (
    fetch_latest_version,
    load_version_info,
    is_development_environment,
    get_update_directory,
)


class SideToolbar(QToolBar, I18nContext):
    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setObjectName("side_toolbar")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setFloatable(False)
        self.setFixedWidth(50)
        self.setStyleSheet(
            """
            QToolBar{
                padding-left: 4px;
                padding-right: 4px;
                spacing: 18px;
                background-color: #404040;
            }
            """
        )

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
        self.menu.setStyleSheet(
            """
            QMenu::item {
                padding-left: 8px;
            }
        """
        )

        for language in __languages__:
            action = QAction(language["label"], self)
            action.triggered.connect(
                lambda _, lang=language: self.on_language_change(lang["value"])
            )
            self.menu.addAction(action)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

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
                    self.start_update_process()
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

    def start_update_process(self):
        """Start the update process using GUI update manager"""
        try:
            # Check for GUI update manager
            update_gui_py = resolve_path("update/update_manager_gui.py")
            
            if not os.path.exists(update_gui_py):
                QMessageBox.critical(
                    self.root,
                    "Update Error",
                    f"Update manager not found.\n\n"
                    f"Looking for: update/update_manager_gui.py\n"
                    f"Please download the latest version manually from GitHub.",
                    QMessageBox.StandardButton.Ok,
                )
                return

            # Show confirmation message
            confirm_msg = (
                "The update manager will now open.\n\n"
                "You can configure update settings and start the update process.\n"
                "The main application will remain open.\n\n"
                "Continue?"
            )

            # Show final confirmation
            final_reply = QMessageBox.question(
                self.root,
                "Open Update Manager",
                confirm_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if final_reply == QMessageBox.StandardButton.Yes:
                # Show a quick status message
                self.root.statusBar().showMessage("Opening update manager...", 2000)

                # Launch the GUI update manager in a separate process
                if os.name == "nt":  # Windows
                    subprocess.Popen(
                        [sys.executable, update_gui_py],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        cwd=os.path.dirname(update_gui_py),
                    )
                else:  # Unix-like
                    subprocess.Popen(
                        [sys.executable, update_gui_py],
                        cwd=os.path.dirname(update_gui_py),
                    )

        except Exception as e:
            logger.error(f"Failed to start update manager: {e}")
            QMessageBox.critical(
                self.root,
                "Update Error",
                f"Failed to open update manager:\n{str(e)}\n\n"
                f"Please try opening it manually.",
                QMessageBox.StandardButton.Ok,
            )

