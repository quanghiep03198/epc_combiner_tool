from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from pathlib import Path


class AppSettingsDialog(QDialog):
    """
    Setting dialog form for application connection settings
    """

    _form_state = {
        "uhf_reader_tcp_ip": "",
        "reader_port": 8160,
        "database_host": "",
    }

    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(Path("./themes/global.qss").read_text())
        self.setFixedSize(400, 300)
        self.setContentsMargins(8, 8, 8, 8)
        self.setGeometry(
            (self.root.width() - self.width()) // 2,
            (self.root.height() - self.height()) // 2,
            self.width(),
            self.height(),
        )

        _setting_form_layout = QVBoxLayout(self)
        _setting_form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _setting_form_layout.setSpacing(12)

        # UHF Reader IP setting field control
        self.reader_ip_setting_field_control = QWidget(self)
        self.reader_ip_setting_layout = QVBoxLayout(
            self.reader_ip_setting_field_control
        )
        self.reader_ip_setting_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_ip_setting_layout.setSpacing(4)

        self.reader_ip_setting_label = QLabel(
            "UHF Reader TCP/IP", self.reader_ip_setting_field_control
        )
        self.reader_ip_input_field = QLineEdit(self.reader_ip_setting_field_control)
        self.reader_ip_input_field.setPlaceholderText("0.0.0.0")

        self.reader_ip_setting_layout.addWidget(self.reader_ip_setting_label)
        self.reader_ip_setting_layout.addWidget(self.reader_ip_input_field)
        self.reader_ip_setting_field_control.setLayout(self.reader_ip_setting_layout)

        # UHF Reader port setting field control
        self.reader_port_setting_field_control = QWidget(self)
        self.reader_port_setting_layout = QVBoxLayout(
            self.reader_port_setting_field_control
        )
        self.reader_port_setting_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_port_setting_layout.setSpacing(4)

        self.reader_port_label = QLabel(
            "UHF Reader port", self.reader_port_setting_field_control
        )
        self.reader_port_input_field = QLineEdit(self.reader_port_setting_field_control)
        self.reader_port_input_field.setText("8160")
        self.reader_port_input_field.setEnabled(False)

        self.reader_port_setting_layout.addWidget(self.reader_port_label)
        self.reader_port_setting_layout.addWidget(self.reader_port_input_field)
        self.reader_port_setting_field_control.setLayout(
            self.reader_port_setting_layout
        )

        # UHF Reader port setting field control
        self.database_host_setting_field_control = QWidget(self)
        self.database_setting_field_layout = QVBoxLayout(
            self.database_host_setting_field_control
        )
        self.database_setting_field_layout.setContentsMargins(0, 0, 0, 0)
        self.database_setting_field_layout.setSpacing(4)

        self.reader_port_label = QLabel(
            "Database host", self.database_host_setting_field_control
        )
        self.database_host_input_field = QLineEdit(
            self.database_host_setting_field_control
        )
        self.database_host_input_field.setPlaceholderText("127.0.0.1")

        self.database_setting_field_layout.addWidget(self.reader_port_label)
        self.database_setting_field_layout.addWidget(self.database_host_input_field)
        self.database_host_setting_field_control.setLayout(
            self.database_setting_field_layout
        )

        self.save_button = QPushButton("Save", self)
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.save_settings)

        self.close_button = QPushButton("Close", self)
        self.close_button.setFixedWidth(100)
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
        self.close_button.clicked.connect(self.close)

        self.button_group = QWidget(self)
        self.button_group_layout = QHBoxLayout(self.button_group)
        self.button_group_layout.setContentsMargins(0, 0, 0, 0)
        self.button_group_layout.setSpacing(4)
        self.button_group_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.button_group_layout.addWidget(self.save_button)
        self.button_group_layout.addWidget(self.close_button)
        self.button_group.setLayout(self.button_group_layout)

        _setting_form_layout.addWidget(self.reader_ip_setting_field_control)
        _setting_form_layout.addWidget(self.reader_port_setting_field_control)
        _setting_form_layout.addWidget(self.database_host_setting_field_control)
        _setting_form_layout.addWidget(self.button_group)

        self.setLayout(_setting_form_layout)
        self.exec()

    def on_form_state_change(self, field, value):
        self._form_state[field] = value

    def save_settings(self):
        print(f"Setting saved: {self._form_state}")
        self.close()
