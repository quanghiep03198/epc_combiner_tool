from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from helpers.configuration import ConfigService
from events import __event_emitter__, UserActionEvent
from widgets.toaster import Toaster
from pyqttoast import ToastPreset


class AppSettingsDialog(QDialog):
    """
    Setting dialog form for application connection settings
    """

    _form_state = ConfigService.load_configs()

    def __init__(self, root: QMainWindow):
        super().__init__(root)

        self.root = root

        self.setWindowTitle("Settings")
        self.setObjectName("settings_dialog")
        self.setWindowFlags(Qt.WindowType.CoverWindow)
        self.setFixedWidth(500)
        self.setSizeGripEnabled(False)
        self.setContentsMargins(8, 8, 8, 8)

        _setting_form_layout = QVBoxLayout()
        _setting_form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _setting_form_layout.setSpacing(24)
        # region UHF Reader settings

        # UHF Reader IP setting field control
        self.reader_fieldset_layout = QVBoxLayout()
        self.reader_fieldset_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_fieldset_layout.setSpacing(12)
        self.reader_fieldset = QFrame()
        self.reader_fieldset.setLayout(self.reader_fieldset_layout)
        self.db_fieldset_legend = QLabel("UHF Reader", self.reader_fieldset)
        self.db_fieldset_legend.setObjectName("fieldset_legend")
        self.reader_fieldset_layout.addWidget(self.db_fieldset_legend)

        self.reader_ip_field_control_layout = QVBoxLayout(self.reader_fieldset)
        self.reader_ip_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_ip_field_control_layout.setSpacing(4)
        self.reader_ip_field_control = QWidget(self.reader_fieldset)
        self.reader_ip_field_control.setLayout(self.reader_ip_field_control_layout)

        self.reader_ip_label = QLabel("UHF Reader TCP/IP", self.reader_ip_field_control)
        self.reader_ip_input = QLineEdit(self.reader_ip_field_control)
        self.reader_ip_input.setPlaceholderText("0.0.0.0")
        self.reader_ip_input.setFixedHeight(36)
        if self._form_state.get("UHF_READER_TCP_IP"):
            self.reader_ip_input.setText(self._form_state.get("UHF_READER_TCP_IP"))

        self.reader_ip_input.textChanged.connect(
            lambda value: self.on_form_state_change("UHF_READER_TCP_IP", value)
        )

        self.reader_ip_field_control_layout.addWidget(self.reader_ip_label)
        self.reader_ip_field_control_layout.addWidget(self.reader_ip_input)

        # UHF Reader port setting field control
        self.reader_port_field_control_layout = QVBoxLayout()
        self.reader_port_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_port_field_control_layout.setSpacing(4)
        self.reader_port_field_control = QWidget(self.reader_fieldset)
        self.reader_port_field_control.setLayout(self.reader_port_field_control_layout)
        self.reader_port_label = QLabel(
            "UHF Reader port", self.reader_port_field_control
        )
        self.reader_port_input = QLineEdit(self.reader_port_field_control)
        self.reader_port_input.setPlaceholderText("8160")
        self.reader_port_input.setFixedHeight(36)
        if self._form_state.get("UHF_READER_TCP_PORT"):
            self.reader_port_input.setText(self._form_state.get("UHF_READER_TCP_PORT"))
        self.reader_port_input.textChanged.connect(
            lambda value: self.on_form_state_change("UHF_READER_TCP_PORT", value)
        )
        self.reader_port_field_control_layout.addWidget(self.reader_port_label)
        self.reader_port_field_control_layout.addWidget(self.reader_port_input)

        self.reader_fieldset_layout.addWidget(self.reader_ip_field_control)
        self.reader_fieldset_layout.addWidget(self.reader_port_field_control)

        _setting_form_layout.addWidget(self.reader_fieldset)
        # endregion

        # region Database settings

        # Database driver settings
        self.db_fieldset_layout = QVBoxLayout()
        self.db_fieldset_layout.setContentsMargins(0, 0, 0, 0)
        self.db_fieldset_layout.setSpacing(12)
        self.db_fieldset = QFrame()
        self.db_fieldset.setLayout(self.db_fieldset_layout)
        self.db_fieldset_legend = QLabel("Database", self.db_fieldset)
        self.db_fieldset_legend.setObjectName("fieldset_legend")
        self.db_fieldset_layout.addWidget(self.db_fieldset_legend)

        self.db_driver_field_control_layout = QVBoxLayout()
        self.db_driver_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_driver_field_control_layout.setSpacing(4)
        self.db_driver_field_control = QWidget(self.db_fieldset)
        self.db_driver_field_control.setLayout(self.db_driver_field_control_layout)

        # Datbase host setting field control
        self.db_driver_label = QLabel("Database driver", self.db_driver_field_control)
        self.db_driver_input = QLineEdit(self.db_driver_field_control)
        self.db_driver_input.setPlaceholderText("SQL Server")
        self.db_driver_input.setFixedHeight(36)
        self.db_driver_input.setText("SQL Server")

        self.db_driver_field_control_layout.addWidget(self.db_driver_label)
        self.db_driver_field_control_layout.addWidget(self.db_driver_input)

        # Datbase host setting field control
        self.db_server_field_control_layout = QVBoxLayout()
        self.db_server_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_server_field_control_layout.setSpacing(4)
        self.db_server_field_control = QWidget(self.db_fieldset)
        self.db_server_field_control.setLayout(self.db_server_field_control_layout)

        self.db_server_label = QLabel("Database server", self.db_server_field_control)
        self.db_server_input = QLineEdit(self.db_server_field_control)
        self.db_server_input.setPlaceholderText("0.0.0.0")
        self.db_server_input.setFixedHeight(36)
        if self._form_state.get("DB_SERVER"):
            self.db_server_input.setText(self._form_state.get("DB_SERVER"))
        self.db_server_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_SERVER", value)
        )
        self.db_server_field_control_layout.addWidget(self.db_server_label)
        self.db_server_field_control_layout.addWidget(self.db_server_input)

        # Database port setting field control
        self.db_port_field_control_layout = QVBoxLayout()
        self.db_port_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_port_field_control_layout.setSpacing(4)
        self.db_port_field_control = QWidget(self.db_fieldset)
        self.db_port_field_control.setLayout(self.db_port_field_control_layout)
        self.db_port_label = QLabel("Port", self.db_port_field_control)
        self.db_port_input = QLineEdit(self.db_port_field_control)
        self.db_port_input.setPlaceholderText("1433")
        self.db_port_input.setFixedHeight(36)
        if self._form_state.get("DB_PORT"):
            self.db_port_input.setText(self._form_state.get("DB_PORT"))
        self.db_port_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_PORT", value)
        )

        self.db_port_field_control_layout.addWidget(self.db_port_label)
        self.db_port_field_control_layout.addWidget(self.db_port_input)

        # Database user
        self.db_uid_field_control_layout = QVBoxLayout()
        self.db_uid_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_uid_field_control_layout.setSpacing(4)
        self.db_uid_field_control = QWidget(self.db_fieldset)
        self.db_uid_field_control.setLayout(self.db_uid_field_control_layout)
        self.db_uid_label = QLabel("User", self.db_uid_field_control)
        self.db_uid_input = QLineEdit(self.db_uid_field_control)
        self.db_uid_input.setPlaceholderText("user")
        self.db_uid_input.setFixedHeight(36)
        if self._form_state.get("DB_UID"):
            self.db_uid_input.setText(self._form_state.get("DB_UID"))
        self.db_uid_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_UID", value)
        )

        self.db_uid_field_control_layout.addWidget(self.db_uid_label)
        self.db_uid_field_control_layout.addWidget(self.db_uid_input)

        # Database password
        self.db_pwd_field_control_layout = QVBoxLayout()
        self.db_pwd_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_pwd_field_control_layout.setSpacing(4)
        self.db_pwd_field_control = QWidget(self.db_fieldset)
        self.db_pwd_field_control.setLayout(self.db_pwd_field_control_layout)
        self.db_pwd_label = QLabel("Password", self.db_pwd_field_control)
        self.db_pwd_input = QLineEdit(self.db_pwd_field_control)
        self.db_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_pwd_input.setPlaceholderText("******")
        self.db_pwd_input.setStyleSheet(
            """
                QLineEdit[echoMode="2"] {
                    lineedit-password-character: 8226;
                }
            """
        )
        self.db_pwd_input.setFixedHeight(36)
        if self._form_state.get("DB_PWD"):
            self.db_pwd_input.setText(self._form_state.get("DB_PWD"))
        self.db_pwd_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_PWD", value)
        )
        self.db_pwd_field_control_layout.addWidget(self.db_pwd_label)
        self.db_pwd_field_control_layout.addWidget(self.db_pwd_input)

        self.db_fieldset_layout.addWidget(self.db_driver_field_control)
        self.db_fieldset_layout.addWidget(self.db_server_field_control)
        self.db_fieldset_layout.addWidget(self.db_port_field_control)
        self.db_fieldset_layout.addWidget(self.db_uid_field_control)
        self.db_fieldset_layout.addWidget(self.db_pwd_field_control)

        _setting_form_layout.addWidget(self.db_fieldset)
        # endregion

        # region Form dialog actions buttons

        self.save_button = QPushButton("Lưu", self)
        self.save_button.setMinimumWidth(100)
        self.save_button.setFixedHeight(36)
        self.save_button.clicked.connect(self.save_settings)

        self.close_button = QPushButton("Đóng lại", self)
        self.close_button.setMinimumWidth(100)
        self.close_button.setFixedHeight(36)
        self.close_button.setStyleSheet(
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
        self.close_button.clicked.connect(self.handle_close)

        self.button_group = QWidget(self)
        self.button_group_layout = QHBoxLayout()
        self.button_group_layout.setContentsMargins(0, 0, 0, 0)
        self.button_group_layout.setSpacing(4)
        self.button_group_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.button_group_layout.addWidget(self.save_button)
        self.button_group_layout.addWidget(self.close_button)
        self.button_group.setLayout(self.button_group_layout)

        _setting_form_layout.addWidget(self.button_group)
        # endregion
        self.setLayout(_setting_form_layout)

    @pyqtSlot(str, str)
    def on_form_state_change(self, field, value):
        self._form_state[field] = value

    @pyqtSlot()
    def save_settings(self):
        err_count = 0
        print(self._form_state)
        for key, value in self._form_state.items():
            if value == "":
                toast = Toaster(
                    parent=self.root,
                    title="Thông tin cài đặt không hợp lệ",
                    text=f"Vui lòng điền đầy đủ thông tin cài đặt.",
                    preset=ToastPreset.ERROR_DARK,
                )
                toast.show()
                err_count += 1
                break
            ConfigService.set_env(key, value)

        if err_count == 0:
            toast = Toaster(
                parent=self.root,
                title="Lưu thông tin cài đặt thành công",
                text=f"Ứng dụng sẽ khởi động lại để cập nhật thông tin cài đặt.",
                preset=ToastPreset.SUCCESS_DARK,
            )
            toast.setPositionRelativeToWidget(None)
            toast.show()
            __event_emitter__.emit(UserActionEvent.SETTINGS_CHANGE.value, None)

    @pyqtSlot()
    def handle_close(self):
        configurations = ConfigService.load_configs()
        if all(value == "" for value in configurations.values()):
            reply = QMessageBox.question(
                self.root,
                "Cài đặt kết nối chưa được thiết lập",
                "Bạn có muốn thiết lập lại ngay bây giờ không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                self.close()
                self.root.close()
        else:
            self.close()
