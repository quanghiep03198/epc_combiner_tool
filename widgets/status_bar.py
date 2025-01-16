from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from helpers.configuration import ConfigService
from widgets.switch import QToggle


class StatusBar(QToolBar):
    def __init__(self, parent=QMainWindow):
        super().__init__(parent)

        self.configurations = ConfigService.load_configs()
        self.setMovable(False)
        self.setFloatable(False)

        self.setObjectName("status_bar")
        self.setStyleSheet(
            """
            QToolBar{
                padding-left: 8px;
                padding-right: 8px;
                spacing: 16px;
                background-color: #171717;
                border-top: 1px solid #52525b;
            }
        """
        )
        # self.spacer = QWidget()
        # self.spacer.setSizePolicy(
        #     QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        # )
        # self.addWidget(self.spacer)

        # Database connection status
        # Primary database connection status
        self.db_primary_connection_layout = QHBoxLayout()
        self.db_primary_connection_layout.setContentsMargins(0, 0, 0, 0)
        self.db_primary_connection_layout.setSpacing(4)
        self.db_primary_connection_status = QWidget()
        self.db_primary_connection_status.setLayout(self.db_primary_connection_layout)
        self.db_primary_text = QLabel(
            text=self.configurations.get("DB_SERVER", "Not connected")
        )
        database_icon = QLabel()
        pixmap = QPixmap("./assets/icons/database.svg")
        database_icon.setPixmap(
            pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.db_primary_connection_layout.addWidget(database_icon)
        self.db_primary_connection_layout.addWidget(self.db_primary_text)
        self.addWidget(self.db_primary_connection_status)

        # Database master connection status
        self.db_master_connection_layout = QHBoxLayout()
        self.db_master_connection_layout.setContentsMargins(0, 0, 0, 0)
        self.db_master_connection_layout.setSpacing(4)
        self.db_master_connection_status = QWidget()
        self.db_master_connection_status.setLayout(self.db_master_connection_layout)
        self.db_master_text = QLabel(
            text=self.configurations.get("DB_SERVER_DEFAULT", "Not connected")
        )
        database_icon = QLabel()
        pixmap = QPixmap("./assets/icons/database.svg")
        database_icon.setPixmap(
            pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.db_master_connection_layout.addWidget(database_icon)
        self.db_master_connection_layout.addWidget(self.db_master_text)
        self.addWidget(self.db_master_connection_status)

        # UHF Reader connection status
        self.reader_connection_layout = QHBoxLayout()
        self.reader_connection_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_connection_layout.setSpacing(4)
        self.reader_connection_status = QWidget()
        self.reader_connection_status.setLayout(self.reader_connection_layout)
        self.reader_icon = QLabel()
        pixmap = QPixmap("./assets/icons/hard-drive.svg")
        self.reader_icon.setPixmap(
            pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.reader_connection_text = QLabel(
            text=self.configurations.get("UHF_READER_TCP_IP", "Not connected")
        )

        self.reader_connection_layout.addWidget(self.reader_icon)
        self.reader_connection_layout.addWidget(self.reader_connection_text)

        self.addWidget(self.reader_connection_status)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.addWidget(self.spacer)

        # Auto save toggle
        self.auto_save_form_layout = QHBoxLayout()
        self.auto_save_form_layout.setContentsMargins(0, 0, 0, 0)
        self.auto_save_form_layout.setSpacing(8)
        self.auto_save_form = QWidget()
        self.auto_save_form.setLayout(self.auto_save_form_layout)

        auto_save_label = QLabel("Tự động lưu")
        auto_save_toggle = QToggle()
        self.auto_save_form_layout.addWidget(auto_save_label)
        self.auto_save_form_layout.addWidget(auto_save_toggle)

        self.addWidget(self.auto_save_form)
