import asyncio
import types
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from asyncio import Queue
from uhf.reader import *
from helpers.logger import logger
from repositories.rfid_repository import RFIDRepository
from database import DATA_SOURCE_DL

# Import widgets
from widgets.custom_message_box import CustomMessageBox
from widgets.loading import LoadingWidget

from events import UserActionEvent, sync_event_emitter
import json

# lock = threading.Lock()


class EpcReaderPlayground(QFrame):
    """
    EPC reader widget for scanning EPC from UHF reader
    """

    _connection_status: bool = False
    _play_state: bool = False
    _epc_count: int = 0
    _max_epc_qty: int = 0
    _epc_datalist: list[str] = []
    _has_over_qty_alert: bool = False

    PAGE_SIZE = 100
    _current_page = 1
    _total_page = 1
    _has_next_page = False
    _has_prev_page = False
    # uhf_reader_instance: GClient

    def __init__(self, parent):
        super().__init__(parent)
        self.rfid_repository = RFIDRepository(DATA_SOURCE_DL)

        self.setObjectName("epc_reader_playground")
        self.setAutoFillBackground(True)
        self.epc_reader_layout = QVBoxLayout(self)
        self.epc_reader_layout.setContentsMargins(2, 2, 2, 2)
        self.epc_reader_layout.setSpacing(6)

        self.setLayout(self.epc_reader_layout)
        # region EPC counter box
        self.epc_counter_box = QFrame(parent=self)
        self.epc_counter_box.setObjectName("epc_counter_box")
        self.epc_counter_box_layout = QHBoxLayout()

        self.epc_counter_box_layout.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.epc_counter_box_layout.setContentsMargins(0, 0, 0, 0)

        self.epc_counter_box.setLayout(self.epc_counter_box_layout)
        self.epc_counter_box.setStyleSheet(
            """
            #epc_counter_box{
                padding: 2px;
                border-radius: 4px;
            }
            """
        )

        self.label_group_layout_1 = QHBoxLayout()
        self.label_group_layout_2 = QHBoxLayout()
        self.label_group_layout_3 = QHBoxLayout()

        self.label_group_layout_1.setSpacing(4)
        self.label_group_layout_2.setSpacing(4)
        self.label_group_layout_3.setSpacing(4)

        self.label_group_layout_1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label_group_layout_2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label_group_layout_3.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.label_group_1 = QFrame(parent=self.epc_counter_box)
        self.label_group_2 = QFrame(parent=self.epc_counter_box)
        self.label_group_3 = QFrame(parent=self.epc_counter_box)

        self.label_group_1.setLayout(self.label_group_layout_1)
        self.label_group_2.setLayout(self.label_group_layout_2)
        self.label_group_3.setLayout(self.label_group_layout_3)

        self.scanned_epc_counter_label = QLabel(parent=self.label_group_1)
        self.scanned_epc_counter_label.setText("Đã quét")
        self.scanned_epc_counter = QLabel(parent=self.label_group_1)
        self.scanned_epc_counter.setText("0/0")
        self.label_group_layout_1.addWidget(self.scanned_epc_counter)
        self.label_group_layout_1.addWidget(self.scanned_epc_counter_label)

        self.label_group_2.setStyleSheet("color: #22c55e; font-weight: 500")
        self.epc_pass_counter_label = QLabel(parent=self.label_group_2)
        self.epc_pass_counter_label.setText("OK")
        self.epc_pass_qty = QLabel(parent=self.label_group_2)
        self.epc_pass_qty.setText("0/0")
        self.label_group_layout_2.addWidget(self.epc_pass_qty)
        self.label_group_layout_2.addWidget(self.epc_pass_counter_label)

        self.label_group_3.setStyleSheet("color: #ef4444; font-weight: 500")
        self.epc_failed_counter_label = QLabel(parent=self.label_group_3)
        self.epc_failed_counter_label.setText("NG")
        self.epc_failed_qty = QLabel(parent=self.label_group_3)
        self.epc_failed_qty.setText("0/0")
        self.label_group_layout_3.addWidget(self.epc_failed_qty)
        self.label_group_layout_3.addWidget(self.epc_failed_counter_label)

        self.epc_counter_box_layout.addWidget(self.label_group_1, 1)
        self.epc_counter_box_layout.addWidget(self.label_group_2, 1)
        self.epc_counter_box_layout.addWidget(self.label_group_3, 1)

        # endregion

        # region EPC list
        self.epc_list = QListWidget(parent=self)
        self.epc_list.setObjectName("epc_list")
        self.epc_list.setStyleSheet(
            """
            QListWidget::item{
                font-weight: 600
            }
            """
        )
        self.epc_list.setSortingEnabled(False)
        # endregion

        # region EPC list actions group
        self.epc_list_action_group_layout = QHBoxLayout()
        self.epc_list_action_group_layout.setContentsMargins(2, 2, 2, 2)
        self.epc_list_action_group_layout.setStretch(0, 1)
        self.epc_list_action_group_layout.setStretch(1, 1)
        self.epc_list_action_group = QFrame(parent=self)
        self.epc_list_action_group.setLayout(self.epc_list_action_group_layout)
        self.epc_list_action_group.setObjectName("epc_list_action_group")
        self.epc_list_action_group.setStyleSheet(
            """
            QFrame{
                padding: 2px;
                border-radius: 4px;
            }
            QPushButton{
                background: transparent;
                border: 1px solid #262626;
                color: #fafafa
            }
            QPushButton:hover{
                background-color: #404040;
            }
            QPushButton:disabled{
                color: #57534e;
            }
        """
        )
        # Toggle connect UHF reader button
        self.reader_actions_group_layout = QHBoxLayout()
        self.reader_actions_group_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.reader_actions_group_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_actions_group_layout.setSpacing(2)
        self.reader_actions_group = QFrame(parent=self)
        self.reader_actions_group.setLayout(self.reader_actions_group_layout)

        self.plug_icon = QIcon()
        self.plug_icon.addPixmap(
            QPixmap("./assets/icons/plug-zap.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.unplug_icon = QIcon()
        self.unplug_icon.addPixmap(
            QPixmap("./assets/icons/unplug.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.toggle_connect_button = QPushButton(parent=self.reader_actions_group)
        self.toggle_connect_button.setObjectName("toggle_connect_button")
        self.toggle_connect_button.setFixedSize(32, 32)
        self.toggle_connect_button.setIcon(self.plug_icon)
        self.toggle_connect_button.setToolTip("Kết nối máy UHF")
        self.toggle_connect_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_connect_button.setEnabled(False)
        self.toggle_connect_button.clicked.connect(self.handle_toggle_connect)

        # Toggle start/stop reader
        self.play_icon = QIcon()
        self.play_icon.addPixmap(
            QPixmap("./assets/icons/play.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.pause_icon = QIcon()
        self.pause_icon.addPixmap(
            QPixmap("./assets/icons/pause.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.toggle_play_button = QPushButton(parent=self.reader_actions_group)
        self.toggle_play_button.setObjectName("toggle_play_button")
        self.toggle_play_button.setToolTip("Bắt đầu đọc")
        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setFixedSize(32, 32)
        self.toggle_play_button.setEnabled(False)
        self.toggle_play_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_play_button.clicked.connect(self.handle_toggle_play)

        # Reset all reader data
        self.reset_icon = QIcon()
        self.reset_icon.addPixmap(
            QPixmap("./assets/icons/rotate-ccw.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.reset_btn = QPushButton(parent=self.reader_actions_group)
        self.reset_btn.setIcon(self.reset_icon)
        self.reset_btn.setFixedSize(32, 32)
        self.reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.setToolTip("Đặt lại danh sách quét")
        self.reset_btn.clicked.connect(self.handle_reset_scanned_epc)

        self.reader_actions_group_layout.addWidget(self.toggle_connect_button)
        self.reader_actions_group_layout.addWidget(self.toggle_play_button)
        self.reader_actions_group_layout.addWidget(self.reset_btn)

        # region Pagination group
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pagination_layout.setContentsMargins(0, 0, 0, 0)
        self.pagination_layout.setSpacing(2)
        self.pagination_group = QFrame(parent=self)
        self.pagination_group.setLayout(self.pagination_layout)
        self.prev_page_button = QPushButton(parent=self.pagination_group)
        self.next_page_button = QPushButton(parent=self.pagination_group)
        self.pagination_layout.addWidget(self.prev_page_button)
        self.pagination_layout.addWidget(self.next_page_button)

        self.next_icon = QIcon()
        self.next_icon.addPixmap(
            QPixmap("./assets/icons/chevron-last.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.prev_icon = QIcon()
        self.prev_icon.addPixmap(
            QPixmap("./assets/icons/chevron-first.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.prev_page_button.setIcon(self.prev_icon)
        self.next_page_button.setIcon(self.next_icon)
        self.prev_page_button.setFixedSize(32, 32)
        self.next_page_button.setFixedSize(32, 32)
        self.prev_page_button.setToolTip("Trang trước")
        self.next_page_button.setToolTip("Trang sau")

        self.pagination_layout.addWidget(self.prev_page_button)
        self.pagination_layout.addWidget(self.next_page_button)

        self.epc_list_action_group_layout.addWidget(self.reader_actions_group)
        self.epc_list_action_group_layout.addWidget(self.pagination_group)
        # endregion

        self.epc_reader_layout.addWidget(self.epc_counter_box)
        self.epc_reader_layout.addWidget(self.epc_list)
        self.epc_reader_layout.addWidget(self.epc_list_action_group)

        self.loading = LoadingWidget(parent, "")
        self.alert = None

        # Fake data
        with open("./data/faker.json", "r") as file:
            data = json.load(file)
            logger.debug(data.get("epcs", []))

            self._epc_datalist = data.get("epcs", [])
            self.epc_list.addItems(self._epc_datalist)

        sync_event_emitter.on(UserActionEvent.SELECTED_SIZE_CHANGE.value)(
            self.on_selected_size_change
        )

    def on_selected_size_change(self, data):
        # * Only when size is selected, enable the connect button
        self.toggle_connect_button.setEnabled(True)
        self.toggle_play_button.setEnabled(True)

        self._max_epc_qty = data["size_qty"]
        self._epc_count = 0
        _curr_epc_qty = len(self._epc_datalist)
        self.scanned_epc_counter.setText(f"{_curr_epc_qty}/{data["size_qty"]}")
        self.epc_pass_qty.setText(f"{_curr_epc_qty}/{data["size_qty"]}")
        self.epc_failed_qty.setText(f"{_curr_epc_qty}/{data["size_qty"]}")

    def show_over_limit_qty_alert(self):
        self.alert = CustomMessageBox(
            "Số lượng quét vượt quá số lượng cần phối. Vui lòng kiểm tra lại!",
            QMessageBox.Icon.Warning,
        )
        self.alert.exec()
        QCoreApplication.processEvents()
        self.handle_stop_reading()
        self.handle_reset_scanned_epc()
        self.alert = None

    def handle_pagination(self):
        self._total_page = len(self._epc_datalist) // self.PAGE_SIZE
        self._has_next_page = self._current_page < self._total_page
        self._has_prev_page = self._current_page > 1

    def handle_next_page(self):
        self._current_page += 1
        self.handle_pagination()

    def handle_prev_page(self):
        self._current_page -= 1
        self.handle_pagination()

    async def process_epc_queue(self, epc):
        if (
            self._connection_status
            and self._play_state
            and epc not in self._epc_datalist
        ):
            self.epc_list.clear()
            logger.debug(f"Has alert shown : {self.alert is None}")
            if len(self._epc_datalist) > self._max_epc_qty and self.alert is None:
                self.show_over_limit_qty_alert()
                return

            self._epc_datalist.insert(0, epc)
            self.epc_list.addItems(self._epc_datalist[:100])
            self.scanned_epc_counter.setText(
                f"{len(self._epc_datalist)}/{self._max_epc_qty}"
            )
            sync_event_emitter.emit(
                UserActionEvent.EPC_DATA_CHANGE.value, self._epc_datalist
            )

    async def on_receive_epc(self, epcInfo: LogBaseEpcInfo):
        try:
            if epcInfo.result == 0:
                await asyncio.sleep(0.05)
                await self.process_epc_queue(epcInfo.epc.upper())
        except Exception as e:
            logger.error(f"Error in on_receive_epc: {e}")

    def on_receive_epc_end(self, epcOver: LogBaseEpcOver):
        print(epcOver)

    def handle_toggle_connect(self):
        try:
            if self._connection_status:
                self.loading.open("Đang ngắt kết nối máy UHF...")
                self.toggle_connect_button.setIcon(self.plug_icon)
                self.toggle_connect_button.setToolTip("Kết nối máy UHF")
                self.reset_btn.setEnabled(True)
                self.toggle_play_button.setEnabled(False)
                QCoreApplication.processEvents()
                stop = MsgBaseStop()
                if (
                    hasattr(self, "uhf_reader_instance")
                    and self.uhf_reader_instance.sendSynMsg(stop) == 0
                ):
                    print(stop.rtMsg)
                    self._play_state(False)
                    self.toggle_play_button.setIcon(self.play_icon)
                    self.toggle_play_button.setEnabled(False)
                    self.uhf_reader_instance.close()
                self.loading.close()

            else:
                self.loading.open("Đang kết nối ...")
                QCoreApplication.processEvents()
                self.uhf_reader_instance = GClient()
                if self.uhf_reader_instance.openTcp(("10.30.82.20", 8160)):
                    self.toggle_connect_button.setIcon(self.unplug_icon)
                    self.toggle_connect_button.setToolTip("Ngắt kết nối máy UHF")
                    self.uhf_reader_instance.callEpcInfo = lambda epcInfo: asyncio.run(
                        self.on_receive_epc(epcInfo)
                    )
                    self.uhf_reader_instance.callEpcOver = self.on_receive_epc_end
                    self.toggle_play_button.setEnabled(True)
                    self._connection_status = True
                self.loading.close()

        except Exception as e:
            logger.error(f"Error in handle_toggle_connect: {e}")
            self._connection_status = False

    def handle_toggle_play(self):
        try:
            if self._play_state:
                # * With scanned EPC, check if they are end of their lifecycle
                self.handle_stop_reading()
                asyncio.run(self.handle_check_epc_combinable())

            else:
                self.handle_perform_reading()

        except Exception as e:
            logger.error(f"Error in handle_toggle_play: {e}")

    async def handle_check_epc_combinable(self):
        result = await self.rfid_repository.check_epc_lifecycle_end(self._epc_datalist)
        logger.debug(result)
        # Todo: Highlight the EPC that are not combinable & update quantity of pass/fail EPC

    def handle_stop_reading(self):
        self.loading.open("Đang dừng đọc ...")
        stop = MsgBaseStop()
        if self.uhf_reader_instance.sendSynMsg(stop) == 0:
            logger.info(f"Stopped reading with :>>> {stop.rtMsg}")

        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setToolTip("Bắt đầu đọc")
        self.loading.close()
        self._play_state = False

    def handle_perform_reading(self):
        self._epc_queue = Queue(maxsize=100)

        self.toggle_play_button.setToolTip("Dừng đọc & kiểm tra")
        self.toggle_play_button.setIcon(self.pause_icon)
        # * Đọc EPC
        msg = MsgBaseInventoryEpc(
            antennaEnable=EnumG.AntennaNo_1.value,
            inventoryMode=EnumG.AntennaNo_1.value,
        )

        if self.uhf_reader_instance.sendSynMsg(msg) == 0:
            logger.info(f"Stop reading with :>>> {msg.rtMsg}")

        self._play_state = True

    def handle_reset_scanned_epc(self):
        logger.debug("Resetting scanned EPC list")
        self._epc_datalist.clear()
        self.epc_list.clear()
        _curr_epc_qty = len(self._epc_datalist)
        self.scanned_epc_counter.setText(f"{_curr_epc_qty}/{self._max_epc_qty}")
        self.epc_pass_qty.setText(f"{_curr_epc_qty}/{self._max_epc_qty}")
        self.epc_failed_qty.setText(f"{_curr_epc_qty}/{self._max_epc_qty}")
        self.alert = CustomMessageBox(
            "Đã đặt lại danh sách quét", QMessageBox.Icon.Information
        )
        # self.alert.setMinimumSize(500, 400)
        self.alert.exec()
        # QCoreApplication.processEvents()
