from PyQt6.QtWidgets import QToolButton, QToolBar, QApplication, QMainWindow
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QRect, QSize, Qt


class CustomToolButton(QToolButton):
    def paintEvent(self, event):
        painter = QPainter(self)

        # Vẽ biểu tượng (icon)
        icon_size = self.iconSize()
        icon_rect = QRect(
            8,
            (self.height() - icon_size.height()) // 2,
            icon_size.width(),
            icon_size.height(),
        )
        painter.drawPixmap(icon_rect, self.icon().pixmap(icon_size))

        # Vẽ text (tùy chỉnh khoảng cách)
        text_offset = icon_rect.right() + 12  # Điều chỉnh khoảng cách giữa icon và text
        painter.drawText(
            text_offset,
            0,
            self.width() - text_offset,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )
