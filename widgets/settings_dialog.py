from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from helpers.configuration import ConfigService
from events import __event_emitter__, UserActionEvent
from widgets.toaster import Toaster
from pyqttoast import ToastPreset
from i18n import I18nService, I18nContext
from uhf.reader import EnumG
from themes.theme_manager import theme_manager
from themes.colors import Theme, get_color


class AppSettingsDialog(QDialog, I18nContext):
    """
    Setting dialog form for application connection settings
    """

    __form_state = ConfigService.load_configs()

    def __init__(self, root: QMainWindow):
        super().__init__(root)

        self.root = root

        self.setWindowTitle("Settings")
        self.setObjectName("settings_dialog")
        self.setWindowFlags(Qt.WindowType.CoverWindow)
        self.setFixedWidth(750)
        self.setMinimumHeight(500)
        self.setSizeGripEnabled(False)
        self.setContentsMargins(8, 8, 8, 8)

        self.setting_form_container_layout = QVBoxLayout()
        self.setting_form_container_layout.setContentsMargins(0, 0, 0, 0)
        self.setting_form_container_layout.setSpacing(12)
        self.setting_form_container = QFrame()
        self.setting_form_container.setLayout(self.setting_form_container_layout)

        self.setting_form_layout = QHBoxLayout()
        self.setting_form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setting_form_layout.setSpacing(24)
        self.setting_form_fieldsets = QWidget()
        self.setting_form_fieldsets.setLayout(self.setting_form_layout)

        # region Reader TCP/IP
        self.reader_fieldset_layout = QVBoxLayout()
        self.reader_fieldset_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_fieldset_layout.setSpacing(16)
        self.reader_fieldset_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.reader_fieldset = QFrame()
        self.reader_fieldset.setLayout(self.reader_fieldset_layout)
        self.reader_fieldset_legend = QLabel("UHF Reader", self.reader_fieldset)
        self.reader_fieldset_legend.setFixedHeight(32)
        self.reader_fieldset_legend.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.reader_fieldset_legend.setObjectName("fieldset_legend")
        self.reader_fieldset_layout.addWidget(self.reader_fieldset_legend)

        self.reader_ip_field_control_layout = QVBoxLayout(self.reader_fieldset)
        self.reader_ip_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_ip_field_control_layout.setSpacing(4)
        self.reader_ip_field_control = QWidget(self.reader_fieldset)
        self.reader_ip_field_control.setFixedHeight(64)
        self.reader_ip_field_control.setLayout(self.reader_ip_field_control_layout)

        self.reader_ip_label = QLabel("TCP/IP", self.reader_ip_field_control)
        self.reader_ip_input = QLineEdit(self.reader_ip_field_control)
        self.reader_ip_input.setPlaceholderText("0.0.0.0")
        self.reader_ip_input.setFixedHeight(36)
        if self.__form_state.get("UHF_READER_TCP_IP"):
            self.reader_ip_input.setText(self.__form_state.get("UHF_READER_TCP_IP"))

        self.reader_ip_input.textChanged.connect(
            lambda value: self.on_form_state_change("UHF_READER_TCP_IP", value)
        )

        self.reader_ip_field_control_layout.addWidget(self.reader_ip_label)
        self.reader_ip_field_control_layout.addWidget(self.reader_ip_input)
        # endregion

        # region Reader port
        self.reader_port_field_control_layout = QVBoxLayout()
        self.reader_port_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_port_field_control_layout.setSpacing(4)
        self.reader_port_field_control = QWidget(self.reader_fieldset)
        self.reader_port_field_control.setLayout(self.reader_port_field_control_layout)
        self.reader_port_field_control.setFixedHeight(64)
        self.reader_port_label = QLabel("Port", self.reader_port_field_control)
        self.reader_port_input = QLineEdit(self.reader_port_field_control)
        self.reader_port_input.setPlaceholderText("8160")
        self.reader_port_input.setFixedHeight(36)
        if self.__form_state.get("UHF_READER_TCP_PORT"):
            self.reader_port_input.setText(self.__form_state.get("UHF_READER_TCP_PORT"))
        self.reader_port_input.textChanged.connect(
            lambda value: self.on_form_state_change("UHF_READER_TCP_PORT", value)
        )
        self.reader_port_field_control_layout.addWidget(self.reader_port_label)
        self.reader_port_field_control_layout.addWidget(self.reader_port_input)

        self.reader_fieldset_layout.addWidget(self.reader_ip_field_control)
        self.reader_fieldset_layout.addWidget(self.reader_port_field_control)
        # endregion

        # region Reader antenna
        self.reader_ant_field_control_layout = QVBoxLayout()
        self.reader_ant_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_ant_field_control_layout.setSpacing(4)
        self.reader_ant_field_control = QWidget(self.reader_fieldset)
        self.reader_ant_field_control.setLayout(self.reader_ant_field_control_layout)
        self.reader_ant_field_control.setFixedHeight(64)
        self.reader_ant_label = QLabel("Antenna", self.reader_ant_field_control)
        self.reader_ant_select = QComboBox(self.reader_ant_field_control)
        self.reader_ant_select.addItem("Ant 1", EnumG.AntennaNo_1.value)
        self.reader_ant_select.addItem("Ant 2", EnumG.AntennaNo_2.value)
        self.reader_ant_select.addItem("Ant 3", EnumG.AntennaNo_3.value)
        self.reader_ant_select.addItem("Ant 4", EnumG.AntennaNo_4.value)
        self.reader_ant_select.setPlaceholderText("Ant 1")
        self.reader_ant_select.setFixedHeight(36)
        if self.__form_state.get("UHF_READER_ANT"):
            self.reader_ant_select.setCurrentIndex(
                self.reader_ant_select.findData(
                    int(self.__form_state.get("UHF_READER_ANT"))
                )
                # int(self.__form_state.get("UHF_READER_ANT"))
            )
        self.reader_ant_select.currentIndexChanged.connect(
            lambda _: self.on_form_state_change(
                "UHF_READER_ANT", str(self.reader_ant_select.currentData())
            )
        )
        self.reader_ant_field_control_layout.addWidget(self.reader_ant_label)
        self.reader_ant_field_control_layout.addWidget(self.reader_ant_select)
        # endregion

        # region Reader power
        self.reader_power_field_control_layout = QVBoxLayout()
        self.reader_power_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_power_field_control_layout.setSpacing(4)
        self.reader_power_field_control = QWidget(self.reader_fieldset)
        self.reader_power_field_control.setLayout(
            self.reader_power_field_control_layout
        )
        self.reader_power_field_control.setFixedHeight(64)
        self.reader_power_label = QLabel("Power", self.reader_power_field_control)
        self.reader_power_input = QLineEdit(self.reader_power_field_control)
        self.reader_power_input.setPlaceholderText("20")
        self.reader_power_input.setFixedHeight(36)
        if self.__form_state.get("UHF_READER_POWER"):
            self.reader_power_input.setText(self.__form_state.get("UHF_READER_POWER"))
        self.reader_power_input.textChanged.connect(
            lambda value: self.on_form_state_change("UHF_READER_POWER", value)
        )
        self.reader_power_field_control_layout.addWidget(self.reader_power_label)
        self.reader_power_field_control_layout.addWidget(self.reader_power_input)

        # endregion

        self.reader_fieldset_layout.addWidget(self.reader_ip_field_control)
        self.reader_fieldset_layout.addWidget(self.reader_port_field_control)
        self.reader_fieldset_layout.addWidget(self.reader_power_field_control)
        self.reader_fieldset_layout.addWidget(self.reader_ant_field_control)
        self.setting_form_layout.addWidget(self.reader_fieldset)
        # endregion

        # region Database fieldset layout
        self.db_fieldset_layout = QVBoxLayout()
        self.db_fieldset_layout.setContentsMargins(0, 0, 0, 0)
        self.db_fieldset_layout.setSpacing(16)
        self.db_fieldset_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.db_fieldset = QFrame()
        self.db_fieldset.setLayout(self.db_fieldset_layout)
        self.db_fieldset_legend = QLabel("Database", self.db_fieldset)
        self.db_fieldset_legend.setFixedHeight(32)
        self.db_fieldset_legend.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.db_fieldset_legend.setObjectName("fieldset_legend")
        self.db_fieldset_layout.addWidget(self.db_fieldset_legend)
        # endregion

        # region Database driver
        self.db_driver_field_control_layout = QVBoxLayout()
        self.db_driver_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_driver_field_control_layout.setSpacing(4)
        self.db_driver_field_control = QWidget(self.db_fieldset)
        self.db_driver_field_control.setLayout(self.db_driver_field_control_layout)
        self.db_driver_field_control.setFixedHeight(64)
        self.db_driver_label = QLabel("Database driver", self.db_driver_field_control)
        self.db_driver_input = QLineEdit(self.db_driver_field_control)
        self.db_driver_input.setPlaceholderText("SQL Server")
        self.db_driver_input.setFixedHeight(36)
        self.db_driver_input.setText("SQL Server")
        self.db_driver_field_control_layout.addWidget(self.db_driver_label)
        self.db_driver_field_control_layout.addWidget(self.db_driver_input)
        # endregion

        # region Database host
        self.db_server_field_control_layout = QVBoxLayout()
        self.db_server_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_server_field_control_layout.setSpacing(4)
        self.db_server_field_control = QWidget(self.db_fieldset)
        self.db_server_field_control.setLayout(self.db_server_field_control_layout)
        self.db_server_field_control.setFixedHeight(64)

        self.db_server_label = QLabel("Database server", self.db_server_field_control)
        self.db_server_input = QLineEdit(self.db_server_field_control)
        self.db_server_input.setPlaceholderText("0.0.0.0")
        self.db_server_input.setFixedHeight(36)
        if self.__form_state.get("DB_SERVER"):
            self.db_server_input.setText(self.__form_state.get("DB_SERVER"))
        self.db_server_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_SERVER", value)
        )
        self.db_server_field_control_layout.addWidget(self.db_server_label)
        self.db_server_field_control_layout.addWidget(self.db_server_input)
        # endregion

        # region Database port
        self.db_port_field_control_layout = QVBoxLayout()
        self.db_port_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_port_field_control_layout.setSpacing(4)
        self.db_port_field_control = QWidget(self.db_fieldset)
        self.db_port_field_control.setLayout(self.db_port_field_control_layout)
        self.db_port_field_control.setFixedHeight(64)
        self.db_port_label = QLabel("Port", self.db_port_field_control)
        self.db_port_input = QLineEdit(self.db_port_field_control)
        self.db_port_input.setPlaceholderText("1433")
        self.db_port_input.setFixedHeight(36)
        if self.__form_state.get("DB_PORT"):
            self.db_port_input.setText(self.__form_state.get("DB_PORT"))
        self.db_port_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_PORT", value)
        )

        self.db_port_field_control_layout.addWidget(self.db_port_label)
        self.db_port_field_control_layout.addWidget(self.db_port_input)

        # region Database user
        self.db_uid_field_control_layout = QVBoxLayout()
        self.db_uid_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_uid_field_control_layout.setSpacing(4)
        self.db_uid_field_control = QWidget(self.db_fieldset)
        self.db_uid_field_control.setLayout(self.db_uid_field_control_layout)
        self.db_uid_field_control.setFixedHeight(64)
        self.db_uid_label = QLabel("User", self.db_uid_field_control)
        self.db_uid_input = QLineEdit(self.db_uid_field_control)
        self.db_uid_input.setPlaceholderText("user")
        self.db_uid_input.setFixedHeight(36)
        if self.__form_state.get("DB_UID"):
            self.db_uid_input.setText(self.__form_state.get("DB_UID"))
        self.db_uid_input.textChanged.connect(
            lambda value: self.on_form_state_change("DB_UID", value)
        )

        self.db_uid_field_control_layout.addWidget(self.db_uid_label)
        self.db_uid_field_control_layout.addWidget(self.db_uid_input)
        # endregion

        # region Database password
        self.db_pwd_field_control_layout = QVBoxLayout()
        self.db_pwd_field_control_layout.setContentsMargins(0, 0, 0, 0)
        self.db_pwd_field_control_layout.setSpacing(4)
        self.db_pwd_field_control = QWidget(self.db_fieldset)
        self.db_pwd_field_control.setLayout(self.db_pwd_field_control_layout)
        self.db_pwd_field_control.setFixedHeight(64)
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
        if self.__form_state.get("DB_PWD"):
            self.db_pwd_input.setText(self.__form_state.get("DB_PWD"))
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
        # endregion

        # region Form dialog actions buttons

        self.save_button = QPushButton("Lưu", self)
        self.save_button.setMinimumWidth(100)
        self.save_button.setFixedHeight(36)
        self.save_button.clicked.connect(self.save_settings)

        self.close_button = QPushButton("Đóng lại", self)
        self.close_button.setMinimumWidth(100)
        self.close_button.setFixedHeight(36)
        self.close_button.setObjectName("close_button")
        self.close_button.clicked.connect(self.handle_close)

        self.button_group = QWidget(self)
        self.button_group_layout = QHBoxLayout()
        self.button_group_layout.setContentsMargins(0, 8, 0, 8)
        self.button_group_layout.setSpacing(8)
        self.button_group_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.button_group_layout.addWidget(self.save_button)
        self.button_group_layout.addWidget(self.close_button)
        self.button_group.setLayout(self.button_group_layout)

        self.setting_form_layout.addWidget(self.db_fieldset)
        self.setting_form_layout.addWidget(self.reader_fieldset)
        self.setting_form_container_layout.addWidget(self.setting_form_fieldsets)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(1)
        self.setting_form_container_layout.addWidget(separator)
        # self.setting_form_container_layout.addWidget(QLine(), 1, 0, 1, 2)
        self.setting_form_container_layout.addWidget(self.button_group)
        self.setLayout(self.setting_form_container_layout)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value, self.__translate__)
        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(
            self.update_theme_styles
        )
        # endregion

        # Apply initial theme
        self.update_theme_styles()

    def __translate__(self):
        self.save_button.setText(I18nService.t("actions.save"))
        self.close_button.setText(I18nService.t("actions.close"))

    def update_theme_styles(self, theme: Theme = None):
        """Update close button colors based on current theme (outline style)"""
        if theme is None:
            theme = theme_manager.current_theme

        # Get colors from theme
        fg_color = get_color(theme, "foreground")
        border_color = get_color(theme, "border")
        hover_bg = get_color(theme, "muted")

        # Update close_button with outline style
        self.close_button.setStyleSheet(
            f"""
            #close_button {{
                background: transparent;
                border: 1px solid {border_color};
                color: {fg_color};
            }}
            #close_button:hover {{
                background-color: {hover_bg};
            }}
            """
        )

        # Force update
        self.close_button.style().unpolish(self.close_button)
        self.close_button.style().polish(self.close_button)
        self.close_button.update()

    @pyqtSlot(str, str)
    def on_form_state_change(self, field, value):
        self.__form_state[field] = value

    @pyqtSlot()
    def save_settings(self):
        err_count = 0
        for key, value in self.__form_state.items():
            if value == "":
                toast = Toaster(
                    parent=self.root,
                    title=I18nService.t("notification.setting_validation_error_title"),
                    text=I18nService.t("notification.setting_validation_error_text"),
                    preset=ToastPreset.ERROR_DARK,
                )
                toast.show()
                err_count += 1
                break
            ConfigService.set_env(key, value)

        if err_count == 0:
            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notification.setting_validation_success_title"),
                text=I18nService.t("notification.setting_validation_success_text"),
                preset=ToastPreset.SUCCESS_DARK,
            )
            toast.setPositionRelativeToWidget(None)
            toast.show()
            __event_emitter__.emit(UserActionEvent.SETTINGS_CHANGE.value)

    @pyqtSlot()
    def handle_close(self):
        configurations = ConfigService.load_configs()
        if any(value == "" for value in configurations.values()):
            reply = QMessageBox.question(
                self.root,
                I18nService.t("notification.missing_setting_title"),
                I18nService.t("notification.missing_setting_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                self.close()
                self.root.close()
                QApplication.instance().quit()
        else:
            self.close()
