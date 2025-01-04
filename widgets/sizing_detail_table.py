import asyncio
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from repositories.sizing_repository import SizingRepository
from helpers.logger import logger
from events import async_event_emitter, sync_event_emitter, UserActionEvent
from concurrent.futures import ThreadPoolExecutor
from database import DATA_SOURCE_ERP


class SizingDetailTableWidget(QTableWidget):
    """
    Table for displaying sizing details
    """

    _size_list = []

    def __init__(self, root):
        super().__init__(root.container)
        self.executor = ThreadPoolExecutor()
        self.sizing_repository = SizingRepository(DATA_SOURCE_ERP)

        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setMidLineWidth(1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(True)
        self.setRowCount(6)
        self.setContentsMargins(2, 2, 2, 2)
        self.setVerticalHeaderLabels(
            [
                "Cỡ giày",
                "Số lượng đặt đơn",
                "Tem đã phối",
                "Đang sử dụng",
                "Đã hủy",
                "Tem khách",
            ]
        )

        sync_event_emitter.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )
        async_event_emitter.on(UserActionEvent.MO_NO_CHANGE.value)(self.on_mo_no_change)

    async def on_mo_no_change(self, data):
        try:
            result = await self.sizing_repository.find_size_qty(data)

            if not result:
                logger.warning("No sizing detail found")
                return
            self.setColumnCount(len(result))
            self._size_list = result
            sync_event_emitter.emit(UserActionEvent.SIZE_LIST_CHANGE.value, result)
            col = 0
            for record in result:
                self.setItem(0, col, QTableWidgetItem(str(record["size_numcode"])))
                self.setItem(1, col, QTableWidgetItem(str(record["size_qty"])))
                self.setItem(2, col, QTableWidgetItem(str(0)))
                self.setItem(3, col, QTableWidgetItem(str(0)))
                self.setItem(4, col, QTableWidgetItem(str(0)))
                self.setItem(5, col, QTableWidgetItem(str(0)))
                col += 1

        except Exception as e:
            logger.error(f"Error reading SQL file: {e}")

    def on_combined_epc_created(self, data):
        size_item = next(
            (item for item in self._size_list if item["size_numcode"] == data["size"]),
            None,
        )
        for col in range(self.columnCount()):
            if self.item(0, col) and self.item(0, col).text() == data["size"]:
                self.item(2, col).setText(str(data["qty"]))
                if size_item["size_qty"] == data["qty"]:
                    self.item(2, col).setForeground(QBrush(QColor("#22c55e")))
                else:
                    self.item(2, col).setForeground(QBrush(QColor("#eab308")))
                break
        logger.debug(data)
        pass
