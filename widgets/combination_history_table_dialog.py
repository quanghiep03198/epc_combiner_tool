from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class CombinationHistoryTableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lịch sử phối")
        self.resize(800, 600)

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["EPC", "Chỉ lệnh", "Size", "Ngày Phối", "Trạm Đang Sử Dụng"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

    def set_data(self, data: list[dict[str, str]]):
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row["EPC"]))
            self.table.setItem(i, 1, QTableWidgetItem(row["Chỉ lệnh"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["Size"]))
            self.table.setItem(i, 3, QTableWidgetItem(row["Ngày Phối"]))
