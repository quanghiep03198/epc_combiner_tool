import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from constants import NgAction
from services.rfid_service import RFIDService
from typing import Callable
from numpy import unique
from widgets.loading_widget import LoadingWidget
from widgets.toaster import Toaster, ToastPreset
from events import sync_event_emitter, UserActionEvent
from helpers.logger import logger

MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 500


class WorkerSignals(QObject):
    """
    Defines the signals available for storing data worker thread.
    """

    fulfill = pyqtSignal(int)
    error = pyqtSignal(str)


class MutateNgEpcWorker(QRunnable):
    def __init__(
        self,
        action: NgAction,
        payload: dict,
        on_success: Callable[[int], None],
        on_error: Callable[[str], None],
    ):
        super().__init__()
        self._payload = payload
        self._action = action
        self.signals = WorkerSignals()
        self.signals.fulfill.connect(on_success)
        self.signals.error.connect(on_error)

    def run(self):
        num_rows_affected = 0
        try:
            if self._action == NgAction.COMPENSATE.value:
                num_rows_affected = RFIDService.force_end_lifecycle(self._payload)
            elif self._action == NgAction.CANCEL.value:
                num_rows_affected = RFIDService.force_cancel(self._payload["epcs"])

            self.signals.fulfill.emit(num_rows_affected)
        except Exception as e:
            logger.error(e)
            e.message = "Thao tác thất bại"
            self.signals.error.emit(e.message)


class NgEpcTableDialog(QDialog):
    _horizontal_header_labels = [
        "EPC",
        "Chỉ Lệnh",
        "Size",
        "Ngày Phối",
        "Trạm Đang Sử Dụng",
    ]

    _mutation_form_values: dict[str, str] = {
        "mo_no": None,
        "size_code": None,
        "action": None,
    }

    _is_compensable: bool = False

    _original_data: list = []
    _filtered_data: list = []
    _filtered_size_data: list = []

    _current_page: int = 1
    _total_page: int = 1
    _page_size: int = 10
    _has_next_page: bool = False
    _has_prev_page: bool = False
    _ng_action: NgAction = None

    # region UI Initialization
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = parent

        self.setWindowTitle("Lịch sử phối")
        self.minimumWidth = QSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # region Mutation Form
        self.dialog_layout = QVBoxLayout(self)
        self.dialog_layout.setSpacing(8)
        self.dialog_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.dialog_layout)

        self.mutation_form_layout = QHBoxLayout(self)
        self.mutation_form_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.mutation_form_layout.setContentsMargins(0, 0, 0, 0)
        self.mutation_form = QWidget()
        self.mutation_form.setLayout(self.mutation_form_layout)

        # ComboBox for "mo_no" field
        self.mo_no_select = QComboBox()
        self.mo_no_select.currentIndexChanged.connect(self.handle_mo_no_change)
        self.mo_no_select.setPlaceholderText("Chọn chỉ lệnh")

        # ComboBox for "size_code" field
        self.size_select = QComboBox()
        self.size_select.currentIndexChanged.connect(self.handle_size_change)
        self.size_select.setPlaceholderText("Chọn size")

        # ComboBox for "action" field
        self.action_select = QComboBox()
        self.action_select.setPlaceholderText("Thao tác tem NG")
        self.action_select.addItem("Bù tem", NgAction.COMPENSATE.value)
        self.action_select.addItem("Hủy", NgAction.CANCEL.value)
        self.action_select.currentIndexChanged.connect(self.handle_ng_action_change)

        # Submit button
        self.submit_button = QPushButton("Thực hiện")
        self.submit_button.setEnabled(False)
        self.submit_button.setFixedWidth(100)
        self.submit_button.clicked.connect(self.handle_submit)

        self.mutation_form_layout.addWidget(self.mo_no_select)
        self.mutation_form_layout.addWidget(self.size_select)
        self.mutation_form_layout.addWidget(self.action_select)
        self.mutation_form_layout.addWidget(self.submit_button)

        # region EPC Combination Table
        self.table = QTableWidget(self)
        self.table.setMaximumHeight(350)
        self.table.setColumnCount(len(self._horizontal_header_labels))
        self.table.setHorizontalHeaderLabels(self._horizontal_header_labels)
        self.table.setSortingEnabled(False)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored
        )
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setMinimumSectionSize(150)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setCascadingSectionResizes(True)
        self.table.verticalHeader().setHighlightSections(False)
        self.table.verticalHeader().setSortIndicatorShown(False)
        self.table.verticalHeader().setStretchLastSection(False)
        self.table.setAutoFillBackground(True)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setFrameShadow(QFrame.Shadow.Plain)
        self.table.setMidLineWidth(1)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)

        # Table Pagination
        self.pagination_group_layout = QHBoxLayout()
        self.pagination_group_layout.setContentsMargins(0, 0, 0, 0)
        self.pagination_group_layout.setSpacing(16)
        self.pagination_group_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.pagination_group = QWidget()
        self.pagination_group.setLayout(self.pagination_group_layout)
        self.pagination_group.setObjectName("pagination_group")

        self.page_index = QLabel("Trang 1/1")

        self.first_page_icon = QIcon()
        self.first_page_icon.addPixmap(
            QPixmap("./assets/icons/chevron-first.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.last_page_icon = QIcon()
        self.last_page_icon.addPixmap(
            QPixmap("./assets/icons/chevron-last.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.prev_page_icon = QIcon()
        self.prev_page_icon.addPixmap(
            QPixmap("./assets/icons/chevron-left.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.next_page_icon = QIcon()
        self.next_page_icon.addPixmap(
            QPixmap("./assets/icons/chevron-right.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.pagination_button_group_layout = QHBoxLayout()
        self.pagination_button_group_layout.setSpacing(2)
        self.pagination_button_group_layout.setContentsMargins(0, 0, 0, 0)
        self.pagination_button_group = QWidget()
        self.pagination_button_group.setLayout(self.pagination_button_group_layout)

        self.first_page_button = QPushButton()
        self.last_page_button = QPushButton()
        self.prev_page_button = QPushButton()
        self.next_page_button = QPushButton()
        self.first_page_button.setFixedSize(32, 32)
        self.last_page_button.setFixedSize(32, 32)
        self.prev_page_button.setFixedSize(32, 32)
        self.next_page_button.setFixedSize(32, 32)
        self.first_page_button.setToolTip("Trang đầu")
        self.last_page_button.setToolTip("Trang trước")
        self.prev_page_button.setToolTip("Trang sau")
        self.next_page_button.setToolTip("Trang cuối")

        self.first_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.last_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_page_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.first_page_button.setIcon(self.first_page_icon)
        self.last_page_button.setIcon(self.last_page_icon)
        self.prev_page_button.setIcon(self.prev_page_icon)
        self.next_page_button.setIcon(self.next_page_icon)

        self.first_page_button.clicked.connect(self.handle_goto_first_page)
        self.prev_page_button.clicked.connect(lambda: self.handle_goto_page(step=-1))
        self.next_page_button.clicked.connect(lambda: self.handle_goto_page(step=1))
        self.last_page_button.clicked.connect(self.handle_goto_last_page)

        self.pagination_button_group_layout.addWidget(self.first_page_button)
        self.pagination_button_group_layout.addWidget(self.prev_page_button)
        self.pagination_button_group_layout.addWidget(self.next_page_button)
        self.pagination_button_group_layout.addWidget(self.last_page_button)

        self.page_size_select = QComboBox()
        self.page_size_select.setFixedWidth(100)
        self.page_size_select.addItem("10 hàng", 10)
        self.page_size_select.addItem("20 hàng", 20)
        self.page_size_select.addItem("50 hàng", 50)
        self.page_size_select.setCurrentIndex(0)
        self.page_size_select.currentIndexChanged.connect(self.handle_page_size_change)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setStyleSheet(
            "background-color: #404040; padding-left: 16px; padding-right: 16px;"
        )
        separator1.setMaximumHeight(24)
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet(
            "background-color: #404040; padding-left: 16px; padding-right: 16px;"
        )
        separator2.setMaximumHeight(24)

        self.pagination_group_layout.addWidget(self.pagination_button_group)
        self.pagination_group_layout.addWidget(separator1)
        self.pagination_group_layout.addWidget(self.page_index)
        self.pagination_group_layout.addWidget(separator2)
        self.pagination_group_layout.addWidget(self.page_size_select)

        self.dialog_layout.addWidget(self.mutation_form)
        self.dialog_layout.addWidget(self.table)
        self.dialog_layout.addWidget(self.pagination_group)

    def set_data(self, data: list[dict[str, str]]) -> None:
        self._original_data = data
        self._filtered_data = data

        self.mo_no_select.clear()
        self.mo_no_select.addItem("Tất cả", "all")

        for item in unique(list(map(lambda item: item["mo_no"], data))):
            self.mo_no_select.addItem(item, item)

        self._current_page = 1
        self._handle_pagination()
        self._render_page_row()
        self._check_is_cancellable()
        self._check_is_compensable()
        self._validate_mutation_form()

    def set_form_field_value(self, field: str, value: str) -> None:
        self._mutation_form_values[field] = value
        self._check_is_cancellable()
        self._check_is_compensable()
        can_submit = self._validate_mutation_form()
        self.submit_button.setEnabled(can_submit)

    def _handle_pagination(self) -> None:
        self._total_page = math.ceil(len(self._original_data) / self._page_size)
        self._has_next_page = self._current_page < self._total_page
        self._has_prev_page = self._current_page > 1
        self.page_index.setText(f"Trang {self._current_page}/{self._total_page}")
        self.prev_page_button.setEnabled(self._has_prev_page)
        self.next_page_button.setEnabled(self._has_next_page)

    def _render_page_row(self) -> None:
        start_index = (self._current_page - 1) * self._page_size
        end_index = start_index + self._page_size
        page_data = self._filtered_data[start_index:end_index]
        self.table.setRowCount(len(page_data))
        for index, row in enumerate(page_data):
            self.table.setItem(index, 0, QTableWidgetItem(row["EPC_Code"]))
            self.table.setItem(index, 1, QTableWidgetItem(row["mo_no"]))
            self.table.setItem(index, 2, QTableWidgetItem(row["size_numcode"]))
            self.table.setItem(index, 3, QTableWidgetItem(row["ri_date"]))
            self.table.setItem(index, 4, QTableWidgetItem(row["stationNO"]))
        # Always resize columns to fit content
        self.table.resizeColumnsToContents()

    def _check_is_compensable(self) -> bool:
        is_compensable = (
            all(item["stationNO"] is not None for item in self._filtered_data)
            # and (self._mutation_form_values["action"] == NgAction.COMPENSATE.value)
            and (self._mutation_form_values["mo_no"] is not None)
            and self._mutation_form_values["mo_no"] != "all"
            and (self._mutation_form_values["size_code"] is not None)
        )
        self._set_action_enabled(0, is_compensable)
        return is_compensable

    def _check_is_cancellable(self) -> bool:
        is_cancellable = (
            all(item["stationNO"] is None for item in self._filtered_data)
            # and (self._mutation_form_values["action"] == NgAction.CANCEL.value)
            and (self._mutation_form_values["mo_no"] is not None)
            and self._mutation_form_values["mo_no"] != "all"
            and (self._mutation_form_values["size_code"] is not None)
        )
        logger.debug(is_cancellable)
        self._set_action_enabled(1, is_cancellable)
        return is_cancellable

    def _set_action_enabled(self, index, is_enabled: bool):
        model = self.action_select.model()
        item = model.item(index)
        if is_enabled:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
        else:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

    def _validate_mutation_form(self) -> bool:
        """
        Validates the mutation form based on the current form values.
        """
        match self._mutation_form_values["action"]:
            case None:
                return False
            case NgAction.COMPENSATE.value:
                return self._check_is_compensable()
            case NgAction.CANCEL.value:
                # Only cancel EPCs that have not been moved to a station
                return self._check_is_cancellable()

    @pyqtSlot(int)
    def handle_mo_no_change(self, index: int):
        mo_no = self.mo_no_select.itemData(index)

        # Set form field value
        self.set_form_field_value("mo_no", mo_no)

        # Filter data based on selected mo_no
        self.size_select.clear()
        if mo_no == "all":
            self._filtered_data = self._original_data
            self.size_select.setEnabled(False)
            self.set_form_field_value("size_code", None)
        else:
            self.size_select.setEnabled(True)
            self._filtered_data = list(
                filter(lambda item: item["mo_no"] == mo_no, self._original_data)
            )
            # Get size list that match with selected mo_no
            size_datalist = unique(
                list(map(lambda item: item["size_numcode"], self._filtered_data))
            )
            for item in size_datalist:
                self.size_select.addItem(item, item)

        self._current_page = 1
        self._render_page_row()
        self._handle_pagination()

    @pyqtSlot(int)
    def handle_size_change(self, index: int):
        size_code = self.size_select.itemData(index)
        if size_code is not None:
            self._filtered_data = list(
                filter(
                    lambda item: item["size_numcode"] == size_code, self._original_data
                )
            )
            self.set_form_field_value("size_code", size_code)
        else:
            self._filtered_data = self._original_data
            self.set_form_field_value("size_code", None)

    @pyqtSlot(int)
    def handle_goto_page(self, step):
        self._current_page += step
        self._render_page_row()
        self._handle_pagination()

    @pyqtSlot()
    def handle_goto_first_page(self):
        self._current_page = 1
        self._render_page_row()
        self._handle_pagination()

    @pyqtSlot()
    def handle_goto_last_page(self):
        self._current_page = self._total_page
        self._render_page_row()
        self._handle_pagination()

    @pyqtSlot(int)
    def handle_page_size_change(self, index: int):
        self._page_size = self.page_size_select.itemData(index)
        if self._page_size > self._total_page:
            self._current_page = 1
        self._handle_pagination()
        self._render_page_row()

    @pyqtSlot(int)
    def handle_ng_action_change(self, index: int):
        self.set_form_field_value("action", self.action_select.itemData(index))
        # self._validate_mutation_form()

    @pyqtSlot()
    def handle_submit(self):
        self.loading = LoadingWidget(self)
        self.loading.show_loading()

        worker = MutateNgEpcWorker(
            action=self._mutation_form_values["action"],
            payload={
                "epcs": list(map(lambda item: item["EPC_Code"], self._filtered_data)),
                "mo_no": self._mutation_form_values["mo_no"],
                "size_code": str(int(self._mutation_form_values["size_code"])),
            },
            on_success=self.on_mutate_fulfill,
            on_error=self.on_mutate_error,
        )
        QThreadPool.globalInstance().start(worker)

    @pyqtSlot(int)
    def on_mutate_fulfill(self, num_row_affected: int):
        try:
            self.loading.close_loading()

            def is_matching_epc(item, mutation_values):
                mo_no_match = item["mo_no"] == mutation_values["mo_no"]
                size_match = item["size_numcode"] == mutation_values["size_code"]

                if mutation_values["action"] == NgAction.CANCEL.value:
                    return item["stationNO"] is None and mo_no_match and size_match
                else:
                    return item["stationNO"] is not None and mo_no_match and size_match

            def filter_epc_codes(
                a: list[dict[str, str]], b: list[dict[str, str]]
            ) -> list[dict[str, str]]:
                b_epc_codes = {item["EPC_Code"] for item in b}
                return [item for item in a if item["EPC_Code"] not in b_epc_codes]

            revoked_epcs = list(
                filter(
                    lambda item: is_matching_epc(item, self._mutation_form_values),
                    self._filtered_data,
                )
            )

            remain_ng_epcs = filter_epc_codes(self._filtered_data, revoked_epcs)
            self.set_data(remain_ng_epcs)

            message = (
                f"{num_row_affected} tem đã được bù"
                if self._mutation_form_values["action"] == NgAction.COMPENSATE.value
                else f"{num_row_affected} tem đã được hủy"
            )

            sync_event_emitter.emit(
                UserActionEvent.NG_EPC_MUTATION.value,
                list(map(lambda item: item["EPC_Code"], remain_ng_epcs)),
            )

            toast = Toaster(
                parent=self.root,
                title="Thành công",
                text=message,
                preset=ToastPreset.SUCCESS_DARK,
            )
            toast.show()
            if len(remain_ng_epcs) == 0:
                self.close()
        except Exception as e:
            logger.error(e)

    @pyqtSlot(str)
    def on_mutate_error(self, message: str):
        self.loading.close_loading()
        toast = Toaster(
            parent=self.root,
            title="Thành công",
            text=message,
            preset=ToastPreset.ERROR_DARK,
        )
        toast.show()
