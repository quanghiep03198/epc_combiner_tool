from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class LoadingWidget(QWidget):

    def __init__(self, parent: QMainWindow, message: str):
        super().__init__(parent)
        self.parent = parent

        self.text_label = QLabel(message)
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.loading_box_layout = QHBoxLayout()
        self.setLayout(self.loading_box_layout)
        self.setFixedSize(250, 100)
        self.setStyleSheet(
            "background-color: #262626; color: #fafafa; font-size: 14px; padding: 16px; border-radius: 4px;"
        )

        self.loading_box_layout.addWidget(self.text_label)
        self.loading_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setVisible(False)
        # self.setVisible(False)

    def open(self, message=None):
        if message is not None:
            self.text_label.setText(message)
        QCoreApplication.processEvents()
        self.setGeometry(
            (self.parent.width() - self.width()) // 2,
            (self.parent.height() - self.height()) // 2,
            self.width(),
            self.height(),
        )
        self.show()

    def close(self):
        self.hide()
