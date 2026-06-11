import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from constants import StatusCode
from contexts.auth_context import auth_context
from decorators.debounce import pyqtDebounce
from events import UserActionEvent, __event_emitter__
from helpers.resolve_path import resolve_path
from i18n import I18nContext, I18nService
from services.auth_service import AuthService
from themes.colors import Theme, get_color
from themes.theme_manager import theme_manager
from widgets.toaster import Toaster, ToastPreset


class LoginDialog(QDialog, I18nContext):

    __form_values = {
        "username": None,
        "password": None,
        "factory_code": None,
    }

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)

        self.root = parent
        self.error_toast: Toaster | None = None

        # Create form layout
        layout = QFormLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.setWindowFlag(Qt.WindowType.CoverWindow)

        self.setSizeGripEnabled(False)
        self.setFixedWidth(500)
        self.setFixedHeight(200)
        # Create widgets
        user_label_layout = QHBoxLayout()
        user_label_layout.setSpacing(6)
        user_label_layout.setContentsMargins(0, 0, 0, 0)
        user_label_icon = QWidget()
        user_label_icon.setLayout(user_label_layout)

        self.username_label = QLabel()
        icon_label = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/user.svg"))
        icon_label.setPixmap(
            pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        user_label_layout.addWidget(icon_label)
        user_label_layout.addWidget(self.username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username")
        self.username_input.setProperty("valid", False)
        self.username_input.textChanged.connect(self.on_username_change)

        password_label_layout = QHBoxLayout()
        password_label_layout.setSpacing(6)
        password_label_layout.setContentsMargins(0, 0, 0, 0)
        password_label_icon = QWidget()
        password_label_icon.setLayout(password_label_layout)
        self.password_label = QLabel()
        icon_label = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/key-round.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_label.setPixmap(pixmap)
        password_label_layout.addWidget(icon_label)
        password_label_layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setProperty("valid", False)
        self.password_input.setPlaceholderText("*******")
        self.password_input.setStyleSheet("""
            QLineEdit[echoMode="2"] {
                lineedit-password-character: 8226;
            }
            """)
        self.password_input.textChanged.connect(self.on_password_change)

        factory_label_layout = QHBoxLayout()
        factory_label_layout.setSpacing(6)
        factory_label_layout.setContentsMargins(0, 0, 0, 0)
        factory_label_icon = QWidget()
        factory_label_icon.setLayout(factory_label_layout)

        icon_label = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/factory.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_label.setPixmap(pixmap)
        self.factory_code_label = QLabel()

        factory_label_layout.addWidget(icon_label)
        factory_label_layout.addWidget(self.factory_code_label)

        self.factory_code_select = QComboBox()
        self.factory_code_select.setPlaceholderText("Chọn nhà máy")
        self.factory_code_select.currentIndexChanged.connect(
            lambda index: self.on_factory_code_change(index)
        )
        self.login_button = QPushButton("Đăng nhập")
        self.login_button.setAutoDefault(False)
        self.login_button.setDefault(False)
        self.login_button.setEnabled(False)
        self.login_button.clicked.connect(self.handle_submit_login)

        self.exit_button = QPushButton("Thoát")
        self.exit_button.setFixedWidth(120)
        self.exit_button.setObjectName("exit_button")
        self.exit_icon = QIcon()
        self.exit_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/log-out.svg")),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.exit_button.setAutoDefault(False)
        self.exit_button.setDefault(False)
        self.exit_button.clicked.connect(self.handle_exit)

        # Add widgets to layout
        layout.addRow(user_label_icon, self.username_input)
        layout.addRow(password_label_icon, self.password_input)
        layout.addRow(factory_label_icon, self.factory_code_select)
        layout.addRow(self.exit_button, self.login_button)

        # Set dialog layout
        self.setLayout(layout)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(
            self.update_theme_styles
        )
        self.__translate__()

        # Apply initial theme
        self.update_theme_styles()

    def __translate__(self):
        self.setWindowTitle(I18nService.t("actions.login"))
        self.username_label.setText(I18nService.t("labels.username"))
        self.password_label.setText(I18nService.t("labels.password"))
        self.factory_code_label.setText(I18nService.t("labels.factory"))
        self.factory_code_select.setPlaceholderText(
            I18nService.t("placeholders.factory_placeholder")
        )
        self.exit_button.setText(I18nService.t("actions.exit"))
        self.login_button.setText(I18nService.t("actions.login"))

    def update_theme_styles(self, theme: Theme = None):
        """Update exit button colors based on current theme (outline style)"""
        if theme is None:
            theme = theme_manager.current_theme

        # Get colors from theme
        fg_color = get_color(theme, "foreground")
        border_color = get_color(theme, "border")
        hover_bg = get_color(theme, "muted")

        # Update exit_button with outline style
        self.exit_button.setStyleSheet(f"""
            #exit_button {{
                background: transparent;
                border: 1px solid {border_color};
                color: {fg_color};
            }}
            #exit_button:hover {{
                background-color: {hover_bg};
            }}
            """)

        # Force update
        self.exit_button.style().unpolish(self.exit_button)
        self.exit_button.style().polish(self.exit_button)
        self.exit_button.update()

    def keyPressEvent(self, event):
        # Kiểm tra nếu phím được nhấn là Esc
        if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_Enter:
            # Bỏ qua sự kiện để chặn đóng
            event.ignore()
        else:
            # Xử lý các phím khác bình thường
            super().keyPressEvent(event)

    @pyqtDebounce(wait=300, immediate=False)
    @pyqtSlot(str)
    def on_username_change(self, value: str):
        self.__form_values.update(username=value)
        self.handle_authenticate()

    @pyqtDebounce(wait=300, immediate=False)
    @pyqtSlot(str)
    def on_password_change(self, value: str):
        self.__form_values.update(password=value)
        self.handle_authenticate()

    def on_factory_code_change(self, index):
        auth_context.update(factory_code=self.factory_code_select.itemData(index))
        auth_context.update(factory_name=self.factory_code_select.itemText(index))
        auth_context.update(is_authenticated=True)
        # Only enable login button if all values in auth context is not None
        if all(value is not None for value in auth_context.values()):
            self.login_button.setEnabled(True)
            self.login_button.setDefault(True)
        else:
            self.login_button.setEnabled(False)

    def handle_form_values_change(self, key: str, value: str) -> None:
        self.__form_values[key] = value

    def handle_authenticate(self):
        try:
            if self.__form_values["username"] and self.__form_values["password"]:
                result: dict | None = AuthService.login(
                    self.__form_values["username"], self.__form_values["password"]
                )
                if result:
                    user: dict = result.get("user")
                    auth_context.update(user_code=user.get("user_code"))
                    auth_context.update(employee_code=user.get("employee_code"))
                    auth_context.update(employee_name=user.get("employee_name"))
                    success_color = get_color(theme_manager.current_theme, "success")
                    self.username_input.setStyleSheet(
                        f"border: 1px solid {success_color}"
                    )
                    self.password_input.setStyleSheet(
                        f"border: 1px solid {success_color}"
                    )
                    if (
                        isinstance(self.error_toast, Toaster)
                        and self.error_toast.isVisible()
                    ):
                        self.error_toast.reset()
                        self.error_toast = None
                    factories: list[dict[str, str]] = result.get("factories")
                    self.factory_code_select.clear()
                    for factory in factories:
                        self.factory_code_select.addItem(
                            factory.get("factory_name"), factory.get("factory_code")
                        )

        except Exception as e:
            if isinstance(e.args[0], dict) and "status" in e.args[0]:
                e.status = e.args[0]["status"]
                e.message = e.args[0]["message"]
                if e.status == StatusCode.UNAUTHORIZED.value:
                    destructive_color = get_color(
                        theme_manager.current_theme, "destructive"
                    )
                    self.username_input.setStyleSheet(f"""
                        QLineEdit{{
                            border: 1px solid {destructive_color}
                        }}
                        """)
                    self.password_input.setStyleSheet(f"""
                        QLineEdit{{
                            border: 1px solid {destructive_color}
                        }}
                        QLineEdit[echoMode="2"] {{
                            lineedit-password-character: 8226;
                        }}
                        """)
                    if (
                        isinstance(self.error_toast, Toaster)
                        and self.error_toast.isVisible()
                    ):
                        self.error_toast.reset()
                        self.error_toast = None
                    self.error_toast = Toaster(
                        parent=self.root,
                        title=I18nService.t("notification.login_failed"),
                        text=e.message,
                        preset=ToastPreset.ERROR_DARK,
                        duration=2000,
                    )
                    self.error_toast.__always_on_main_screen = True
                    self.error_toast.show()

    def handle_submit_login(self):
        self.close()
        __event_emitter__.emit(UserActionEvent.AUTH_STATE_CHANGE.value, auth_context)
        toast = Toaster(
            parent=self.root,
            title=I18nService.t("notification.login_success"),
            text=None,
            preset=ToastPreset.SUCCESS_DARK,
        )
        toast.show()

    def handle_exit(self):
        self.close()
        self.root.close()
        sys.exit(0)
