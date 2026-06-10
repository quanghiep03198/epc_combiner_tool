from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget

from events import UserActionEvent, __event_emitter__
from themes.theme_manager import ThemeManager
from widgets.loading_spinner import LoadingSpinner


class LoadingWidget:
    def __init__(self, parent):
        theme = ThemeManager()
        bg = QColor(theme.get_color("background"))

        self.overlay = QWidget(parent)
        self.overlay = QWidget(parent)
        self.overlay.setObjectName("overlay")
        self.overlay.setStyleSheet(
            f"background-color: rgba({bg.red()}, {bg.green()}, {bg.blue()}, 0.5);"
        )
        self.overlay.setGeometry(
            0, 0, parent.frameSize().width(), parent.frameSize().height()
        )
        self.loading_spinner = LoadingSpinner(parent)
        self.loading_spinner.move(
            int((parent.frameSize().width() - self.loading_spinner.width()) / 2),
            int((parent.frameSize().height() - self.loading_spinner.height()) / 2),
        )
        self.overlay.hide()
        self.loading_spinner.hide()

    def show_loading(self):
        self.overlay.show()
        self.loading_spinner.show()
        __event_emitter__.emit(UserActionEvent.LOADING_STATE_CHANGE.value, True)

    def close_loading(self):
        self.overlay.close()
        self.loading_spinner.close()
        __event_emitter__.emit(UserActionEvent.LOADING_STATE_CHANGE.value, False)
