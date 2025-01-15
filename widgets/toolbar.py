from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pyqttoast import *
from widgets.settings_dialog import AppSettingsDialog
from widgets.toaster import Toaster
import os
import subprocess
from contexts.auth_context import auth_context
from events import sync_event_emitter, UserActionEvent
from helpers.logger import logger


class AppToolBar(QToolBar):
    """
    Custom QMenuBar for the application
    """

    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setObjectName("toolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # region File actions
        open_file_icon = QIcon()
        pixmap = QPixmap("./assets/icons/folder-open.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        open_file_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.open_file_act = QAction(icon=open_file_icon, text="Thư Mục", parent=self)
        self.open_file_act.triggered.connect(self.handle_reveal_data_folder)
        self.addAction(self.open_file_act)

        # region Language actions
        language_icon = QIcon()
        pixmap = QPixmap("./assets/icons/languages.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        language_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        # self.language_menu = QMenu( title="Ngôn Ngữ", parent=self)
        # self.language_menu.addAction("English")
        # self.language_menu.addAction("Tiếng Việt")
        # self.language_menu.addAction("Español")
        # self.language_menu.addAction("Français")
        # self.language_setting_act.setMenu(self.language_menu)
        self.language_setting_act = QAction(
            icon=language_icon, text="Ngôn Ngữ", parent=self
        )
        self.language_setting_act.triggered.connect(self.handle_change_language)
        self.addAction(self.language_setting_act)

        # region Settings actions
        self.setting_window = AppSettingsDialog(self.root)
        setting_icon = QIcon()
        pixmap = QPixmap("./assets/icons/settings.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        setting_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.connection_setting_act = QAction(
            icon=setting_icon, text="Cài Đặt", parent=self
        )
        self.connection_setting_act.triggered.connect(self.handle_show_settings_window)
        self.addAction(self.connection_setting_act)

        # region Help actions
        help_icon = QIcon()
        pixmap = QPixmap("./assets/icons/circle-help.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        help_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.help_act = QAction(icon=help_icon, text="Trợ Giúp", parent=self)
        # self.help_act.triggered.connect(self.handle_show_settings_window)
        self.addAction(self.help_act)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.addWidget(self.spacer)

        # region Users actions
        self.factory_icon = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/factory.svg").scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.factory_icon.setPixmap(scaled_pixmap)
        self.addWidget(self.factory_icon)

        self.user_factory = QLabel("N/A")
        self.addWidget(self.user_factory)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(24)
        separator.setStyleSheet("background-color: #262626;")
        self.addWidget(separator)

        self.user_icon = QLabel()
        pixmap = QPixmap("./assets/icons/user.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.user_icon.setPixmap(scaled_pixmap)
        self.addWidget(self.user_icon)

        self.username = QLabel()
        self.addWidget(self.username)

        logout_icon = QIcon()
        pixmap = QPixmap("./assets/icons/log-out.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        logout_icon.addPixmap(scaled_pixmap, QIcon.Mode.Normal, QIcon.State.Off)
        self.logout_act = QAction(icon=logout_icon, text="Đăng Xuất", parent=self)
        self.logout_act.setObjectName("logout_act")
        self.logout_act.triggered.connect(self.handle_logout)

        sync_event_emitter.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            self.on_auth_state_change
        )

    def on_auth_state_change(self, data):
        if data["is_authenticated"]:
            self.user_factory.setText(data["factory_name"])
            self.username.setText(data["employee_name"])
            self.addAction(self.logout_act)
        else:

            self.user_factory.setText("N/A")
            self.username.setText("Đăng Nhập")
            self.removeAction(self.logout_act)

    def handle_show_settings_window(self):
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

    def handle_change_language(self):
        toast = Toaster(
            parent=self.root,
            title="Thông Báo",
            text="Chức năng đang phát triển",
            preset=ToastPreset.INFORMATION_DARK,
        )
        toast.show()

    def handle_logout(self):
        auth_context.update(is_authenticated=False)
        auth_context.update(employee_code=None)
        auth_context.update(employee_name=None)
        auth_context.update(factory_code=None)
        auth_context.update(factory_name=None)
        toast = Toaster(
            parent=self.root,
            title="Đăng xuất thành công",
            text="Bạn có thể sử dụng tài khoản khác để tiếp tục sử dụng ứng dụng.",
            preset=ToastPreset.SUCCESS_DARK,
        )
        toast.show()
        sync_event_emitter.emit(UserActionEvent.AUTH_STATE_CHANGE.value, auth_context)
