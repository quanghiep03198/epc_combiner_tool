from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import Callable

from repositories.sizing_repository import SizingRepository
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent
from widgets.loading_widget import LoadingWidget
from i18n import I18nService

from contexts.combine_form_context import combine_form_context


class FetchSizeDataWorker(QRunnable):
    def __init__(self, param: str, callback: Callable[[list[dict]], None]):
        super().__init__()
        self.param = param
        self.callback = callback

    @pyqtSlot()
    def run(self):
        query_result = SizingRepository.find_size_qty(self.param)
        self.callback(query_result)


class SizingDetailTableWidget(QTableWidget):
    """
    Table for displaying sizing details
    """

    def __init__(self, root):
        super().__init__(root.container)
        self.root = root

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
        # self.setRowCount(len(self._vertical_header_labels))
        # self.setVerticalHeaderLabels(self._vertical_header_labels)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )
        __event_emitter__.on(UserActionEvent.MO_NO_CHANGE.value)(
            self.handle_fetch_size_data
        )
        __event_emitter__.on(UserActionEvent.NG_EPC_MUTATION.value)(
            lambda _: self.handle_fetch_size_data(combine_form_context["mo_no"])
        )

    def __translate__(self):
        vertical_header_labels: list[str] = [
            I18nService.t("fields.size_numcode"),
            I18nService.t("fields.size_qty"),
            I18nService.t("fields.combined_qty"),
            I18nService.t("fields.in_use_qty"),
            I18nService.t("fields.compensated_qty"),
            I18nService.t("fields.cancelled_qty"),
        ]
        self.setRowCount(len(vertical_header_labels))
        self.setVerticalHeaderLabels(vertical_header_labels)

    def handle_fetch_size_data(self, data: str):
        try:
            self.loading = LoadingWidget(self)
            self.loading.show_loading()
            worker = FetchSizeDataWorker(data, self.handle_render_row)
            QThreadPool.globalInstance().start(worker)

        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")

    def handle_render_row(self, result: list[dict]):
        self.setColumnCount(len(result))
        __event_emitter__.emit(UserActionEvent.SIZE_LIST_CHANGE.value, result)
        col: int = 0
        for record in result:
            self.setItem(0, col, QTableWidgetItem(str(record["size_numcode"])))
            self.setItem(1, col, QTableWidgetItem(str(record["size_qty"])))
            self.setItem(2, col, QTableWidgetItem(str(record["combined_qty"])))
            self.setItem(3, col, QTableWidgetItem(str(record["in_use_qty"])))
            self.setItem(4, col, QTableWidgetItem(str(record["compensated_qty"])))
            self.setItem(5, col, QTableWidgetItem(str(record["cancelled_qty"])))
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
