from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0  # Góc xoay
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)  # Cập nhật vòng lặp animation
        self.timer.start(30)  # Increased speed to 30ms for smoother animation
        self.setFixedSize(25, 25)  # Kích thước của widget
        self.show()  # Make widget visible by default

    def start_animation(self):
        self.timer.start(30)
        self.show()

    def stop_animation(self):
        self.timer.stop()
        self.hide()

    def update_animation(self):
        self.angle = (self.angle + 10) % 360  # Adjusted rotation speed
        self.update()  # Yêu cầu vẽ lại

    def paintEvent(self, event):
        # Vẽ vòng tròn bằng QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.white, 2)  # Increased line width
        painter.setPen(pen)

        rect = self.rect()
        painter.translate(rect.center())  # Đưa điểm (0, 0) về trung tâm
        painter.rotate(self.angle)  # Xoay góc

        # Vẽ cung tròn
        radius = (rect.width() - 10) // 2  # Adjusted radius size
        painter.drawArc(
            -radius, -radius, 2 * radius, 2 * radius, 0, 300 * 16
        )  # Extended arc length
