from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSql import *
from typing import Callable
from pyqttoast import ToastPreset
from events import __event_emitter__, UserActionEvent
from services.rfid_service import RFIDService
from i18n import I18nService
from constants import CombineAction
from widgets.toaster import Toaster
from contexts.combine_form_context import combine_form_context
from helpers.logger import logger
from helpers.write_data import write_data
from contexts.auth_context import auth_context


class WorkerSignals(QObject):
    """
    Defines the signals available for storing data worker thread.
    """

    fulfill = pyqtSignal(int)
    error = pyqtSignal(dict)


class StoreDataWorker(QRunnable):
    """
    Worker thread for storing data to the database
    """

    def __init__(
        self,
        payload: dict,
        on_success: Callable[[int], None],
        on_error: Callable[[dict], None],
    ):
        super().__init__()

        self.signals = WorkerSignals()
        self.payload = payload
        self.signals.fulfill.connect(on_success)
        self.signals.error.connect(on_error)

    @pyqtSlot()
    def run(self):
        try:
            query_result = RFIDService.reset_and_add_combinations(self.payload)
            if isinstance(query_result, int):
                self.signals.fulfill.emit(query_result)
        except Exception as e:
            error_data: dict = e.args[0]
            self.signals.error.emit(error_data)


class CombineForm(QWidget):
    """
    EPC combination form submission
    """

    _size_list: list[dict[str, str]] = []
    _epcs: list[str] = []

    PROCEED_BUTTON_TEXT = "Tiến hành phối"

    def __init__(self, root):
        super().__init__(root.container)
        self.root = root

        # region Combine submission form
        self.setObjectName("combine_form")
        self.combine_form_layout = QHBoxLayout(self)
        self.combine_form_layout.setContentsMargins(0, 0, 0, 0)
        self.combine_form_layout.setSpacing(4)
        self.combine_form_layout.setObjectName("combine_form_layout")
        # Action select
        self.action_select = QComboBox(parent=self)
        self.action_select.setObjectName("actionSelect")
        self.action_select.setPlaceholderText("Chọn cách thức phối")
        self.action_select.addItem(
            CombineAction.COMBINE_NEW.value, CombineAction.COMBINE_NEW.value
        )
        self.action_select.addItem(
            CombineAction.COMPENSATE.value, CombineAction.COMPENSATE.value
        )

        self.action_select.currentIndexChanged.connect(
            lambda item: self.on_combine_from_state_change(
                "ri_type", self.action_select.itemData(item)
            )
        )

        # Size select
        self.size_select = QComboBox(parent=self)
        self.size_select.setAutoFillBackground(False)
        self.size_select.setObjectName("size_select")
        self.size_select.setPlaceholderText("Chọn cỡ giày")
        self.size_select.currentTextChanged.connect(self.handle_selected_size_change)

        # Sub-order select
        self.mo_noseq_select = QComboBox(parent=self)
        self.mo_noseq_select.setObjectName("mo_noseq_select")
        self.mo_noseq_select.setPlaceholderText("Chọn tiểu chỉ lệnh")
        self.mo_noseq_select.addItem("all", "all")
        self.mo_noseq_select.currentIndexChanged.connect(self.handle_mo_noseq_change)

        # Combine proceed button
        self.combine_proceed_button = QPushButton(parent=self)
        self.combine_proceed_button.setObjectName("combine_procedd_button")
        self.combine_proceed_button.setFixedWidth(150)
        self.combine_proceed_button.setEnabled(False)
        self.combine_proceed_button.setText(self.PROCEED_BUTTON_TEXT)
        self.combine_proceed_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.combine_proceed_button.clicked.connect(self.on_combine_proceed)

        self.combine_form_layout.addWidget(self.action_select)
        self.combine_form_layout.addWidget(self.size_select)
        self.combine_form_layout.addWidget(self.mo_noseq_select)
        self.combine_form_layout.addWidget(self.combine_proceed_button)

        # region Event listeners
        # * On current language change
        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

        # * On fetch size list successfully
        __event_emitter__.on(UserActionEvent.SIZE_LIST_CHANGE.value)(
            self.on_size_list_change
        )

        # * On scanned EPC data change
        __event_emitter__.on(UserActionEvent.EPC_DATA_CHANGE.value)(
            self.on_epc_data_change
        )

        # * On manufacturer order number sequence change
        __event_emitter__.on(UserActionEvent.GET_ORDER_DETAIL_SUCCESS.value)(
            self.handle_get_mo_noseq
        )

        # * On auth state change
        __event_emitter__.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            self.on_auth_state_change
        )
        # * On selected size change
        __event_emitter__.on(UserActionEvent.SELECTED_SIZE_CHANGE.value)(
            self.resume_combination
        )

    def __translate__(self):
        self.action_select.setPlaceholderText(
            I18nService.t("placeholders.combine_action_placeholder")
        )
        self.size_select.setPlaceholderText(
            I18nService.t("placeholders.size_numcode_placeholder")
        )
        self.mo_noseq_select.setPlaceholderText(
            I18nService.t("placeholders.mo_noseq_placeholder")
        )
        self.mo_noseq_select.setItemText(0, I18nService.t("labels.all"))
        self.combine_proceed_button.setText(I18nService.t("actions.confirm"))
        self.action_select.setItemText(0, I18nService.t("actions.new_combination"))
        self.action_select.setItemText(
            1, I18nService.t("actions.compensating_combination")
        )
        self.combine_proceed_button.setText(I18nService.t("actions.confirm"))

    def on_size_list_change(self, data):
        self._size_list = data
        self.size_select.clear()
        self.size_select.addItems(map(lambda item: item["size_numcode"], data))

    def on_epc_data_change(self, data):
        self._epcs = data
        self.on_combine_from_state_change(
            "has_epc", isinstance(data, list) and len(data) > 0
        )

    def on_auth_state_change(self, data):
        """
        Update form values when user login
        """
        combine_form_context.update(user_code_created=data["user_code"])
        combine_form_context.update(user_name_created=data["employee_name"])
        combine_form_context.update(user_code_updated=data["user_code"])
        combine_form_context.update(user_name_updated=data["employee_name"])
        combine_form_context.update(factory_code_orders=data["factory_code"])
        combine_form_context.update(factory_name_orders=data["factory_code"])
        combine_form_context.update(factory_code_produce=data["factory_code"])
        combine_form_context.update(factory_name_produce=data["factory_code"])
        combine_form_context.update(dept_code=f"{data['factory_code']}A0000")
        combine_form_context.update(dept_name=f"{data['factory_code']}A0000")

    def handle_get_mo_noseq(self, data: list[str]):
        try:
            self.mo_noseq_select.clear()
            for mo_noseq in data:
                self.mo_noseq_select.addItem(mo_noseq, mo_noseq)
        except Exception as e:
            logger.error(e)

    def handle_selected_size_change(self, value: str):
        """
        When user select a size, update the selected size in the form and set maxiumn EPC quantity that user need to scan
        """
        size_item = next(
            (
                item
                for item in self._size_list
                if "size_numcode" in item and item["size_numcode"] == value
            ),
            None,
        )

        if size_item:
            self.on_combine_from_state_change("size_numcode", size_item["size_numcode"])
            self.on_combine_from_state_change("size_code", size_item["size_code"])
            self.on_combine_from_state_change("size_qty", size_item["size_qty"])

    @pyqtSlot(int)
    def handle_mo_noseq_change(self, selected_index: int):
        value = self.mo_noseq_select.itemData(selected_index)
        __event_emitter__.emit(UserActionEvent.MO_NOSEQ_CHANGE.value, value)
        self.on_combine_from_state_change("mo_noseq", value)
        if value == "all":
            self.combine_proceed_button.setEnabled(False)

    def on_combine_from_state_change(self, field, value) -> None:
        """
        Update the form values when user interact with the form
        Args:
            field: The form field that user interact with
            value: The value that user selected
        """

        combine_form_context[field] = value

        __event_emitter__.emit(
            UserActionEvent.COMBINE_FORM_STATE_CHANGE.value, combine_form_context
        )

        is_combinable = self.check_can_submit()

        self.combine_proceed_button.setEnabled(is_combinable)

    @pyqtSlot()
    def on_combine_proceed(self):
        if (
            combine_form_context["ri_type"] == CombineAction.COMBINE_NEW.value
            and len(self._epcs) > combine_form_context["size_qty"]
        ):
            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notifications.over_scan_limit_title"),
                text=I18nService.t("notifications.over_scan_limit_text"),
                preset=ToastPreset.WARNING_DARK,
            )
            toast.show()
            return

        try:
            self.combine_proceed_button.setEnabled(False)
            self.combine_proceed_button.setText("Đang xử lý...")
            payload = list(
                map(
                    lambda item: {
                        **combine_form_context,
                        "EPC_Code": item,
                        "remark": "combined by quanghiep03198",
                    },
                    self._epcs,
                )
            )
            worker = StoreDataWorker(
                payload, self.on_mutate_success, self.on_mutate_error
            )
            QThreadPool.globalInstance().start(worker)

            # RFIDService.reset_and_add_combinations(payload)

        except Exception as e:
            logger.error(e)

    @pyqtSlot(int)
    def on_mutate_success(self, num_rows_affected: int | None):
        if isinstance(num_rows_affected, int):
            # Ensure the directory exists
            self.combine_proceed_button.setText(self.PROCEED_BUTTON_TEXT)
            write_data(
                {
                    "mo_no": combine_form_context["mo_no"],
                    "size_numcode": combine_form_context["size_numcode"],
                    "epcs": self._epcs,
                    "created_by": auth_context["employee_name"],
                }
            )
            __event_emitter__.emit(
                UserActionEvent.COMBINED_EPC_CREATED.value,
                {
                    "mo_no": combine_form_context["mo_no"],
                    "size_numcode": combine_form_context["size_numcode"],
                    "affected": num_rows_affected,
                },
            )

    @pyqtSlot(dict)
    def on_mutate_error(self, error_data):
        self.combine_proceed_button.setText(self.PROCEED_BUTTON_TEXT)

        if (
            isinstance(error_data, dict)
            and "message" in error_data
            and "data" in error_data
        ):
            toast = Toaster(
                parent=self.root,
                title="notification.combine_epc_failure_title",
                text=error_data["message"],
                preset=ToastPreset.ERROR_DARK,
            )
            toast.show()
            __event_emitter__.emit(
                UserActionEvent.CHECK_COMBINABLE_FAILED.value, error_data["data"]
            )

    def check_can_submit(self) -> bool:
        return (
            combine_form_context["ri_type"] is not None
            and combine_form_context["mo_no"] is not None
            and combine_form_context["mo_noseq"] is not None
            and combine_form_context["size_numcode"] is not None
            and combine_form_context["size_code"] is not None
            and combine_form_context["mat_code"] is not None
            and combine_form_context["or_no"] is not None
            and combine_form_context["or_custpo"] is not None
            and combine_form_context["cust_shoestyle"] is not None
            and combine_form_context["has_epc"]
        )

    def resume_combination(self, ng_epcs: list[str]) -> None:
        """
        Resume the combination process when NG EPCs are mutated
        """
        is_combinable = self.check_can_submit() and len(ng_epcs) == 0
        self.combine_proceed_button.setEnabled(is_combinable)
