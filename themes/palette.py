from PyQt6.QtGui import *
from PyQt6.QtCore import *


def create_palette():
    palette = QPalette()
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Light, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Midlight, brush)
    brush = QBrush(QColor(127, 127, 127))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark, brush)
    brush = QBrush(QColor(170, 170, 170))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid, brush)
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText, brush)
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, brush)
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush)
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush)
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Shadow, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.AlternateBase,
        brush,
    )
    brush = QBrush(QColor(255, 255, 220))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.ToolTipBase,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.ToolTipText,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0, 128))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.PlaceholderText,
        brush,
    )
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.WindowText,
        brush,
    )
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Light, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Midlight, brush)
    brush = QBrush(QColor(127, 127, 127))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Dark, brush)
    brush = QBrush(QColor(170, 170, 170))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Mid, brush)
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.BrightText,
        brush,
    )
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.ButtonText,
        brush,
    )
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush)
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush)
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Shadow, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.AlternateBase,
        brush,
    )
    brush = QBrush(QColor(255, 255, 220))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.ToolTipBase,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.ToolTipText,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0, 128))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.PlaceholderText,
        brush,
    )
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        brush,
    )
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Light, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Midlight, brush)
    brush = QBrush(QColor(127, 127, 127))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Dark, brush)
    brush = QBrush(QColor(170, 170, 170))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Mid, brush)
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.BrightText,
        brush,
    )
    brush = QBrush(QColor(38, 38, 38))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        brush,
    )
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush)
    brush = QBrush(QColor(245, 245, 245))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, brush)
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Shadow, brush)
    brush = QBrush(QColor(255, 255, 255))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.AlternateBase,
        brush,
    )
    brush = QBrush(QColor(255, 255, 220))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ToolTipBase,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ToolTipText,
        brush,
    )
    brush = QBrush(QColor(0, 0, 0, 128))
    brush.setStyle(Qt.BrushStyle.SolidPattern)

    palette.setBrush(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.PlaceholderText,
        brush,
    )

    return palette
