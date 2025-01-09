from PyQt6.QtWidgets import *
import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.auth_service import AuthService
from contexts.auth_context import auth_context
from widgets.toaster import Toaster, ToastPreset
from constants import StatusCode
from helpers.logger import logger
from events import sync_event_emitter, UserActionEvent


class LoginDialog(QDialog):

    _form_values = {
        "username": None,
        "password": None,
        "factory_code": None,
        "dept_code": None,
    }

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)

        self.root = parent

        self.setWindowTitle("Đăng Nhập")

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

        self.username_label = QLabel("Tên đăng nhập")
        icon_label = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/user.svg").scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_label.setPixmap(scaled_pixmap)
        user_label_layout.addWidget(icon_label)
        user_label_layout.addWidget(self.username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username")
        self.username_input.setProperty("valid", False)
        self.username_input.textChanged.connect(
            lambda value: self.on_auth_field_change("username", value)
        )

        password_label_layout = QHBoxLayout()
        password_label_layout.setSpacing(6)
        password_label_layout.setContentsMargins(0, 0, 0, 0)
        password_label_icon = QWidget()
        password_label_icon.setLayout(password_label_layout)
        self.password_label = QLabel("Mật khẩu")
        icon_label = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/key-round.svg").scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_label.setPixmap(scaled_pixmap)
        password_label_layout.addWidget(icon_label)
        password_label_layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setProperty("valid", False)
        self.password_input.setPlaceholderText("*******")
        self.password_input.setStyleSheet(
            """
            QLineEdit[echoMode="2"] {
                lineedit-password-character: 8226;
            }
            """
        )
        self.password_input.textChanged.connect(
            lambda value: self.on_auth_field_change("password", value)
        )

        factory_label_layout = QHBoxLayout()
        factory_label_layout.setSpacing(6)
        factory_label_layout.setContentsMargins(0, 0, 0, 0)
        factory_label_icon = QWidget()
        factory_label_icon.setLayout(factory_label_layout)

        icon_label = QLabel()
        scaled_pixmap = QPixmap("./assets/icons/factory.svg").scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_label.setPixmap(scaled_pixmap)
        self.factory_code_label = QLabel("Nhà máy")

        factory_label_layout.addWidget(icon_label)
        factory_label_layout.addWidget(self.factory_code_label)

        self.factory_code_select = QComboBox()
        self.factory_code_select.setPlaceholderText("Chọn nhà máy")
        self.factory_code_select.currentIndexChanged.connect(
            lambda index: self.on_factory_code_change(index)
        )
        self.login_button = QPushButton("Đăng nhập")
        self.login_button.setEnabled(False)
        self.login_button.clicked.connect(self.handle_submit_login)

        self.exit_button = QPushButton("Thoát")
        self.exit_button.setFixedWidth(120)
        # self.exit_button.setToolTip("Thoát")
        self.exit_icon = QIcon()
        self.exit_icon.addPixmap(
            QPixmap("./assets/icons/log-out.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        # self.exit_button.setIcon(self.exit_icon)
        self.exit_button.setStyleSheet(
            """
             QPushButton{
                background: transparent;
                border: 1px solid #404040;
                color: #fafafa
            }
            QPushButton:hover{
                background-color: #404040;
            }
            """
        )
        self.exit_button.clicked.connect(self.handle_exit)

        # Add widgets to layout
        layout.addRow(user_label_icon, self.username_input)
        layout.addRow(password_label_icon, self.password_input)
        layout.addRow(factory_label_icon, self.factory_code_select)
        layout.addRow(self.exit_button, self.login_button)

        # Set dialog layout
        self.setLayout(layout)

    def keyPressEvent(self, event):
        # Kiểm tra nếu phím được nhấn là Esc
        if event.key() == Qt.Key.Key_Escape:
            print("Esc pressed - Dialog will not close.")
            # Bỏ qua sự kiện để chặn đóng
            event.ignore()
        else:
            # Xử lý các phím khác bình thường
            super().keyPressEvent(event)

    @pyqtSlot()
    def on_auth_field_change(self, key: str, value: str):
        if hasattr(self, "debounce_timer") and self.debounce_timer.isActive():
            self.debounce_timer.stop()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(
            lambda: self.handle_debounce_change(key, value)
        )
        self.debounce_timer.start(200)  # 500ms debounce time

    def on_factory_code_change(self, index):
        auth_context.update(factory_code=self.factory_code_select.itemData(index))
        auth_context.update(factory_name=self.factory_code_select.itemText(index))
        auth_context.update(is_authenticated=True)
        # Only enable login button if all values in auth context is not None
        if all(value is not None for value in auth_context.values()):
            self.login_button.setEnabled(True)
        else:
            self.login_button.setEnabled(False)

    def handle_form_values_change(self, key: str, value: str) -> None:
        self._form_values[key] = value

    def handle_debounce_change(self, key: str, value: str) -> None:
        self.handle_form_values_change(key, value)
        self.handle_authenticate()

    def handle_authenticate(self):
        try:
            if self._form_values["username"] and self._form_values["password"]:
                result: dict | None = AuthService.login(
                    self._form_values["username"], self._form_values["password"]
                )
                if result:
                    user: dict = result.get("user")
                    auth_context.update(user_code=user.get("user_code"))
                    auth_context.update(employee_code=user.get("employee_code"))
                    auth_context.update(employee_name=user.get("employee_name"))
                    self.username_input.setStyleSheet("border: 1px solid #22c55e")
                    self.password_input.setStyleSheet("border: 1px solid #22c55e")

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
                self.username_input.setStyleSheet("border: 1px solid #ef4444")
                self.password_input.setStyleSheet(
                    """
                    QLineEdit{
                        border: 1px solid #ef4444
                    }
                    QLineEdit[echoMode="2"] {
                        lineedit-password-character: 8226;
                    }
                    """
                )
                if e.status == StatusCode.UNAUTHORIZED.value:
                    toast = Toaster(
                        parent=self.root,
                        title="Đăng nhập thất bại",
                        text=e.message,
                        preset=ToastPreset.ERROR_DARK,
                    )
                    toast.show()

    def handle_submit_login(self):
        self.close()
        sync_event_emitter.emit(UserActionEvent.AUTH_STATE_CHANGE.value, auth_context)
        toast = Toaster(
            parent=self.root,
            title="Đăng nhập thành công",
            text=None,
            preset=ToastPreset.SUCCESS_DARK,
        )
        toast.show()

    def handle_exit(self):
        self.close()
        self.root.close()
        sys.exit(0)
