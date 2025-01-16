# Import built-in modules
import sys
import subprocess

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
from helpers.configuration import ConfigService
from helpers.logger import logger
from events import sync_event_emitter, UserActionEvent
from contexts.auth_context import auth_context


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

    def setup_ui(self):
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

        # Global overlay

        # region Menubar
        self.toolbar = AppToolBar(self)
        self.status_bar = StatusBar(self)
        self.side_toolbar = SideToolbar(self)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.status_bar)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.side_toolbar)

        self.app_layout = QHBoxLayout(self.container)
        self.app_layout.setSpacing(20)
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
        order_detail_label = QLabel("Chi tiết đơn hàng")
        order_detail_label.setObjectName("playground_section_title")
        order_table_widget = QWidget(self.container)
        order_table_widget.setLayout(order_table_layout)
        self.order_detail_table = OrderDetailTableWidget(self)
        order_table_layout.addWidget(order_detail_label)
        order_table_layout.addWidget(self.order_detail_table)
        self.playground.addWidget(order_table_widget)
        # endregion

        # region Sizing table detail
        sizing_table_layout = QVBoxLayout()
        sizing_table_layout.setContentsMargins(0, 0, 0, 0)
        sizing_table_layout.setSpacing(10)
        sizing_detail_lable = QLabel("Số lượng size đơn hàng")
        sizing_detail_lable.setObjectName("playground_section_title")
        sizing_table_widget = QWidget(self.container)
        sizing_table_widget.setLayout(sizing_table_layout)
        self.sizing_detail_table = SizingDetailTableWidget(self)
        sizing_table_layout.addWidget(sizing_detail_lable)
        sizing_table_layout.addWidget(self.sizing_detail_table)
        self.playground.addWidget(sizing_table_widget)
        # endregion

        # region Combine submission form
        self.combine_form_layout = QVBoxLayout()
        self.combine_form_layout.setSpacing(10)
        self.combine_form_widget = QWidget(self.container)
        self.combine_form_widget.setLayout(self.combine_form_layout)
        self.combine_form_label = QLabel("Thông tin phối đôi")
        self.combine_form_label.setObjectName("playground_section_title")
        self.combine_form_layout.addWidget(self.combine_form_label)
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
        self.setWindowTitle("EPC CI - v1.0.0 Beta")
        self.addToolBar(self.toolbar)

        QMetaObject.connectSlotsByName(self)
        self.retranslate_ui()

    def retranslate_ui(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "EPC CI - v1.0.0 Beta"))

    def on_app_shutdown(self):
        """
        Close reader connection on application shutdown
        """
        if hasattr(ui.epc_reader_playground, "uhf_reader_instance") and isinstance(
            ui.epc_reader_playground.uhf_reader_instance, GClient
        ):
            ui.epc_reader_playground.uhf_reader_instance.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # * Setup main window
    ui = MainWindow()
    ui.setup_ui()

    # * Setup global stylesheet for application
    with open("./themes/global.qss", "r", encoding="utf-8") as f:
        stylesheet = f.read()
        app.setStyleSheet(stylesheet)
    try:
        ui.show()
    except Exception as e:
        logger.error(e)

    def on_setting_update(e):
        ui.setEnabled(True)
        ui.toolbar.setting_window.close()
        ui.overlay.close()
        ui.close()
        subprocess.Popen([sys.executable] + sys.argv)
        app.quit()

    def check_authentication(data):
        if not data.get("is_authenticated"):
            ui.overlay = QWidget(ui)
            ui.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            ui.overlay.setGeometry(ui.rect())
            ui.overlay.show()
            login_dialog = LoginDialog(parent=ui)
            login_dialog.exec()
        else:
            ui.overlay.close()

    sync_event_emitter.on(
        UserActionEvent.SETTINGS_CHANGE.value,
    )(on_setting_update)

    sync_event_emitter.on(UserActionEvent.AUTH_STATE_CHANGE.value)(check_authentication)

    configuration = ConfigService.load_configs()
    if "" in configuration.values():
        ui.overlay = QWidget(ui)
        ui.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        ui.overlay.setGeometry(ui.rect())
        QMessageBox.warning(
            ui,
            "Cài đặt kết nối chưa được thiết lập",
            "Vui lòng cài đặt kết nối đến cơ sở dữ liệu và máy đọc UHF trước khi sử dụng ứng dụng.",
        )
        ui.toolbar.handle_show_settings_window()
        ui.toolbar.setting_window.setWindowFlag(
            Qt.WindowType.WindowCloseButtonHint, False
        )
    else:
        check_authentication(auth_context)

    # * Setup global font for application
    font_id = QFontDatabase.addApplicationFont("./assets/fonts/Inter-Regular.ttf")
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
        app.setFont(font)
        ui.setFont(font)
        QApplication.setFont(QFont("Inter"))

    # * Handle application shutdown
    app.aboutToQuit.connect(ui.on_app_shutdown)
    app.lastWindowClosed.connect(ui.on_app_shutdown)

    sys.exit(app.exec())
