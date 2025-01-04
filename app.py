import sys

from pathlib import Path
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from uhf.reader import *

# Import Database initialization
from database import DATA_SOURCE_ERP, DATA_SOURCE_DL

# Import data sources
from repositories.sizing_repository import SizingRepository
from repositories.order_repository import OrderRepository

# Import widgets
from widgets.menubar import AppMenuBar
from widgets.order_detail_table import OrderDetailTableWidget
from widgets.sizing_detail_table import SizingDetailTableWidget
from widgets.order_autocomplete import OrderAutoCompleteWidget
from widgets.playground_heading_text import PlaygroundHeading
from widgets.combine_form import CombineForm
from widgets.epc_reader_playground import EpcReaderPlayground


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sizing_repository = SizingRepository(DATA_SOURCE_ERP)
        self.order_repository = OrderRepository(DATA_SOURCE_ERP)

    def setup_ui(self):
        self.setObjectName("MainWindow")
        self.resize(1366, 768)

        self.setAutoFillBackground(True)
        # * Setup global font for application
        font_id = QFontDatabase.addApplicationFont("./assets/fonts/Inter-Medium.ttf")
        if font_id == -1:
            print("Failed to load font.")
            sys.exit(1)

        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            print(f"Loaded font: {font_families[0]}")
            self.setFont(QFont(font_families[0], 14))

        self.setStyleSheet(Path("./themes/global.qss").read_text())

        # Import and setup separated widgets

        self.container = QWidget(parent=self)
        self.container.setObjectName("container")

        # GLobal loading widget
        # self.loading = LoadingWidget(self, '')

        # region Menubar
        self.menubar = AppMenuBar(self)
        self.setMenuBar(self.menubar)

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
        self.playground_header_layout = QHBoxLayout()
        self.playground_header_layout.setContentsMargins(0, 0, 0, 0)
        self.playground_header_layout.setSpacing(50)
        self.playground_header_layout.setStretch(0, 3)
        self.playground_header_layout.setStretch(1, 0)
        self.playground_header = QFrame(parent=self.container)
        self.playground_header.setLayout(self.playground_header_layout)

        self.playground_heading_text = PlaygroundHeading()
        self.playground_header_layout.addWidget(self.playground_heading_text)
        self.playground_header_layout.addWidget(self.mo_no_autocomplete)

        self.playground.addWidget(self.playground_header)
        self.mo_no_autocomplete.handle_find_mo_no("")
        # endregion

        # region Order information table
        order_table_layout = QVBoxLayout()
        order_table_layout.setContentsMargins(0, 0, 0, 0)
        order_table_layout.setSpacing(10)
        order_detail_lable = QLabel("Chi tiêt đơn hàng")
        order_detail_lable.setStyleSheet("font-size: 16px; font-weight: bold;")
        order_table_widget = QWidget(self.container)
        order_table_widget.setLayout(order_table_layout)
        self.order_detail_table = OrderDetailTableWidget(self, self.order_repository)
        order_table_layout.addWidget(order_detail_lable)
        order_table_layout.addWidget(self.order_detail_table)
        self.playground.addWidget(order_table_widget)
        # endregion

        # region Sizing table detail
        sizing_table_layout = QVBoxLayout()
        sizing_table_layout.setContentsMargins(0, 0, 0, 0)
        sizing_table_layout.setSpacing(10)
        sizing_detail_lable = QLabel("Số lượng cỡ giày")
        sizing_detail_lable.setStyleSheet("font-size: 16px; font-weight: bold;")
        sizing_table_widget = QWidget(self.container)
        sizing_table_widget.setLayout(sizing_table_layout)
        self.sizing_detail_table = SizingDetailTableWidget(self)
        sizing_table_layout.addWidget(sizing_detail_lable)
        sizing_table_layout.addWidget(self.sizing_detail_table)
        self.playground.addWidget(sizing_table_widget)
        # endregion

        # region Combine submission form
        self.combine_form = CombineForm(self.container)
        self.playground.addWidget(self.combine_form)
        # endregion

        self.playground.setStretch(1, 1)
        self.playground.setStretch(2, 1)

        self.app_layout.addLayout(self.playground)
        self.app_layout.setStretch(0, 1)
        self.app_layout.setStretch(1, 3)

        self.setCentralWidget(self.container)
        self.setWindowTitle("EPC Combiner Tool")
        QMetaObject.connectSlotsByName(self)
        # self.retranslate_ui(MainWindow)

    # Handle multi-language for application
    # def retranslate_ui(self, MainWindow):
    #     _translate = QCoreApplication.translate
    #     pass

    def on_app_shutdown(self):
        """
        Close reader connection on application shutdown
        """
        if hasattr(self.epc_reader_playground, "uhf_reader_instance"):
            self.epc_reader_playground.uhf_reader_instance.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # * Setup main window
    ui = Ui_MainWindow()
    ui.setup_ui()
    ui.show()

    # * Handle application shutdown
    app.aboutToQuit.connect(ui.on_app_shutdown)
    app.lastWindowClosed.connect(ui.on_app_shutdown)

    sys.exit(app.exec())
