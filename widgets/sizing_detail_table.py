from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import Callable

from repositories.sizing_repository import SizingRepository
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent
from widgets.loading_widget import LoadingWidget
from i18n import I18nService, I18nContext

from contexts.combine_form_context import combine_form_context


class FetchSizeDataWorker(
    QRunnable,
):
    def __init__(self, params: dict, callback: Callable[[list[dict]], None]):
        super().__init__()
        self.mo_no = params["mo_no"]
        self.mo_noseq = params["mo_noseq"]
        self.callback = callback

    @pyqtSlot()
    def run(self):
        query_result = SizingRepository.find_size_qty(
            {"mo_no": self.mo_no, "mo_noseq": self.mo_noseq}
        )
        self.callback(query_result)


class SizingDetailTableWidget(QTableWidget, I18nContext):
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
            lambda _: self.handle_fetch_size_data(
                {
                    "mo_no": combine_form_context["mo_no"],
                    "mo_noseq": combine_form_context["mo_noseq"],
                }
            )
        )
        __event_emitter__.on(UserActionEvent.NG_EPC_MUTATION.value)(
            lambda _: self.handle_fetch_size_data(
                {
                    "mo_no": combine_form_context["mo_no"],
                    "mo_noseq": combine_form_context["mo_noseq"],
                }
            )
        )
        __event_emitter__.on(UserActionEvent.MO_NOSEQ_CHANGE.value)(
            lambda value: self.handle_fetch_size_data(
                {
                    "mo_no": combine_form_context["mo_no"],
                    "mo_noseq": value,
                }
            )
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

    def handle_fetch_size_data(self, data: dict):
        try:
            self.loading = LoadingWidget(self)
            self.loading.show_loading()
            worker = FetchSizeDataWorker(data, self.handle_render_row)
            QThreadPool.globalInstance().start(worker)

        except Exception as e:
            logger.error(f"[SizingDetailTableWidget] Error reading SQL file: {e}")

    def handle_render_row(self, result: list[dict]):
        try:
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
                self.handle_highlight_qty(
                    3, col, record["size_qty"], record["in_use_qty"]
                )
                col += 1
        except Exception as e:
            logger.error(e)

        finally:
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
