from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pyqttoast import *
from widgets.toaster import Toaster
from contexts.auth_context import auth_context
from events import sync_event_emitter, UserActionEvent
from helpers.configuration import ConfigService

# from qtwidgets import AnimatedToggle


class AppToolBar(QToolBar):
    """
    Custom QMenuBar for the application
    """

    def __init__(self, root):
        super().__init__()

        self.root = root
        self.configurations = ConfigService.load_configs()

        self.setObjectName("toolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setStyleSheet(
            """
            QToolBar{
                padding-left: 8px;
                padding-right: 8px;
                spacing: 8px;
                background-color: #171717;
                border-bottom: 1px solid #3f3f46;
            }
        """
        )
        self.breadcrumb_layout = QHBoxLayout()
        self.breadcrumb_layout.setContentsMargins(6, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(4)
        self.breadcrumb = QWidget()
        self.breadcrumb.setLayout(self.breadcrumb_layout)

        self.home_icon = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/blocks.svg").scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.home_icon.setPixmap(scaled_pixmap)

        self.breadcrumb_separator = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/chevron-right.svg").scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.breadcrumb_separator.setPixmap(scaled_pixmap)

        self.page_title = QLabel("Phối dữ liệu EPC")

        self.breadcrumb_layout.addWidget(self.home_icon)
        self.breadcrumb_layout.addWidget(self.breadcrumb_separator)
        self.breadcrumb_layout.addWidget(self.page_title)

        self.addWidget(self.breadcrumb)

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

        self.user_factory_layout = QHBoxLayout()
        self.user_factory_layout.setSpacing(4)
        self.user_factory = QFrame()
        self.user_factory.setLayout(self.user_factory_layout)
        self.user_factory.setLayout(self.user_factory_layout)

        self.user_factory_text = QLabel("N/A")
        self.user_factory_layout.addWidget(self.factory_icon)
        self.user_factory_layout.addWidget(self.user_factory_text)

        self.addWidget(self.user_factory)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(24)
        separator.setStyleSheet("background-color: #262626;")
        self.addWidget(separator)

        self.user_info_layout = QHBoxLayout()
        self.user_info_layout.setSpacing(4)
        self.user_info_layout.setContentsMargins(0, 0, 0, 0)
        self.user_info = QFrame()
        self.user_info.setLayout(self.user_info_layout)

        self.user_icon = QLabel()
        pixmap = QPixmap("./assets/icons/user.svg")
        scaled_pixmap = pixmap.scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.user_icon.setPixmap(scaled_pixmap)
        self.user_info_layout.addWidget(self.user_icon)

        self.user_display_name_text = QLabel("Đăng Nhập")
        self.user_info_layout.addWidget(self.user_display_name_text)

        self.addWidget(self.user_info)

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
            self.user_factory_text.setText(data["factory_name"])
            self.user_display_name_text.setText(data["employee_name"])
            self.addAction(self.logout_act)
        else:

            self.user_factory_text.setText("N/A")
            self.user_display_name_text.setText("Đăng Nhập")
            self.removeAction(self.logout_act)

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
