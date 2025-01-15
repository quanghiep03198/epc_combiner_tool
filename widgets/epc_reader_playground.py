import asyncio
import math

# import json
from pyqttoast import ToastPreset
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from asyncio import Queue
from uhf.reader import *
from helpers.logger import logger
from constants import CombineAction
from contexts.combine_form_context import combine_form_context

# Import widgets
from widgets.loading import LoadingWidget
from widgets.toaster import Toaster
from widgets.ng_epc_table_dialog import NgEpcTableDialog

from services.rfid_service import RFIDService
from events import UserActionEvent, sync_event_emitter
from helpers.configuration import ConfigService
from typing import Callable

PAGE_SIZE: int = 50
SCANNED_EPC_LABEL: str = "Đã Quét"
NG_EPC_LABEL: str = "NG"


class GetNgEpcDetailWorker(QRunnable):
    def __init__(self, params: list[str], callback: Callable[[list], None]):
        super().__init__()
        self.params = params
        self.callback = callback

    def run(self):
        result = RFIDService.get_ng_epc_detail(self.params)
        self.callback(result)


class EpcReaderPlayground(QFrame):
    """
    EPC reader widget for scanning EPC from UHF reader
    """

    uhf_reader_instance: GClient
    """
    UHF reader instance

    Scope: public
    """

    # region Local states
    _max_epc_qty: int = 0
    _epc_datalist: list[str] = []
    _ng_epc_datalist: list[str] = []
    _ng_epc_detail_datalist: list[dict[str, str]] = []
    _current_tab_index: int = 1
    _current_page: int = 1
    _total_page: int = 1
    _has_next_page: bool = False
    _has_prev_page: bool = False

    def __init__(self, parent):
        super().__init__(parent)
        self.root = parent

        self.setObjectName("epc_reader_playground")
        self.setAutoFillBackground(True)
        self.epc_reader_layout = QVBoxLayout(self)
        self.epc_reader_layout.setContentsMargins(8, 8, 8, 8)
        self.epc_reader_layout.setSpacing(8)

        self.setLayout(self.epc_reader_layout)
        # region EPC counter box
        self.epc_counter_box = QFrame(parent=self)
        self.epc_counter_box.setObjectName("epc_counter_box")
        self.epc_counter_box_layout = QHBoxLayout()

        self.epc_counter_box_layout.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.epc_counter_box_layout.setContentsMargins(0, 0, 0, 0)
        self.epc_counter_box_layout.setSpacing(4)

        self.epc_counter_box.setLayout(self.epc_counter_box_layout)

        self.scanned_epc_counter = QPushButton(parent=self.epc_counter_box)
        self.scanned_epc_counter.setObjectName("scanned_epc_counter")
        self.scanned_epc_counter.setText(f"0/0 {SCANNED_EPC_LABEL}")
        self.scanned_epc_counter.clicked.connect(lambda: self.handle_view_curr_tab(1))
        self.scanned_epc_counter.setCheckable(True)
        self.scanned_epc_counter.setChecked(self._current_tab_index == 1)

        self.ng_epc_counter = QPushButton(parent=self.epc_counter_box)
        self.ng_epc_counter.setObjectName("ng_epc_counter")
        self.ng_epc_counter.setText(f"0/0 {NG_EPC_LABEL}")
        self.ng_epc_counter.clicked.connect(lambda: self.handle_view_curr_tab(2))
        self.ng_epc_counter.setCheckable(True)
        self.ng_epc_counter.setChecked(self._current_tab_index == 2)

        self.epc_counter_box_layout.addWidget(self.scanned_epc_counter, 1)
        self.epc_counter_box_layout.addWidget(self.ng_epc_counter, 1)

        # endregion

        # region EPC list
        self.epc_list = QListWidget(parent=self)
        self.epc_list.setObjectName("epc_list")
        self.epc_list.setSortingEnabled(False)
        self.epc_list.itemDoubleClicked.connect(self.handle_view_combination_history)
        # endregion

        # region EPC list actions group
        self.epc_list_action_group_layout = QHBoxLayout()
        self.epc_list_action_group_layout.setContentsMargins(2, 2, 2, 2)
        self.epc_list_action_group_layout.setStretch(0, 1)
        self.epc_list_action_group_layout.setStretch(1, 1)
        self.epc_list_action_group = QFrame(parent=self)
        self.epc_list_action_group.setLayout(self.epc_list_action_group_layout)
        self.epc_list_action_group.setObjectName("epc_list_action_group")
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
        self.toggle_connect_button.setCheckable(True)
        self.toggle_connect_button.setChecked(False)
        self.toggle_connect_button.toggled.connect(self.handle_toggle_connect)

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
        self.toggle_play_button.setCheckable(True)
        self.toggle_play_button.setChecked(False)
        self.toggle_play_button.setToolTip("Bắt đầu đọc")
        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setFixedSize(32, 32)
        self.toggle_play_button.setEnabled(False)
        self.toggle_play_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_play_button.toggled.connect(self.handle_toggle_play)

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
        self.page_index = QLabel(parent=self.pagination_group)
        self.page_index.setText("Trang 1/1")
        self.prev_page_button = QPushButton(parent=self.pagination_group)
        self.next_page_button = QPushButton(parent=self.pagination_group)
        self.prev_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_page_button.clicked.connect(lambda: self.handle_goto_page(-1))
        self.next_page_button.clicked.connect(lambda: self.handle_goto_page(1))
        self.pagination_layout.addWidget(self.page_index)
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

        # Fake EPC data
        # with open("./data/faker.json", "r", encoding="utf-8") as f:
        #     data = json.load(f)
        #     self._epc_datalist = data["epcs"][15:30]
        #     self.scanned_epc_counter.setText(
        #         f"{len(self._epc_datalist)}/{self._max_epc_qty} {SCANNED_EPC_LABEL}"
        #     )
        #     self._handle_pagination()
        #     self._get_page_data()

        self.loading = LoadingWidget(parent, "")

        sync_event_emitter.on(UserActionEvent.COMBINE_FORM_STATE_CHANGE.value)(
            self.on_combine_form_state_change
        )

        sync_event_emitter.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )

        sync_event_emitter.on(UserActionEvent.CHECK_COMBINABLE_FAILED.value)(
            self.on_check_combinable_failed
        )

        sync_event_emitter.on(UserActionEvent.NG_EPC_MUTATION.value)(
            self.on_ng_epc_mutation
        )

    # region Event handlers
    def on_check_combinable_failed(self, error_data: dict[str]):
        """
        Handle failed to check combinable EPC
        """
        self._ng_epc_datalist = error_data["ng_epcs"]
        failed_epc_text = self._get_counter_text(
            combine_form_context["ri_type"], len(self._ng_epc_datalist), NG_EPC_LABEL
        )
        self.ng_epc_counter.setText(failed_epc_text)
        worker = GetNgEpcDetailWorker(
            self._ng_epc_datalist, self.set_ng_epc_detail_state
        )
        QThreadPool.globalInstance().start(worker)
        # TODO: Highlighting the NG EPCs

    def set_ng_epc_detail_state(self, data: list[dict[str, str]]):
        self._ng_epc_detail_datalist = data
        self.handle_view_curr_tab(self._current_tab_index)

    def on_combined_epc_created(self, data: dict):
        self._epc_datalist.clear()
        self.epc_list.clear()
        self._handle_pagination()
        self.handle_reset_scanned_epc()
        self.scanned_epc_counter.setText(
            self._get_counter_text(
                combine_form_context["ri_type"], 0, SCANNED_EPC_LABEL
            )
        )
        self.ng_epc_counter.setText(
            self._get_counter_text(combine_form_context["ri_type"], 0, NG_EPC_LABEL)
        )

    def on_combine_form_state_change(self, data):
        # * Only when size is selected, enable the connect button
        self._max_epc_qty = data["size_qty"]

        self.scanned_epc_counter.setText(
            self._get_counter_text(
                data["ri_type"], len(self._epc_datalist), SCANNED_EPC_LABEL
            )
        )
        self.ng_epc_counter.setText(
            self._get_counter_text(
                data["ri_type"], len(self._ng_epc_datalist), NG_EPC_LABEL
            )
        )

    def _get_counter_text(self, type: str, acc_qty: int, sub_text: str) -> str:
        if type == CombineAction.COMBINE_NEW.value:
            return f"{acc_qty}/{self._max_epc_qty} {sub_text}"
        else:
            return f"{acc_qty} {sub_text}"

    def _handle_pagination(self):
        process_data = (
            self._epc_datalist if self._current_tab_index else self._ng_epc_datalist
        )
        self._total_page = math.ceil(len(process_data) / PAGE_SIZE)
        self._has_next_page = self._current_page < self._total_page
        self._has_prev_page = self._current_page > 1

        self.page_index.setText(f"Trang {self._current_page}/{self._total_page}")
        self.prev_page_button.setEnabled(self._has_prev_page)
        self.next_page_button.setEnabled(self._has_next_page)

    #
    @pyqtSlot(int)
    def handle_goto_page(self, step: int):
        self._current_page += step
        self._get_page_data()
        self._handle_pagination()

    def _get_page_data(self):
        process_data = (
            self._epc_datalist
            if self._current_tab_index == 1
            else self._ng_epc_datalist
        )
        self.epc_list.clear()
        start_index = (self._current_page - 1) * PAGE_SIZE
        end_index = start_index + PAGE_SIZE
        self.epc_list.addItems(process_data[start_index:end_index])

    async def _on_receive_epc(self, epcInfo: LogBaseEpcInfo):
        try:
            if epcInfo.result == 0:
                await asyncio.sleep(0.025)
                epc = epcInfo.epc.upper()
                if (
                    self.toggle_connect_button.isChecked()
                    and self.toggle_play_button.isChecked()
                    and epc not in self._epc_datalist
                ):
                    self.epc_list.clear()

                    self._epc_datalist.insert(0, epc)
                    self.scanned_epc_counter.setText(
                        f"{len(self._epc_datalist)}/{self._max_epc_qty} {SCANNED_EPC_LABEL}"
                    )
                    self._handle_pagination()
                    self._get_page_data()
                    sync_event_emitter.emit(
                        UserActionEvent.EPC_DATA_CHANGE.value, self._epc_datalist
                    )
        except Exception as e:
            logger.error(f"Error in on_receive_epc: {e}")

    def _on_receive_epc_end(self, epcOver: LogBaseEpcOver):
        logger.info(f"Stopped with message id: >>> {epcOver.msgId}")

    @pyqtSlot(bool)
    def handle_toggle_connect(self, checked_state: bool):
        UHF_READER_TPC_IP = ConfigService.get("UHF_READER_TCP_IP")
        UHF_READER_TPC_PORT = ConfigService.get("UHF_READER_TCP_PORT")
        if UHF_READER_TPC_IP == "" and UHF_READER_TPC_PORT == "":
            toast = Toaster(
                parent=self.root,
                title="Kết nối thất bại",
                text="Vui lòng kiểm tra cấu hình máy UHF",
                preset=ToastPreset.ERROR,
            )
            toast.show()
            return
        try:
            if not checked_state:
                self.toggle_connect_button.setIcon(self.plug_icon)
                self.toggle_connect_button.setToolTip("Kết nối máy UHF")
                self.reset_btn.setEnabled(True)
                self.toggle_play_button.setEnabled(False)
                QCoreApplication.processEvents()
                self.handle_stop_reading()
                self.uhf_reader_instance.close()

            else:
                self.uhf_reader_instance = GClient()
                if self.uhf_reader_instance.openTcp(
                    (UHF_READER_TPC_IP, int(UHF_READER_TPC_PORT))
                ):
                    self.toggle_connect_button.setIcon(self.unplug_icon)
                    self.toggle_connect_button.setToolTip("Ngắt kết nối máy UHF")
                    self.uhf_reader_instance.callEpcInfo = lambda epcInfo: asyncio.run(
                        self._on_receive_epc(epcInfo)
                    )
                    self.uhf_reader_instance.callEpcOver = self._on_receive_epc_end
                    self.toggle_play_button.setEnabled(True)

        except Exception as e:
            logger.error(f"Error in handle_toggle_connect: {e}")

    @pyqtSlot(bool)
    def handle_toggle_play(self, checked_state: bool):
        try:
            if checked_state:
                self.handle_perform_reading()
            else:
                self.handle_stop_reading()
        except Exception as e:
            logger.error(f"Error in handle_toggle_play: {e}")

    def handle_stop_reading(self):
        stop = MsgBaseStop()
        if self.uhf_reader_instance.sendSynMsg(stop) == 0:
            logger.info(f"Stopped reading with :>>> {stop.rtMsg}")
        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setToolTip("Bắt đầu đọc")

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

    @pyqtSlot(int)
    def handle_view_curr_tab(self, index: int):
        self._current_tab_index = index
        self._current_page = 1
        self.scanned_epc_counter.setChecked(self._current_tab_index == 1)
        self.ng_epc_counter.setChecked(self._current_tab_index == 2)
        self._get_page_data()
        self._handle_pagination()

        if self._current_tab_index == 1:
            self.epc_list.setStyleSheet("QListWidget::item { color: #fafafa; }")
        else:
            self.epc_list.setStyleSheet("QListWidget::item { color: #ef4444; }")

        # TODO: Remove later
        # * Fake data
        # sync_event_emitter.emit(
        #     UserActionEvent.EPC_DATA_CHANGE.value, self._epc_datalist
        # )

    @pyqtSlot()
    def handle_reset_scanned_epc(self):
        self._epc_datalist.clear()
        self._ng_epc_datalist.clear()
        self.epc_list.clear()
        self._handle_pagination()
        self.scanned_epc_counter.setText(
            self._get_counter_text(
                combine_form_context["ri_type"], 0, SCANNED_EPC_LABEL
            )
        )
        self.ng_epc_counter.setText(
            self._get_counter_text(combine_form_context["ri_type"], 0, NG_EPC_LABEL)
        )
        toast = Toaster(
            parent=self.root,
            title="Đã đặt lại danh sách quét.",
            text="Thực hiện quét lại để tiếp tục phối đôi.",
        )
        toast.show()

    @pyqtSlot()
    def handle_view_combination_history(self):
        # TODO: Show combination history dialog
        if self._current_tab_index == 2:
            ng_epcs_detail_table_dialog = NgEpcTableDialog(self.root)
            ng_epcs_detail_table_dialog.set_data(self._ng_epc_detail_datalist)
            ng_epcs_detail_table_dialog.exec()

    def on_ng_epc_mutation(self, data: list[str]):
        self._ng_epc_datalist = data
        self._current_page = 1
        self.handle_view_curr_tab(self._current_tab_index)
        self.ng_epc_counter.setText(
            self._get_counter_text(
                combine_form_context["ri_type"],
                len(self._ng_epc_datalist),
                NG_EPC_LABEL,
            )
        )
