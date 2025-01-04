from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import *


class CustomMessageBox(QMessageBox):

    def __init__(self, message, icon=None, duration=2000):
        super().__init__()
        self.message = message

        self.setText(self.message)
        if icon is not None:
            self.setIcon(icon)

        self.setStandardButtons(QMessageBox.StandardButton.NoButton)
        QTimer.singleShot(duration, self.accept)

        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )

        self.setStyleSheet(
            """
            QMessageBox{
                background-color: #171717;
                color: #fafafa;
                border: 1px solid #404040;
                border-radius: 4px;
                font-size: 14px;
            }
            QMessageBox QPushButton{
                height: 32px;
                width: 96px;
                font-size: 14px;
                font-weight: 500;
                background-color: #fafafa;
                color:  #171717;
                border-radius: 4px;
            }
            QMessageBox QPushButton:hover{
                background-color: #f5f5f5;
                color:  #171717;
            }
        """
        )

        # self.close_button.clicked.connect(self.accept)
