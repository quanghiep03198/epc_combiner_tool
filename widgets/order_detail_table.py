from typing import Callable
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from repositories.order_repository import OrderRepository
from helpers.logger import logger
from contexts.combine_form_context import combine_form_context
from widgets.loading_widget import LoadingWidget
from i18n import I18nService
from events import UserActionEvent, __event_emitter__


class OrderDetailWorker(QRunnable):
    def __init__(self, param: str, callback: Callable[[list], None]):
        super().__init__()
        self.param = param
        self.callback = callback

    @pyqtSlot()
    def run(self):
        query_result = OrderRepository.get_order_detail(self.param)
        self.callback(query_result)


class OrderDetailTableWidget(QTableWidget):
    """
    Table for displaying order details
    """

    __order_detail_data = []

    def __init__(self, root: QWidget):
        super().__init__(
            root.container,
        )

        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 200)
        self.setColumnWidth(3, 200)
        self.setColumnWidth(4, 200)
        self.setColumnWidth(5, 200)
        self.setColumnWidth(6, 250)
        self.resizeColumnsToContents()
        self.setSortingEnabled(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.setCornerButtonEnabled(True)
        # self.setObjectName("tableWidget")
        self.setContentsMargins(4, 4, 4, 4)
        # self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setColumnCount(7)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setMinimumSectionSize(150)
        self.horizontalHeader().setStretchLastSection(False)
        self.verticalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setStretchLastSection(False)
        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setMidLineWidth(1)
        self.setSortingEnabled(False)
        self.verticalHeader().setVisible(False)

        self.empty_state_label = QLabel("No data available")
        self.empty_state_label.setStyleSheet("font-size: 16px; color: gray;")
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        __event_emitter__.on(UserActionEvent.MO_NO_CHANGE.value)(self.on_mo_no_change)
        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.MO_NOSEQ_CHANGE.value)(
            self.on_mo_noseq_change
        )

    def __translate__(self):
        horizontal_headers = [
            I18nService.t("fields.customer_order_code"),
            I18nService.t("fields.shoes_style_code"),
            I18nService.t("fields.shoes_style_code_factory"),
            I18nService.t("fields.mo_noseq"),
            I18nService.t("fields.or_no"),
            I18nService.t("fields.or_custpo"),
            I18nService.t("fields.mo_qty"),
        ]
        self.setColumnCount(len(horizontal_headers))
        self.setHorizontalHeaderLabels(horizontal_headers)

    def render_row(self, data):
        """
        Render order detail to table widget
        Scope:
            Private
        Args:
            data: List of order detail
        """
        self.setRowCount(0)
        row = 0
        for record in data:
            self.insertRow(row)

            # Assign value to table
            self.setItem(row, 0, QTableWidgetItem(str(record["shoestyle_codefactory"])))
            self.setItem(row, 1, QTableWidgetItem(str(record["mat_code"])))
            self.setItem(row, 2, QTableWidgetItem(str(record["cust_shoestyle"])))
            self.setItem(row, 3, QTableWidgetItem(str(record["mo_noseq"])))
            self.setItem(row, 4, QTableWidgetItem(str(record["or_no"])))
            self.setItem(row, 5, QTableWidgetItem(str(record["or_custpo"])))
            self.setItem(row, 6, QTableWidgetItem(str(int(record["size_qty"]))))

            row += 1

        if len(data) == 0:
            self.empty_state_label.show()

        self.resizeColumnsToContents()

    def on_mo_noseq_change(self, selected_mo_noseq: str):
        if selected_mo_noseq == "all":
            self.render_row(self.__order_detail_data)
        else:
            filtered_data = list(
                filter(
                    lambda item: item["mo_noseq"] == selected_mo_noseq,
                    self.__order_detail_data,
                )
            )
            self.render_row(filtered_data)

    def on_mo_no_change(self, data):
        try:
            self.loading = LoadingWidget(self)
            self.loading.show_loading()
            worker = OrderDetailWorker(data, self.handle_query_result)
            QThreadPool.globalInstance().start(worker)

        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")
            return None

    def handle_query_result(self, query_result):
        self.setRowCount(0)

        if len(query_result) > 0:
            combine_form_context["mat_code"] = query_result[0]["mat_code"]
            combine_form_context["shoestyle_codefactory"] = query_result[0][
                "shoestyle_codefactory"
            ]
            combine_form_context["or_no"] = query_result[0]["or_no"]
            combine_form_context["or_custpo"] = query_result[0]["or_custpo"]
            combine_form_context["cust_shoestyle"] = query_result[0]["cust_shoestyle"]
        # Store order detail data
        __event_emitter__.emit(
            UserActionEvent.GET_ORDER_DETAIL_SUCCESS.value,
            list(map(lambda item: item["mo_noseq"], query_result)),
        )
        self.__order_detail_data = query_result
        # Render order detail to UI

        self.render_row(query_result)

        self.loading.close_loading()
