from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from repositories.sizing_repository import SizingRepository
from helpers.logger import logger
from events import sync_event_emitter, UserActionEvent
from widgets.table_loading import TableLoading


class FetchSizeDataWorker(QRunnable):
    def __init__(self, data, callback):
        super().__init__()
        self.data = data
        self.callback = callback

    @pyqtSlot()
    def run(self):
        query_result = SizingRepository.find_size_qty(self.data)
        self.callback(query_result)


class SizingDetailTableWidget(QTableWidget):
    """
    Table for displaying sizing details
    """

    _size_list: list[dict] = []
    _current_mo_no: str = None

    def __init__(self, root):
        super().__init__(root.container)
        self.root = root

        self.setRowCount(5)
        self.setContentsMargins(2, 2, 2, 2)
        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setMidLineWidth(1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.setVerticalHeaderLabels(
            [
                "Cỡ giày",
                "Số lượng đặt đơn",
                "Tem đã phối",
                "Đang sử dụng",
                "Đã hủy",
            ]
        )

        sync_event_emitter.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )
        sync_event_emitter.on(UserActionEvent.MO_NO_CHANGE.value)(
            self.handle_fetch_size_data
        )

    def handle_fetch_size_data(self, data: str):
        try:
            self.loading = TableLoading(self)
            self.loading.show_loading()
            worker = FetchSizeDataWorker(data, self.handle_render_row)
            QThreadPool.globalInstance().start(worker)

        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")

    def handle_render_row(self, result: list[dict]):
        # if not result:
        #     logger.warning("No sizing detail found")
        #     return
        self.setColumnCount(len(result))
        self._size_list = result
        sync_event_emitter.emit(UserActionEvent.SIZE_LIST_CHANGE.value, result)
        col: int = 0
        for record in result:
            self.setItem(0, col, QTableWidgetItem(str(record["size_numcode"])))
            self.setItem(1, col, QTableWidgetItem(str(record["size_qty"])))
            self.setItem(2, col, QTableWidgetItem(str(record["combined_qty"])))
            self.setItem(3, col, QTableWidgetItem(str(record["in_use_qty"])))
            self.setItem(4, col, QTableWidgetItem(str(record["cancelled_qty"])))
            self.handle_highlight_qty(
                2, col, record["size_qty"], record["combined_qty"]
            )
            self.handle_highlight_qty(3, col, record["size_qty"], record["in_use_qty"])
            col += 1

        self.loading.close_loading()

    def on_combined_epc_created(self, data):
        self.handle_fetch_size_data(data["mo_no"])

    def handle_highlight_qty(
        self, row: int, col: int, original_qty: int, actual_qty: int
    ):
        if actual_qty == original_qty:
            self.item(row, col).setForeground(QBrush(QColor("#22c55e")))
        elif actual_qty > original_qty:
            self.item(row, col).setForeground(QBrush(QColor("#ef4444")))
        else:
            self.item(row, col).setForeground(QBrush(QColor("#eab308")))
