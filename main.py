# Import built-in modules
import sys

# Import PyQt6 modules
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from uhf.reader import GClient

# Import widgets
from widgets.toolbar import AppToolBar
from widgets.status_bar import StatusBar
from widgets.order_detail_table import OrderDetailTableWidget
from widgets.sizing_detail_table import SizingDetailTableWidget
from widgets.order_autocomplete import OrderAutoCompleteWidget
from widgets.combine_form import CombineForm
from widgets.epc_reader_playground import EpcReaderPlayground
from widgets.login_dialog import LoginDialog
from widgets.side_toolbar import SideToolbar

# Import services
from helpers.configuration import ConfigService, ConfigSection
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent
from contexts.auth_context import auth_context
from i18n import I18nService, Language
from helpers.resolve_path import resolve_path


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()

        self.__app__ = app

        self.setObjectName("MainWindow")
        self.resize(1366, 768)
        self.setAutoFillBackground(True)

        # Global overlay
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.overlay.setGeometry(self.rect())

        # Import and setup separated widgets
        self.container = QWidget(parent=self)
        self.container.setObjectName("container")

        # region Menubar
        self.toolbar = AppToolBar(self)
        self.status_bar = StatusBar(self)
        self.side_toolbar = SideToolbar(self)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.status_bar)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.side_toolbar)

        self.app_layout = QHBoxLayout(self.container)
        self.app_layout.setSpacing(20)
        self.app_layout.setContentsMargins(20, 20, 20, 20)
        self.app_layout.setObjectName("app_layout")
        # endregion

        # region EPC List
        self.epc_reader_playground = EpcReaderPlayground(parent=self)
        self.app_layout.addWidget(self.epc_reader_playground)
        # endregion

        self.playground = QVBoxLayout()
        self.playground.setSpacing(30)
        self.playground.setObjectName("playground")

        # region Order autocomplete select
        self.mo_no_autocomplete = OrderAutoCompleteWidget(self)
        self.playground.addWidget(self.mo_no_autocomplete)
        # self.mo_no_autocomplete.handle_find_mo_no("")
        # endregion

        # region Order information table
        order_table_layout = QVBoxLayout()
        order_table_layout.setContentsMargins(0, 0, 0, 0)
        order_table_layout.setSpacing(10)
        self.order_detail_title = QLabel()
        self.order_detail_title.setObjectName("playground_section_title")
        order_table_widget = QWidget(self.container)
        order_table_widget.setLayout(order_table_layout)
        self.order_detail_table = OrderDetailTableWidget(self)
        order_table_layout.addWidget(self.order_detail_title)
        order_table_layout.addWidget(self.order_detail_table)
        self.playground.addWidget(order_table_widget)
        # endregion

        # region Sizing table detail
        sizing_table_layout = QVBoxLayout()
        sizing_table_layout.setContentsMargins(0, 0, 0, 0)
        sizing_table_layout.setSpacing(10)
        self.sizing_detail_title = QLabel()
        self.sizing_detail_title.setObjectName("playground_section_title")
        sizing_table_widget = QWidget(self.container)
        sizing_table_widget.setLayout(sizing_table_layout)
        self.sizing_detail_table = SizingDetailTableWidget(self)
        sizing_table_layout.addWidget(self.sizing_detail_title)
        sizing_table_layout.addWidget(self.sizing_detail_table)
        self.playground.addWidget(sizing_table_widget)
        # endregion

        # region Combine submission form
        self.combine_form_layout = QVBoxLayout()
        self.combine_form_layout.setSpacing(10)
        self.combine_form_layout.setContentsMargins(0, 0, 0, 0)
        self.combine_form_widget = QWidget(self.container)
        self.combine_form_widget.setLayout(self.combine_form_layout)
        self.combine_form_title = QLabel()
        self.combine_form_title.setObjectName("playground_section_title")
        self.combine_form_layout.addWidget(self.combine_form_title)
        self.combine_form = CombineForm(self)
        self.combine_form_layout.addWidget(self.combine_form)
        self.playground.addWidget(self.combine_form_widget)
        # endregion

        self.playground.setStretch(1, 1)
        self.playground.setStretch(2, 1)

        self.app_layout.addLayout(self.playground)
        self.app_layout.setStretch(0, 1)
        self.app_layout.setStretch(1, 3)

        self.setCentralWidget(self.container)
        self.setWindowTitle("EPC IC - v1.0.0 Beta")
        self.addToolBar(self.toolbar)

        QMetaObject.connectSlotsByName(self)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

        __event_emitter__.on(
            UserActionEvent.SETTINGS_CHANGE.value,
        )(self.reload)

        __event_emitter__.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            self.on_auth_state_change
        )

    def __translate__(self):
        self.order_detail_title.setText(I18nService.t("labels.order_detail_title"))
        self.sizing_detail_title.setText(I18nService.t("labels.order_detail_title"))
        self.combine_form_title.setText(I18nService.t("labels.combination_form_title"))

    # region Stylesheet setup
    def __set_stylesheet(self) -> None:
        """
        Set the stylesheet of the application to the global stylesheet.
        """
        with open(resolve_path("themes/global.qss"), "r", encoding="utf-8") as f:
            stylesheet = f.read()
            self.__app__.setStyleSheet(stylesheet)

    # region Font setup
    def __set_font(self) -> None:
        """
        Set the font of the application to Inter.
        """
        font_id = QFontDatabase.addApplicationFont(
            resolve_path("assets/fonts/Inter-Regular.ttf")
        )
        if font_id == -1:
            print("Failed to load font.")
            sys.exit(1)

        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            font = QFont(font_families[0])
            font.setFamilies(font_families)
            font.setFamily(font_families[0])
            font.setPixelSize(14)
            font.setWeight(QFont.Weight.Normal)
            self.__app__.setFont(font)
            self.setFont(font)
            QApplication.setFont(QFont("Inter"))

    def __ensure_connection_ready(self):
        configuration = ConfigService.load_configs()
        if "" in configuration.values():
            self.overlay = QWidget(self)
            self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            self.overlay.setGeometry(window.rect())
            self.overlay.show()
            QMessageBox.warning(
                self,
                I18nService.t("notification.settings_not_established_title"),
                I18nService.t("notification.settings_not_established_text"),
            )
            self.side_toolbar.open_setting_dialog()
            self.side_toolbar.setting_window.setWindowFlag(
                Qt.WindowType.WindowCloseButtonHint, False
            )
            return False

        return True

    # region Auth event handler
    def on_auth_state_change(self, data):
        if not data.get("is_authenticated"):
            self.overlay = QWidget(self)
            self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            self.overlay.setGeometry(self.rect())
            self.overlay.show()
            login_dialog = LoginDialog(parent=self)
            login_dialog.exec()
            return
        else:
            self.overlay.close()

    # region Bootstrapping application
    def on_application_bootstrap(self):
        """
        Bootstrap the application with the necessary configurations and settings.
        """

        self.__set_font()
        self.__set_stylesheet()

        # * Setup language
        current_language = ConfigService.get_conf(
            ConfigSection.LOCALE.value, "LANGUAGE", Language.ENGLISH.value
        )
        I18nService.set_language(current_language)
        I18nService.emit()

        if not self.__ensure_connection_ready():
            return

        self.show()
        self.on_auth_state_change(auth_context)

    # region Application shutdown
    def on_application_shutdown(self):
        """
        Close reader connection on application shutdown
        """
        if hasattr(self.epc_reader_playground, "uhf_reader_instance") and isinstance(
            self.epc_reader_playground.uhf_reader_instance, GClient
        ):
            self.epc_reader_playground.uhf_reader_instance.close()

    def reload(self):
        self.close()
        QMetaObject.invokeMethod(self.__app__, "quit", Qt.QueuedConnection)
        QProcess.startDetached(sys.executable, sys.argv)

    def bootstrap(self):
        self.on_application_bootstrap()


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        # * Setup main window
        window = MainWindow(app)
        window.bootstrap()

        app.aboutToQuit.connect(window.on_application_shutdown)
        app.lastWindowClosed.connect(window.on_application_shutdown)

        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        input("Press Enter to exit...")
