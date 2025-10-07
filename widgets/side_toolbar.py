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
        """Start the update process"""
        try:
            # Check for update script/executable first
            # In production, we use updater.exe; in development, update_manager.py
            update_executable = None
            update_batch = resolve_path("update.bat")

            # Priority order: updater.exe > update_manager.py
            updater_exe = resolve_path("updater.exe")
            update_py = resolve_path("update/update_manager.py")

            if os.path.exists(updater_exe):
                update_executable = updater_exe
            elif os.path.exists(update_py):
                update_executable = update_py

            if not update_executable:
                QMessageBox.critical(
                    self.root,
                    "Update Error",
                    f"Update executable not found.\n\n"
                    f"Looking for: updater.exe or update/update_manager.py\n"
                    f"Please download the latest version manually from GitHub.",
                    QMessageBox.StandardButton.Ok,
                )
                return

            # Prepare confirmation message based on environment
            if is_development_environment():
                confirm_msg = (
                    "The update process will now start.\n\n"
                    f"[Development Mode]\n"
                    f"Update will be downloaded to '{get_update_directory()}' folder.\n"
                    f"You can manually install it later.\n\n"
                    f"Continue with the download?"
                )
            else:
                confirm_msg = (
                    "The update process will now start.\n\n"
                    "The application will close and restart automatically.\n"
                    "Make sure to save any unsaved work.\n\n"
                    "Continue with the update?"
                )

            # Show final confirmation without blocking
            final_reply = QMessageBox.question(
                self.root,
                "Confirm Update",
                confirm_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if final_reply == QMessageBox.StandardButton.Yes:
                # Store update script paths for delayed execution
                self.update_executable_path = update_executable
                self.update_batch_path = (
                    update_batch if os.path.exists(update_batch) else None
                )

                # Show a quick status message
                self.root.statusBar().showMessage("Starting update process...", 2000)

                # Use QTimer to delay the update process
                # This allows the dialog to close properly before exit
                QTimer.singleShot(500, self._execute_update_and_exit)

        except Exception as e:
            logger.error(f"Failed to start update process: {e}")
            QMessageBox.critical(
                self.root,
                "Update Error",
                f"Failed to start update process:\n{str(e)}\n\n"
                f"Please try updating manually.",
                QMessageBox.StandardButton.Ok,
            )

    def _execute_update_and_exit(self):
        """Execute the update process and exit application"""
        try:
            # Start update process
            if os.name == "nt" and self.update_batch_path:  # Windows with batch file
                subprocess.Popen(
                    [self.update_batch_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.path.dirname(self.update_batch_path),
                )
            elif os.name == "nt":  # Windows
                # Check if it's an .exe file or .py file
                if self.update_executable_path.endswith(".exe"):
                    # Run executable directly
                    subprocess.Popen(
                        [self.update_executable_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                else:
                    # Run Python script
                    subprocess.Popen(
                        [sys.executable, self.update_executable_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
            else:  # Unix-like
                if self.update_executable_path.endswith(".exe"):
                    subprocess.Popen([self.update_executable_path])
                else:
                    subprocess.Popen([sys.executable, self.update_executable_path])

            # Close all message boxes and dialogs first
            print("🔄 Closing all dialogs and widgets...")
            for widget in QApplication.allWidgets():
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    widget.close()
                    widget.deleteLater()

            # Process events to ensure dialogs are closed
            QApplication.processEvents()

            # Force close main window with proper cleanup
            if self.root:
                print("🔄 Closing main window...")
                self.root.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                self.root.close()
                self.root.deleteLater()

            # Multiple attempts at clean exit
            print("🔄 Initiating application shutdown...")

            # Process any remaining events
            QApplication.processEvents()

            # Quit the application
            QApplication.closeAllWindows()
            QApplication.quit()

            # Force exit after a brief delay to ensure cleanup
            QTimer.singleShot(1000, self._force_exit)

        except Exception as e:
            logger.error(f"Failed to execute update: {e}")
            print(f"Update execution failed: {e}")
            # Force exit even if cleanup fails
            self._force_exit()

    def _force_exit(self):
        """Force application exit with extreme measures"""
        try:
            print("🔄 Force exiting application...")

            # Final cleanup
            QApplication.processEvents()
            QApplication.quit()

            # Nuclear option - force process termination
            if ConfigService.get_env("ENV") != "development":
                import os

                print("💀 Force terminating process...")
                os._exit(0)  # Nuclear exit - bypasses cleanup
            else:
                sys.exit(0)

        except:
            # Last resort
            import os

            os._exit(0)
