from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from pyqttoast import *

from themes.theme_manager import ThemeManager


class Toaster(Toast):
    def __init__(
        self,
        parent: QMainWindow,
        title: str | None,
        text: str | None,
        preset: ToastPreset = ToastPreset.INFORMATION_DARK,
        duration: int = 3000,
    ):
        super().__init__(parent)

        theme = ThemeManager()

        self.setTitle(title)
        self.setText(text)
        self.applyPreset(preset)
        self.setBorderRadius(4)
        self.setTitleFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.setTextFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.setSpacing(10)
        self.setMinimumWidth(300)
        self.setMaximumWidth(800)
        self.setMinimumHeight(50)
        self.setMaximumHeight(200)
        self.setPositionRelativeToWidget(parent)
        self.setPosition(ToastPosition.TOP_RIGHT)
        self.setBackgroundColor(QColor(theme.get_color("background")))
        self.setTitleColor(QColor(theme.get_color("foreground")))
        self.setTextColor(QColor(theme.get_color("card-foreground")))
        self.setIconSeparatorColor(QColor(theme.get_color("border")))
        self.setCloseButtonIconColor(QColor(theme.get_color("muted-foreground")))
        self.setShowDurationBar(True)
        self.setTextSectionSpacing(4)
        self.setContentsMargins(10, 10, 10, 10)
        self.setResetDurationOnHover(False)
        self.setDuration(duration)
        self.setTextSectionMarginRight(10)
        self.setIconSectionMarginRight(10)
