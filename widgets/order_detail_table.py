import asyncio
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from repositories.order_repository import OrderRepository
from helpers.logger import logger
from contexts.combine_form_context import combine_form_context
from concurrent.futures import ThreadPoolExecutor

# from widgets.order_autocomplete import mo_no_change_event
from events import UserActionEvent, async_event_emitter, sync_event_emitter


class OrderDetailTableWidget(QTableWidget):
    """
    Table for displaying order details
    """

    def __init__(self, root: QWidget, order_repository: OrderRepository):
        super().__init__(
            root.container,
        )
        self.executor = ThreadPoolExecutor()
        self.order_detail_data: list = []
        self.order_repository = order_repository

        horizontal_headers = [
            "Đặt đơn của khách",
            "Mã hình thể",
            "Hình thể xưởng",
            "Tiểu chỉ lệnh",
            "Mã đơn hàng",
            "Mã đặt đơn",
            "Số lượng đặt hàng",
        ]
        self.setColumnCount(len(horizontal_headers))
        self.setHorizontalHeaderLabels(horizontal_headers)
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
        self.setObjectName("tableWidget")
        self.setContentsMargins(4, 4, 4, 4)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
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

        async_event_emitter.on(UserActionEvent.MO_NO_CHANGE.value)(self.on_mo_no_change)
        sync_event_emitter.on(UserActionEvent.MO_NOSEQ_CHANGE.value)(
            self.on_mo_noseq_change
        )

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

    def on_mo_noseq_change(self, selected_mo_noseq: str):
        logger.debug(selected_mo_noseq)
        if selected_mo_noseq == "all":
            self.render_row(self.order_detail_data)
        else:
            filtered_data = list(
                filter(
                    lambda item: item["mo_noseq"] == selected_mo_noseq,
                    self.order_detail_data,
                )
            )
            self.render_row(filtered_data)

    async def on_mo_no_change(self, data):
        try:
            # Reset table row on selected order change
            self.setRowCount(0)
            # Get order detail from database

            query_result = await self.order_repository.get_order_detail(data)

            logger.debug(query_result)

            if len(query_result) > 0:
                combine_form_context["mat_code"] = query_result[0]["mat_code"]
                combine_form_context["shoestyle_codefactory"] = query_result[0][
                    "shoestyle_codefactory"
                ]
                combine_form_context["or_no"] = query_result[0]["or_no"]
                combine_form_context["or_custpo"] = query_result[0]["or_custpo"]
                combine_form_context["cust_shoestyle"] = query_result[0][
                    "cust_shoestyle"
                ]
            # Store order detail data
            self.order_detail_data = query_result
            # Render order detail to UI
            self.render_row(query_result)

        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")
            return None
