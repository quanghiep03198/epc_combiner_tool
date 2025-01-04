from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class PlaygroundHeading(QFrame):
    def __init__(
        self,
    ):
        super().__init__()

        header_top_heading_layout = QVBoxLayout()
        header_top_heading_layout.setContentsMargins(0, 0, 0, 0)
        header_top_heading_layout.setSpacing(2)
        self.setLayout(header_top_heading_layout)

        header_top_title = QLabel()
        header_top_desc = QLabel()
        header_top_title.setText("Phối đôi EPC")
        header_top_desc.setText(
            "Chọn chỉ lệnh, quét EPC và nhập các thông tin phía dưới để tiến hành phối."
        )
        header_top_title.setStyleSheet("font-weight: 700; font-size: 16px")
        header_top_desc.setStyleSheet("font-size: 14px; color: #737373")
        header_top_heading_layout.addWidget(header_top_title)
        header_top_heading_layout.addWidget(header_top_desc)
