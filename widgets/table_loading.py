from PyQt6.QtWidgets import QWidget
from widgets.loading_spinner import LoadingSpinner


class TableLoading:
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

    def close_loading(self):
        self.overlay.close()
        self.loading_spinner.close()
