from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from helpers.configuration import ConfigService


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
                padding: 4px 8px;
                spacing: 16px;
            }
        """
        )
        self.spacer = QWidget()
        self.spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.addWidget(self.spacer)

        # Database connection status
        self.db_conn_layout = QHBoxLayout()
        self.db_conn_layout.setContentsMargins(0, 0, 0, 0)
        self.db_conn_layout.setSpacing(4)
        self.db_conn = QWidget()
        self.db_conn.setLayout(self.db_conn_layout)
        self.db_conn_icon = QLabel()
        db_conn_pixmap = QPixmap("./assets/icons/database.svg")
        self.db_conn_icon.setPixmap(
            db_conn_pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.db_conn_status = QLabel(
            text=self.configurations.get("DB_SERVER", "Not connected")
        )

        self.db_conn_layout.addWidget(self.db_conn_icon)
        self.db_conn_layout.addWidget(self.db_conn_status)

        self.addWidget(self.db_conn)

        # UHF Reader connection status
        self.reader_conn_layout = QHBoxLayout()
        self.reader_conn_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_conn_layout.setSpacing(4)
        self.reader_conn = QWidget()
        self.reader_conn.setLayout(self.reader_conn_layout)
        self.reader_conn_icon = QLabel()
        reader_conn_pixmap = QPixmap("./assets/icons/hard-drive.svg")
        self.reader_conn_icon.setPixmap(
            reader_conn_pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.reader_conn_status = QLabel(
            text=self.configurations.get("UHF_READER_TCP_IP", "Not connected")
        )

        self.reader_conn_layout.addWidget(self.reader_conn_icon)
        self.reader_conn_layout.addWidget(self.reader_conn_status)

        self.addWidget(self.reader_conn)
