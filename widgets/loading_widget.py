from PyQt6.QtWidgets import QWidget
from widgets.loading_spinner import LoadingSpinner
from events import __event_emitter__, UserActionEvent


class LoadingWidget:
    def __init__(self, parent):
        self.overlay = QWidget(parent)
        self.overlay = QWidget(parent)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
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
