import os
import subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from widgets.settings_dialog import AppSettingsDialog
from i18n import I18nService, Language, __languages__
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent


class SideToolbar(QToolBar):
    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setObjectName("side_toolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setStyleSheet(
            """
            QToolBar{
                padding-left: 8px;
                padding-right: 8px;
                spacing: 12px;
                background-color: #404040;
            }
            """
        )

        # region File actions
        open_file_icon = QIcon()
        pixmap = QPixmap("./assets/icons/folder-open.svg")
        scaled_pixmap = pixmap.scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        open_file_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.open_folder_action = QAction(
            icon=open_file_icon, text="Thư Mục", parent=self
        )
        self.open_folder_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_folder_action.setObjectName("open_folder_action")
        self.open_folder_action.setToolTip("Ctrl + O")
        self.open_folder_action.triggered.connect(self.handle_reveal_data_folder)
        self.addAction(self.open_folder_action)

        # region Language actions
        language_icon = QIcon()
        pixmap = QPixmap("./assets/icons/languages.svg")
        scaled_pixmap = pixmap.scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        language_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)

        self.language_setting_action = QAction(
            icon=language_icon, text="Ngôn Ngữ", parent=self
        )

        self.language_setting_action.setShortcut(QKeySequence("Ctrl+L"))
        self.language_setting_action.setToolTip("Ctrl + L")
        self.language_setting_action.triggered.connect(self.open_language_options)
        self.addAction(self.language_setting_action)

        # region Settings actions
        self.setting_window = AppSettingsDialog(self.root)
        setting_icon = QIcon()
        pixmap = QPixmap("./assets/icons/settings.svg")
        scaled_pixmap = pixmap.scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        setting_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.setting_action = QAction(icon=setting_icon, text="Cài Đặt", parent=self)
        self.setting_action.triggered.connect(self.open_setting_dialog)
        self.addAction(self.setting_action)

        # region Help actions
        help_icon = QIcon()
        pixmap = QPixmap("./assets/icons/circle-help.svg")
        scaled_pixmap = pixmap.scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        help_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.help_act = QAction(icon=help_icon, text="Trợ Giúp", parent=self)
        # self.help_act.triggered.connect(self.handle_show_settings_window)
        self.addAction(self.help_act)

        self.menu = QMenu(self)
        self.menu.setFixedWidth(150)
        self.menu.setContentsMargins(4, 4, 4, 4)
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
                lambda checked, lang=language: self.on_language_change(lang["value"])
            )
            self.menu.addAction(action)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

    def __translate__(self):
        self.open_folder_action.setToolTip(I18nService.t("open_folder") + " (Ctrl+O)")
        self.language_setting_action.setToolTip(
            I18nService.t("change_languague") + " (Ctrl+L)"
        )
        self.setting_action.setToolTip(I18nService.t("change_languague") + " (Ctrl+S)")
        self.language_setting_action.setToolTip(
            I18nService.t("change_languague") + " (Ctrl+S)"
        )

    def open_setting_dialog(self):
        self.setting_window.exec()

    def handle_reveal_data_folder(self):
        folder_path = os.path.abspath("./data")
        print(folder_path)
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
            I18nService.on_language_change(lang)
            I18nService.emit()
        except Exception as e:
            print(e)

        # Add your logic to handle language change here
