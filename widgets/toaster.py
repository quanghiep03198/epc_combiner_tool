from pyqttoast import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


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

        self.setTitle(title)
        self.setText(text)
        self.applyPreset(preset)
        self.setBorderRadius(4)
        self.setTitleFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.setTextFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.setSpacing(10)
        self.setMinimumWidth(100)
        self.setMaximumWidth(300)
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)
        self.setPositionRelativeToWidget(parent)
        self.setPosition(ToastPosition.TOP_RIGHT)
        self.setBackgroundColor(QColor("#0a0a0a"))
        self.setTitleColor(QColor("#fafafa"))
        self.setTextColor(QColor("#f5f5f5"))
        self.setIconSeparatorColor(QColor("#292524"))
        self.setCloseButtonIconColor(QColor("#737373"))
        self.setShowDurationBar(False)
        self.setTextSectionSpacing(4)
        self.setContentsMargins(10, 10, 10, 10)
        self.setResetDurationOnHover(False)
        self.setDuration(duration)
        self.setTextSectionMarginRight(10)
        self.setIconSectionMarginRight(10)
