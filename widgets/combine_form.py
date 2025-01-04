import asyncio
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSql import *
from database import DATA_SOURCE_ERP
from helpers.logger import logger
from events import sync_event_emitter, async_event_emitter, UserActionEvent
from repositories.rfid_repository import RFIDRepository
from database import DATA_SOURCE_DL
from contexts.combine_form_context import combine_form_context


class CombineForm(QFrame):
    """
    EPC combination form submission
    """

    _size_list: list[dict[str, str]] = []
    _epcs: list[str] = [
        "E28069150000401D2B94E4EC",
        "E28069150000501D2B94E0EC",
        "E28069150000401D2B9404BD",
        # "E28069150000501D2B9400BD",
        # "E28069150000501D2B94F4C7",
        # "E28069150000401D2B9264F6",
    ]

    def __init__(self, parent):
        super().__init__(parent)

        self.rfid_repository = RFIDRepository(DATA_SOURCE_DL)

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
        self.action_select.addItem("Phối mới", "A")
        self.action_select.addItem("Phối bù", "D")
        # self.action_select.addItems(["Phối mới", "Phối bù"])
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
        self.mo_noseq_select.addItem("Tất cả", "all")
        self.mo_noseq_select.currentIndexChanged.connect(self.handle_mo_noseq_change)

        # Combine proceed button
        self.combine_proceed_button = QPushButton(parent=self)
        self.combine_proceed_button.setObjectName("combine_procedd_button")
        self.combine_proceed_button.setEnabled(False)
        self.combine_proceed_button.setText("Tiến hành phối")
        self.combine_proceed_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.combine_proceed_button.clicked.connect(self.on_combine_proceed)

        self.combine_form_layout.addWidget(self.action_select)
        self.combine_form_layout.addWidget(self.size_select)
        self.combine_form_layout.addWidget(self.mo_noseq_select)
        self.combine_form_layout.addWidget(self.combine_proceed_button)

        sync_event_emitter.on(UserActionEvent.SIZE_LIST_CHANGE.value)(
            self.on_size_list_change
        )
        sync_event_emitter.on(UserActionEvent.EPC_DATA_CHANGE.value)(
            self.on_epc_data_change
        )
        async_event_emitter.on(UserActionEvent.MO_NO_CHANGE.value)(
            self.handle_get_mo_noseq
        )

    def on_size_list_change(self, data):
        self._size_list = data
        self.size_select.clear()
        self.size_select.addItems(map(lambda item: item["size_numcode"], data))

    def on_epc_data_change(self, data):
        self._epcs = data
        self.on_combine_from_state_change(
            "has_epc", isinstance(data, list) and len(data) > 0
        )

    async def handle_get_mo_noseq(self, selected_mo_no: str):
        self.on_combine_from_state_change("mo_no", selected_mo_no)

        try:
            if selected_mo_no:
                query = QSqlQuery(DATA_SOURCE_ERP)
                query.prepare(
                    f"""--sql
                        SELECT DISTINCT mo_noseq
                        FROM wuerp_vnrd.dbo.ta_manufacturdet
                        WHERE mo_no = :mo_no
                        ORDER BY mo_noseq ASC
                    """,
                )
                query.bindValue(":mo_no", selected_mo_no)
                query.exec()

                self.mo_noseq_select.clear()
                self.mo_noseq_select.addItem("Tất cả", "all")
                while query.next():
                    mo_noseq = query.value("mo_noseq") or "001"
                    self.mo_noseq_select.addItem(mo_noseq, mo_noseq)

        except Exception as e:
            logger.error(e)

    def handle_selected_size_change(self, value: str):
        """
        When user select a size, update the selected size in the form and set maxiumn EPC quantity that user need to scan
        """
        size_item = next(
            (item for item in self._size_list if item["size_numcode"] == value),
            None,
        )
        self.on_combine_from_state_change("size_numcode", size_item["size_numcode"])
        self.on_combine_from_state_change("size_code", size_item["size_qty"])
        sync_event_emitter.emit(UserActionEvent.SELECTED_SIZE_CHANGE.value, size_item)

    def handle_mo_noseq_change(self, selected_index: int):
        value = self.mo_noseq_select.itemData(selected_index)
        sync_event_emitter.emit(UserActionEvent.MO_NOSEQ_CHANGE.value, value)
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

        is_combinable = (
            combine_form_context["ri_type"] is not None
            and combine_form_context["mo_no"] is not None
            and combine_form_context["mo_noseq"] is not None
            and combine_form_context["size_numcode"] is not None
            and combine_form_context["size_code"] is not None
            and combine_form_context["mat_code"] is not None
            and combine_form_context["or_no"] is not None
            and combine_form_context["or_custpo"] is not None
            and combine_form_context["cust_shoestyle"] is not None
            # and combine_form_context["has_epc"]
        )

        self.combine_proceed_button.setEnabled(is_combinable)

    def on_combine_proceed(self):
        try:
            # combine_form_context.pop("has_epc")
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

            num_rows_affected = self.rfid_repository.insert_match(payload)
            sync_event_emitter.emit(
                UserActionEvent.COMBINED_EPC_CREATED.value,
                {
                    "size": combine_form_context["size_numcode"],
                    "qty": num_rows_affected,
                },
            )

            with open("./data/data.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(e)
