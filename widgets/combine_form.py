from typing import Callable

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSql import *
from PyQt6.QtWidgets import *
from pyqttoast import ToastPreset

from constants import CombineAction
from contexts.auth_context import auth_context
from contexts.combine_form_context import combine_form_context
from decorators.debounce import pyqtDebounce
from events import UserActionEvent, __event_emitter__
from helpers.logger import logger
from helpers.write_data import write_data
from i18n import I18nContext, I18nService
from repositories.rfid_repository import RFIDRepository
from repositories.station_repository import StationRepository
from services.rfid_service import RFIDService
from widgets.toaster import Toaster


class WorkerSignals(QObject):
    """
    Defines the signals available for storing data worker thread.
    """

    fulfill = pyqtSignal(int)
    error = pyqtSignal(Exception)


class StoreDataWorker(QRunnable):
    """
    Worker thread for storing data to the database
    """

    def __init__(
        self,
        payload: dict,
        on_success: Callable[[int], None],
        on_error: Callable[[Exception], None],
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
            logger.error(e.args)
            self.signals.error.emit(e)


class CombineForm(QFrame, I18nContext):
    """
    EPC combination form submission

    Extends `QFrame`

    Extends `I18nContext`

    Implements `I18nContext.__translate__()`
    """

    __size_list: list[dict[str, str]] = []
    __epcs: list[str] = []

    def __init__(self, root):
        super().__init__(root.container)
        self.root = root

        # region Combine submission form
        self.setObjectName("combine_form")
        self.setContentsMargins(0, 0, 0, 0)
        self.combine_form_layout = QHBoxLayout(self)
        self.combine_form_layout.setContentsMargins(0, 0, 0, 0)
        self.combine_form_layout.setSpacing(8)
        self.combine_form_layout.setObjectName("combine_form_layout")

        # Action select
        self.action_select = QComboBox(parent=self)
        self.action_select.setObjectName("actionSelect")
        self.action_select.addItem(
            CombineAction.COMBINE_NEW.value, CombineAction.COMBINE_NEW.value
        )
        self.action_select.addItem(
            CombineAction.COMPENSATE.value, CombineAction.COMPENSATE.value
        )

        self.action_select.setCurrentIndex(0)
        self.action_select.currentIndexChanged.connect(
            lambda item: self.handle_action_change(self.action_select.itemData(item))
        )

        # Action select
        self.station_select = QComboBox(parent=self)
        self.station_select.setObjectName("stationSelect")
        self.station_select.setVisible(False)
        self.station_select.currentIndexChanged.connect(self.handle_station_change)

        # Size select
        self.size_select = QComboBox(parent=self)
        self.size_select.setAutoFillBackground(False)
        self.size_select.setObjectName("size_select")
        self.size_select.currentTextChanged.connect(self.handle_selected_size_change)

        # Sub-order select
        self.mo_noseq_select = QComboBox(parent=self)
        self.mo_noseq_select.setObjectName("mo_noseq_select")
        self.mo_noseq_select.addItem("all", "all")
        self.mo_noseq_select.currentIndexChanged.connect(self.handle_mo_noseq_change)

        # Combine proceed button
        self.combine_proceed_button = QPushButton(parent=self)
        self.combine_proceed_button.setObjectName("combine_procedd_button")
        self.combine_proceed_button.setFixedWidth(150)
        self.combine_proceed_button.setEnabled(False)
        self.combine_proceed_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.combine_proceed_button.clicked.connect(self.on_combine_proceed)

        self.combine_form_layout.addWidget(self.action_select, 2)
        self.combine_form_layout.addWidget(self.station_select, 2)
        self.combine_form_layout.addWidget(self.mo_noseq_select, 2)
        self.combine_form_layout.addWidget(self.size_select, 2)
        self.combine_form_layout.addWidget(self.combine_proceed_button, 1)
        self.action_select.setMinimumWidth(200)
        self.station_select.setMinimumWidth(200)
        self.mo_noseq_select.setMinimumWidth(200)
        self.size_select.setMinimumWidth(200)

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
        self.__retrive_station_list()

        self.mo_noseq_select.setItemText(0, I18nService.t("labels.all"))
        self.action_select.setItemText(0, I18nService.t("actions.new_combination"))
        self.action_select.setItemText(1, I18nService.t("actions.compensate"))
        self.combine_proceed_button.setText(I18nService.t("actions.confirm"))

    def on_size_list_change(self, data):
        self.combine_proceed_button.setEnabled(False)
        self.__size_list = data
        self.size_select.clear()
        self.size_select.addItems(map(lambda item: item["size_numcode"], data))
        self.size_select.setCurrentText(combine_form_context.get("size_numcode"))

    def on_epc_data_change(self, data):
        self.__epcs = data
        should_enable_combination = isinstance(data, list) and len(data) > 0
        self.on_combine_from_state_change("has_epc", should_enable_combination)

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

        self.__retrive_station_list()
        # self.station_select.clear()
        # for station in self.__target_trace_history_stations:
        #     translated_station_no = I18nService.t(station["station_no"])
        #     self.station_select.addItem(
        #         translated_station_no, station["station_seq_no"]
        #     )

    def __retrive_station_list(self):
        self.__target_trace_history_stations = StationRepository.get_stations()
        if auth_context["is_authenticated"] and self.station_select.count() > 0:
            for i in range(len(self.__target_trace_history_stations)):
                translated_station_no = I18nService.t(
                    self.__target_trace_history_stations[i]["station_no"]
                )
                self.station_select.setItemText(i, translated_station_no)
        else:
            self.station_select.clear()
            for station in self.__target_trace_history_stations:
                translated_station_no = I18nService.t(station["station_no"])
                self.station_select.addItem(
                    translated_station_no,
                    station["station_seq_no"],
                )
        # return self.__target_trace_history_stations

    @pyqtSlot(str)
    def handle_action_change(self, value):
        self.station_select.setVisible(value == CombineAction.COMPENSATE.value)
        self.on_combine_from_state_change("ri_type", value)

    @pyqtSlot(int)
    def handle_station_change(self, index):

        self.on_combine_from_state_change(
            "station_seq_no",
            int(self.__target_trace_history_stations[index]["station_seq_no"]),
        )

    @pyqtSlot(str)
    def handle_selected_size_change(self, value: str):
        """
        When user select a size, update the selected size in the form and set maxiumn EPC quantity that user need to scan
        """
        size_item = next(
            (
                item
                for item in self.__size_list
                if "size_numcode" in item and item["size_numcode"] == value
            ),
            None,
        )

        if size_item:
            self.on_combine_from_state_change("size_numcode", size_item["size_numcode"])
            self.on_combine_from_state_change("size_code", size_item["size_code"])
            self.on_combine_from_state_change("size_qty", size_item["size_qty"])
            self.on_combine_from_state_change("combined_qty", size_item["combined_qty"])
            self.on_combine_from_state_change("in_use_qty", size_item["in_use_qty"])

    @pyqtSlot(int)
    def handle_mo_noseq_change(self, selected_index: int):
        value = self.mo_noseq_select.itemData(selected_index)
        self.on_combine_from_state_change("mo_noseq", value)
        self.on_combine_from_state_change("size_numcode", None)
        self.size_select.clear()
        __event_emitter__.emit(UserActionEvent.MO_NOSEQ_CHANGE.value, value)
        if value == "all":
            self.combine_proceed_button.setEnabled(False)

    def handle_get_mo_noseq(self, data: list[str]):
        try:
            self.combine_proceed_button.setEnabled(False)
            self.mo_noseq_select.clear()
            self.mo_noseq_select.addItem(I18nService.t("labels.all"), "all")
            for mo_noseq in data:
                self.mo_noseq_select.addItem(mo_noseq, mo_noseq)
        except Exception as e:
            logger.error(e)

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

        is_combinable = self.__validate_submission_criteria()

        self.combine_proceed_button.setEnabled(is_combinable)

    @pyqtDebounce(wait=500, immediate=True)
    @pyqtSlot()
    def on_combine_proceed(self):
        # Check if all values in data are not None or empty string or "all"
        is_valid = self.__validate_submission_criteria()

        if is_valid is False:
            Toaster(
                parent=self.root,
                title=I18nService.t("notification.combine_epc_failure_title"),
                text=I18nService.t("notification.combine_epc_validation_failure_text"),
                preset=ToastPreset.WARNING_DARK,
            ).show()
            return

        if (
            combine_form_context["ri_type"] == CombineAction.COMBINE_NEW.value
            and len(self.__epcs)
            > combine_form_context["size_qty"] - combine_form_context["combined_qty"]
        ):
            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notification.over_scan_limit_title"),
                text=I18nService.t("notification.over_scan_limit_text"),
                preset=ToastPreset.WARNING_DARK,
            )
            toast.show()
            return

        try:
            self.combine_proceed_button.setEnabled(False)
            self.combine_proceed_button.setText(
                I18nService.t("notification.processing")
            )
            payload = list(
                map(
                    lambda item: {
                        **combine_form_context,
                        "EPC_Code": item,
                        "remark": f"Combined by {auth_context['user_code']}",
                    },
                    self.__epcs,
                )
            )
            validated_epcs = RFIDRepository.check_reasonable_combination(payload)
            if any(epc.get("recombinable") == False for epc in validated_epcs):
                __event_emitter__.emit(
                    UserActionEvent.INVALID_COMBINATION_FOUND.value, validated_epcs
                )
                toast = Toaster(
                    parent=self.root,
                    title=I18nService.t(
                        "notification.recent_combined_epc_exists_title"
                    ),
                    text=I18nService.t("notification.recent_combined_epc_exists_text"),
                    preset=ToastPreset.WARNING_DARK,
                )
                toast.show()
                self.combine_proceed_button.setText(I18nService.t("actions.confirm"))
                return

            worker = StoreDataWorker(
                payload, self.on_mutate_success, self.on_mutate_error
            )
            QThreadPool.globalInstance().start(worker)
        except Exception as e:
            logger.error(e)

    @pyqtSlot(int)
    def on_mutate_success(self, num_rows_affected: int | None):
        if isinstance(num_rows_affected, int):
            # Ensure the directory exists
            self.combine_proceed_button.setText(I18nService.t("actions.confirm"))

            write_data(
                {
                    "epcs": self.__epcs,
                    "mo_no": combine_form_context["mo_no"],
                    "size_numcode": combine_form_context["size_numcode"],
                    "ri_type": combine_form_context["ri_type"],
                    "created_by": auth_context["employee_name"],
                }
            )

            self.__epcs.clear()

            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notification.combine_epc_success").format(
                    quantity=num_rows_affected
                ),
                text=None,
                preset=ToastPreset.SUCCESS_DARK,
            )
            toast.show()

            __event_emitter__.emit(
                UserActionEvent.COMBINED_EPC_CREATED.value,
                {
                    "mo_no": combine_form_context["mo_no"],
                    "mo_noseq": combine_form_context["mo_noseq"],
                    "size_numcode": combine_form_context["size_numcode"],
                    "affected": num_rows_affected,
                },
            )

    @pyqtSlot(Exception)
    def on_mutate_error(self, e: Exception):
        self.combine_proceed_button.setText(I18nService.t("actions.confirm"))
        toast = Toaster(
            parent=self.root,
            title=I18nService.t("notification.combine_epc_failure_title"),
            preset=ToastPreset.ERROR_DARK,
            text=str(e),
        )
        toast.show()

    def __validate_submission_criteria(self) -> bool:
        is_valid = (
            combine_form_context["ri_type"] is not None
            and combine_form_context["mo_no"] is not None
            and combine_form_context["mo_noseq"] is not None
            and combine_form_context["mo_noseq"] != "all"
            and combine_form_context["size_numcode"] is not None
            and combine_form_context["size_code"] is not None
            and combine_form_context["mat_code"] is not None
            and combine_form_context["or_no"] is not None
            and combine_form_context["or_custpo"] is not None
            and combine_form_context["cust_shoestyle"] is not None
            and combine_form_context["has_epc"]
        )
        is_compensating = (
            combine_form_context["ri_type"] == CombineAction.COMPENSATE.value
        )
        if is_compensating:
            return (
                is_valid
                # and combine_form_context["station_no"] is not None
                and combine_form_context["station_seq_no"] is not None
            )
        return is_valid
