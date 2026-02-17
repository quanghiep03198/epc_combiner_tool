# Import built-in modules
import sys
import os
import signal
import atexit

# Import PyQt6 modules
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from uhf.reader import GClient
import random

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
from widgets.refresh_button import RefreshButton

# Import services
from helpers.configuration import ConfigService, ConfigSection
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent
from contexts.auth_context import auth_context
from i18n import I18nService, Language
from helpers.resolve_path import resolve_path
from database import db_service
from themes.theme_manager import theme_manager
from themes.colors import Theme

# from version import get_latest_release_version
from helpers.version import version_info


class MainWindow(QMainWindow):
    singleton: "MainWindow" = None

    def __init__(self, app: QApplication):
        super().__init__()

        self.__app__ = app

        self.setObjectName("MainWindow")
        self.resize(1440, 860)
        self.setAutoFillBackground(True)

        # Global overlay
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.overlay.setGeometry(self.rect())

        # Import and setup separated widgets
        self.container = QWidget()
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
        self.top_layout = QHBoxLayout()
        self.top_layout.setObjectName("top_layout")
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(8)
        self.top_layout_widget = QWidget(self.container)
        self.top_layout_widget.setLayout(self.top_layout)
        self.refetch_button = RefreshButton(self.top_layout_widget)
        self.mo_no_autocomplete = OrderAutoCompleteWidget(self)
        self.top_layout.addWidget(self.mo_no_autocomplete)
        self.top_layout.addWidget(self.refetch_button)
        self.playground.addWidget(self.top_layout_widget)
        # self.mo_no_autocomplete.handle_find_mo_no("")
        # endregion

        # region Order information table
        order_table_layout = QVBoxLayout()
        order_table_layout.setContentsMargins(0, 0, 0, 0)
        order_table_layout.setSpacing(10)
        self.order_detail_title = QLabel()
        self.order_detail_title.setObjectName("playground_section_title")
        order_table_widget = QWidget()
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
        sizing_table_widget = QWidget()
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
        self.combine_form_widget = QWidget()
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
        # Set window title with version
        self.setWindowIcon(QIcon(resolve_path("./icon.ico")))
        self.setWindowTitle(f"EPC Information Combiner {version_info}")

        # Log version info
        logger.info(f"Starting EPC Information Combiner {version_info}")
        logger.info(
            f"Build: {version_info.build_type} | Commit: {version_info.commit_hash}"
        )
        self.addToolBar(self.toolbar)

        QMetaObject.connectSlotsByName(self)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

        __event_emitter__.on(
            UserActionEvent.SETTINGS_CHANGE.value,
        )(self.restart_application)

        __event_emitter__.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            self.on_auth_state_change
        )

        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(self.on_theme_change)

        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()

    def __translate__(self):
        self.order_detail_title.setText(I18nService.t("labels.order_detail_title"))
        self.sizing_detail_title.setText(
            I18nService.t("labels.combination_detail_title")
        )
        self.combine_form_title.setText(I18nService.t("labels.combination_form_title"))

    # region Stylesheet setup
    def __set_stylesheet(self) -> None:
        """
        Set the stylesheet of the application using ThemeManager.
        """
        # Load theme from config
        theme_value = ConfigService.get_conf(
            ConfigSection.UI.value, "theme", Theme.DARK.value
        )
        try:
            theme = Theme(theme_value)
        except ValueError:
            theme = Theme.DARK

        # Apply theme using ThemeManager
        theme_manager.apply_theme(self.__app__, theme)

        # Emit theme change event to update all widgets
        __event_emitter__.emit(UserActionEvent.THEME_CHANGE.value, theme)

    # region Font setup
    def __set_font(self) -> None:
        """
        Set the font of the application to Inter.
        """
        font_id = QFontDatabase.addApplicationFont(
            resolve_path("assets/fonts/Inter-Regular.ttf")
        )
        if font_id == -1:
            logger.error("Failed to load font.")
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

    def on_theme_change(self, theme: Theme):
        """
        Handle theme change event

        Args:
            theme: New theme to apply
        """
        # Save theme to config
        ConfigService.set_conf(ConfigSection.UI.value, "theme", theme.value)
        # Apply theme
        theme_manager.apply_theme(self.__app__, theme)

    # region Bootstrapping application
    def on_application_bootstrap(self):
        """
        Bootstrap the application with the necessary configurations and settings.
        """

        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()

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

    def disconnect_reader(reader_name):
        pass

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.graceful_shutdown()

        # Register signal handlers (Windows)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, signal_handler)

        # Register exit handler
        atexit.register(self.cleanup_on_exit)

    def graceful_shutdown(self):
        """Perform graceful shutdown operations"""
        try:
            logger.info("Starting graceful shutdown...")

            # Close any open dialogs
            for widget in QApplication.allWidgets():
                if isinstance(widget, QDialog) and widget.isVisible():
                    widget.close()

            # Disconnect from database
            try:
                db_service.close_connection()
                logger.info("Database connection closed")
            except:
                pass

            # Close main window
            self.close()

            # Quit application
            QApplication.quit()

        except Exception as e:
            print(f"Error during graceful shutdown: {e}")
        finally:
            # Force exit if needed
            sys.exit(0)

    def cleanup_on_exit(self):
        """Cleanup function called on exit"""
        try:
            logger.info("Performing exit cleanup...")
            # Any additional cleanup code here
        except:
            pass

    def closeEvent(self, event):
        """Override close event for proper cleanup"""
        try:
            logger.info("Main window closing...")

            # Save any pending data
            # Close database connections
            try:
                db_service.close_connection()
            except:
                pass

            # Accept the close event
            event.accept()

            # Ensure application quits
            QApplication.quit()

        except Exception as e:
            print(f"Error during close event: {e}")
            event.accept()  # Accept anyway

    # region Application shutdown
    def on_application_shutdown(self):
        """
        Close reader connection on application shutdown
        """
        if hasattr(self.epc_reader_playground, "uhf_reader_instance") and isinstance(
            self.epc_reader_playground.uhf_reader_instance, GClient
        ):
            self.epc_reader_playground.uhf_reader_instance.callTcpDisconnect
        db_service.close_all_connections()
        # Ensure the application exits completely
        self.__app__.quit()
        os._exit(0)

    # def restart_app(self):

    def restart_application(self):
        os.execl(sys.executable, sys.executable, *sys.argv)

    def bootstrap(self):
        self.on_application_bootstrap()


if __name__ == "__main__":
    app_ref: int = random.randint(1, 100000)
    try:
        app = QApplication(sys.argv)

        # * Setup main window
        window = MainWindow(app)
        window.bootstrap()

        app.aboutToQuit.connect(window.on_application_shutdown)
        app.lastWindowClosed.connect(window.on_application_shutdown)

        app_ref = app.exec()
        sys.exit(app_ref)
        os._exit(app_ref)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        input("Press Enter to exit...")
