from ipaddress import ip_address
from pyqttoast import ToastPreset
from PyQt6.QtCore import *
from PyQt6.QtSql import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from uhf.reader import *
from helpers.logger import logger
from constants import CombineAction
from contexts.combine_form_context import combine_form_context

# Import widgets
from widgets.toaster import Toaster
from events import UserActionEvent, __event_emitter__
from helpers.configuration import ConfigService
from i18n import I18nService, I18nContext
from helpers.resolve_path import resolve_path
from themes.theme_manager import theme_manager
from themes.colors import Theme, get_color


class EpcReaderPlayground(QFrame, I18nContext):
    """
    EPC reader widget for scanning EPC from UHF reader
    """

    uhf_reader_instance: GClient | None = None
    """
    UHF reader instance

    Scope: public
    """

    # region Local states
    __max_epc_qty: int = 0
    __current_tab_index: int = 1

    def __init__(self, parent):
        super().__init__(parent)
        self.root = parent

        self.setObjectName("epc_reader_playground")
        self.setAutoFillBackground(True)
        self.setMinimumWidth(300)
        self.epc_reader_layout = QVBoxLayout(self)
        self.epc_reader_layout.setContentsMargins(8, 8, 8, 8)
        self.epc_reader_layout.setSpacing(8)
        self.setLayout(self.epc_reader_layout)

        # region Search box
        self.search_box_layout = QHBoxLayout()
        self.search_box_layout.setContentsMargins(0, 0, 0, 0)
        self.search_box_layout.setSpacing(2)
        self.search_box = QFrame(parent=self)
        self.search_box.setObjectName("search_box")
        self.search_box.setLayout(self.search_box_layout)
        self.search_box_input = QLineEdit(parent=self.search_box)
        self.search_box_input.setStyleSheet("border: none; padding: 0px")
        self.search_box_input.setPlaceholderText("Search ...")
        self.search_box_input.textChanged.connect(self.on_search)
        search_icon_label = QLabel()
        search_icon_label.setStyleSheet("border: none")
        search_pixmap = QPixmap(resolve_path("assets/icons/search.svg")).scaled(
            16,
            16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        search_icon_label.setPixmap(search_pixmap)
        self.search_box_layout.addWidget(search_icon_label)
        self.search_box_layout.addWidget(self.search_box_input)

        # endregion

        # region EPC list
        self.epc_list = QListWidget(parent=self)
        self.epc_list.setObjectName("epc_list")
        self.epc_list.setSortingEnabled(False)
        self.epc_list.setVisible(False)
        self.epc_list.setSpacing(2)
        self.epc_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.epc_list.itemSelectionChanged.connect(self.handle_epc_selection_changed)

        self.empty_state_layout = QHBoxLayout()
        self.empty_state_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_layout.setContentsMargins(0, 0, 0, 0)
        self.empty_state_layout.setSpacing(8)

        self.empty_state = QFrame(parent=self)
        self.empty_state.setObjectName("empty_state")
        self.empty_state.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        inbox_icon = QLabel(parent=self.empty_state)
        pixmap = QPixmap(resolve_path("assets/icons/inbox.svg")).scaled(
            24,
            24,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        inbox_icon.setPixmap(pixmap)

        self.empty_text = QLabel(parent=self.empty_state)
        self.empty_text.setText("No data")
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text.setObjectName("empty_text")

        self.empty_state.setLayout(self.empty_state_layout)
        self.empty_state_layout.addWidget(
            inbox_icon, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.empty_state_layout.addWidget(
            self.empty_text, alignment=Qt.AlignmentFlag.AlignCenter
        )
        # endregion

        # region EPC actions group
        delete_icon = QIcon()
        delete_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/trash-2.svg")),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.delete_button = QPushButton(parent=self)
        self.delete_button.setObjectName("delete_button")
        self.delete_button.setToolTip("Delete")
        self.delete_button.setText("Delete")
        self.delete_button.setEnabled(False)
        self.delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_button.clicked.connect(self.handle_delete_selected_epcs)
        # endregion

        # region Reader actions group
        self.epc_list_action_group_layout = QHBoxLayout()
        self.epc_list_action_group_layout.setContentsMargins(4, 2, 4, 2)
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
            QPixmap(resolve_path("assets/icons/plug-zap.svg")).scaled(24, 24),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.unplug_icon = QIcon()
        self.unplug_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/unplug.svg")).scaled(24, 24),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        # Helper to set icon size for buttons

        self.toggle_connect_button = QPushButton(parent=self.reader_actions_group)
        self.toggle_connect_button.setObjectName("toggle_connect_button")
        self.toggle_connect_button.setFixedSize(36, 36)
        self.toggle_connect_button.setIconSize(QSize(20, 20))
        self.toggle_connect_button.setIcon(self.plug_icon)
        self.toggle_connect_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_connect_button.setCheckable(True)
        self.toggle_connect_button.setChecked(False)
        self.toggle_connect_button.toggled.connect(self.handle_toggle_connect)

        # Toggle start/stop reader
        self.play_icon = QIcon()
        self.play_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/play.svg")).scaled(24, 24),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.pause_icon = QIcon()
        self.pause_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/pause.svg")).scaled(24, 24),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.toggle_play_button = QPushButton(parent=self.reader_actions_group)
        self.toggle_play_button.setObjectName("toggle_play_button")
        self.toggle_play_button.setCheckable(True)
        self.toggle_play_button.setChecked(False)
        self.toggle_play_button.setToolTip("Bắt đầu đọc")
        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setFixedSize(36, 36)
        self.toggle_play_button.setIconSize(QSize(20, 20))
        self.toggle_play_button.setEnabled(False)
        self.toggle_play_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_play_button.toggled.connect(self.handle_toggle_play)

        # Reset all reader data
        self.reset_icon = QIcon()
        self.reset_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/rotate-ccw.svg")).scaled(24, 24),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.reset_btn = QPushButton(parent=self.reader_actions_group)
        self.reset_btn.setIcon(self.reset_icon)
        self.reset_btn.setFixedSize(36, 36)
        self.reset_btn.setIconSize(QSize(20, 20))
        self.reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.setToolTip("Đặt lại danh sách quét")
        self.reset_btn.clicked.connect(self.handle_reset_scanned_epc)

        self.scanned_epc_counter = QLabel(parent=self.reader_actions_group)
        self.scanned_epc_counter.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.scanned_epc_counter.setObjectName("scanned_epc_counter")
        self.scanned_epc_counter.setStyleSheet("font-weight: 600; font-size: 18px")

        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.reader_actions_group_layout.addWidget(self.toggle_connect_button)
        self.reader_actions_group_layout.addWidget(self.toggle_play_button)
        self.reader_actions_group_layout.addWidget(self.reset_btn)

        self.epc_list_action_group_layout.addWidget(self.reader_actions_group)
        self.epc_list_action_group_layout.addItem(self.spacer)
        self.epc_list_action_group_layout.addWidget(self.scanned_epc_counter)
        # endregion

        self.epc_reader_layout.addWidget(self.search_box)
        self.epc_reader_layout.addWidget(self.epc_list)
        self.epc_reader_layout.addWidget(self.empty_state)
        self.epc_reader_layout.addWidget(self.delete_button)
        self.epc_reader_layout.addWidget(self.epc_list_action_group)

        # region Event listeners
        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)

        __event_emitter__.on(UserActionEvent.MO_NO_CHANGE.value)(self.on_mo_no_change)

        __event_emitter__.on(UserActionEvent.SIZE_LIST_CHANGE.value)(
            self.on_size_list_change
        )

        __event_emitter__.on(UserActionEvent.COMBINE_FORM_STATE_CHANGE.value)(
            self.on_combine_form_state_change
        )

        __event_emitter__.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )

        __event_emitter__.on(UserActionEvent.INVALID_COMBINATION_FOUND.value)(
            self.on_invalid_combination_found
        )

        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(
            self.update_theme_styles
        )
        # endregion

        # Apply initial theme
        self.update_theme_styles()

    def __translate__(self):
        if self.__current_tab_index == 1:
            self.scanned_epc_counter.setText(
                I18nService.t(
                    "labels.scanned",
                    plurals={"count": f"{self.epc_list.count()}/{self.__max_epc_qty}"},
                )
            )
        else:
            self.scanned_epc_counter.setText(
                I18nService.t(
                    "labels.scanned", plurals={"count": str(self.epc_list.count())}
                )
            )
        self.reset_btn.setToolTip(I18nService.t("actions.reset"))
        self.delete_button.setText(I18nService.t("actions.delete"))
        if self.toggle_connect_button.isChecked():
            self.toggle_connect_button.setToolTip(
                I18nService.t("actions.disconnect_uhf_reader")
            )
        else:
            self.toggle_connect_button.setToolTip(
                I18nService.t("actions.connect_uhf_reader")
            )
        if self.toggle_connect_button.isChecked():
            self.toggle_play_button.setToolTip(I18nService.t("actions.stop_reading"))
        else:
            self.toggle_play_button.setToolTip(I18nService.t("actions.start_reading"))

    def update_theme_styles(self, theme: Theme = None):
        """Update widget colors based on current theme"""
        if theme is None:
            theme = theme_manager.current_theme

        # Get colors from theme
        bg_color = get_color(theme, "card")
        fg_color = get_color(theme, "foreground")
        border_color = get_color(theme, "border")
        muted_fg_color = get_color(theme, "muted-foreground")

        # Update search_box style
        self.search_box.setStyleSheet(
            f"height: 36px; background-color: {bg_color}; color: {fg_color}; border: 1px solid {border_color}; border-radius: 4px; padding: 0px 4px;"
        )

        # Update empty_state style
        self.empty_state.setStyleSheet(f"background: {bg_color}; border-radius: 4px")

        # Update empty_text style
        self.empty_text.setStyleSheet(f"color: {muted_fg_color}")

        # Force update
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


    def on_mo_no_change(self, _):
        self.__max_epc_qty = 0
        self.handle_reset_scanned_epc(toastify=False)

    def on_size_list_change(self, data):
        if (
            combine_form_context["size_numcode"] == ""
            or combine_form_context["size_numcode"] is None
        ):
            return
        curr_size_data = next(
            (
                item
                for item in data
                if item.get("size_numcode") == combine_form_context["size_numcode"]
            ),
            0,
        )
        if (
            isinstance(curr_size_data, dict)
            and combine_form_context["ri_type"] == CombineAction.COMBINE_NEW.value
        ):
            self.__max_epc_qty = (
                curr_size_data["size_qty"] - curr_size_data["in_use_qty"]
            )
            self.scanned_epc_counter.setText(
                self.__get_counter_text(
                    combine_form_context["ri_type"], self.epc_list.count()
                )
            )

    def on_combined_epc_created(self, _: dict):
        self.epc_list.clear()
        self.handle_reset_scanned_epc(toastify=False)
        self.__max_epc_qty = 0
        self.scanned_epc_counter.setText(
            self.__get_counter_text(combine_form_context["ri_type"], 0)
        )

    def on_invalid_combination_found(self, data: list[dict]):
        for i in range(self.epc_list.count()):
            item = self.epc_list.item(i)
            epc_value = item.text()
            # * Find EPCs having recombinable = False, if found, highlight the item
            match = next(
                (
                    d
                    for d in data
                    if d.get("EPC_Code") == epc_value and d.get("recombinable") is False
                ),
                None,
            )
            if match is not None:
                item.setForeground(QColor("#ff4d4f"))  # Highlight background

    def on_combine_form_state_change(self, data):
        # * Only when size is selected, enable the connect button
        self.__max_epc_qty = data["size_qty"] - data["combined_qty"]
        self.scanned_epc_counter.setText(
            self.__get_counter_text(data["ri_type"], self.epc_list.count())
        )

    def __get_counter_text(self, type: str, acc_qty: int) -> str:
        if type == CombineAction.COMBINE_NEW.value:
            return I18nService.t(
                "labels.scanned",
                plurals={"count": f"{acc_qty}/{self.__max_epc_qty}"},
            )
        else:
            return I18nService.t(
                "labels.scanned",
                plurals={"count": acc_qty},
            )

    @pyqtSlot()
    def handle_epc_selection_changed(self):
        selected_items = self.epc_list.selectedItems()
        selected_epcs = [item.text() for item in selected_items]
        self.delete_button.setEnabled(len(selected_epcs) > 0)
        if len(selected_items) > 0:
            self.delete_button.setText(
                f"{I18nService.t("actions.delete")} {I18nService.t(
                    "labels.selected", plurals={"count": str(len(selected_epcs))}
                )}"
            )
        else:
            self.delete_button.setText(I18nService.t("actions.delete"))

    @pyqtSlot()
    def handle_delete_selected_epcs(self):
        for item in self.epc_list.selectedItems():
            row = self.epc_list.row(item)
            self.epc_list.takeItem(row)
            self.epc_list.count()
            self.scanned_epc_counter.setText(
                self.__get_counter_text(
                    combine_form_context["ri_type"],
                    self.epc_list.count(),
                )
            )
        epc_data = [self.epc_list.item(i).text() for i in range(self.epc_list.count())]
        __event_emitter__.emit(UserActionEvent.EPC_DATA_CHANGE.value, epc_data)

    def __on_receive_epc(self, epcInfo: LogBaseEpcInfo):
        try:
            if epcInfo.result == 0:
                epc = epcInfo.epc.upper()
                should_insert = not any(
                    self.epc_list.item(i).text() == epc
                    for i in range(self.epc_list.count())
                )
                if (
                    self.toggle_connect_button.isChecked()
                    and self.toggle_play_button.isChecked()
                    and should_insert
                ):
                    self.epc_list.addItem(epc)
                    self.epc_list.sortItems(Qt.SortOrder.AscendingOrder)
                    self.epc_list.setVisible(True)
                    self.empty_state.setVisible(False)
                    self.scanned_epc_counter.setText(
                        self.__get_counter_text(
                            combine_form_context.get("ri_type"),
                            self.epc_list.count(),
                        )
                    )
                    epc_data = [
                        self.epc_list.item(i).text()
                        for i in range(self.epc_list.count())
                    ]
                    __event_emitter__.emit(
                        UserActionEvent.EPC_DATA_CHANGE.value, epc_data
                    )
        except Exception as e:
            logger.error(f"Error in on_receive_epc: {e}")

    def __on_receive_epc_end(self, epcOver: LogBaseEpcOver):
        logger.info(f"Stopped with message id: >>> {epcOver.msgId}")

    @pyqtSlot(str)
    def on_search(self, search_term: str):
        match_count = 0
        for i in range(self.epc_list.count()):
            item = self.epc_list.item(i)
            if search_term.upper() in item.text().upper():
                match_count += 1
            item.setHidden(search_term.upper() not in item.text().upper())
        self.epc_list.setVisible(match_count > 0)
        self.empty_state.setVisible(match_count == 0)

    @pyqtSlot(bool)
    def handle_toggle_connect(self, checked_state: bool):

        uhf_reader_tcp_ip = ConfigService.get_env("UHF_READER_TCP_IP")
        uhf_reader_port = ConfigService.get_env("UHF_READER_TCP_PORT")

        if not ip_address(uhf_reader_tcp_ip) or not uhf_reader_port.isnumeric():
            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notification.failure_connection_uhf_title"),
                text=I18nService.t("notification.failure_connection_uhf_text"),
                preset=ToastPreset.ERROR,
            )
            toast.show()
            return
        try:
            if not checked_state:
                signal = self.__handle_stop_reading()
                if signal:
                    logger.info("Stopped reading successfully.")
                self.toggle_connect_button.setIcon(self.plug_icon)
                self.toggle_play_button.setIcon(self.play_icon)
                self.toggle_connect_button.setToolTip("Kết nối máy UHF")
                self.reset_btn.setEnabled(True)
                self.toggle_play_button.setEnabled(False)
                self.uhf_reader_instance.close()
                self.uhf_reader_instance.callTcpDisconnect
                self.uhf_reader_instance = None

            else:
                if self.uhf_reader_instance is None:
                    self.uhf_reader_instance = GClient()
                if self.uhf_reader_instance.openTcp(
                    (uhf_reader_tcp_ip, int(uhf_reader_port))
                ):
                    self.toggle_connect_button.setIcon(self.unplug_icon)
                    self.toggle_connect_button.setToolTip("Ngắt kết nối máy UHF")

                    self.toggle_play_button.setEnabled(True)
                    self.uhf_reader_instance.callEpcOver = self.__on_receive_epc_end
                    self.uhf_reader_instance.callEpcInfo = (
                        lambda epcInfo: self.__on_receive_epc(epcInfo)
                    )

        except Exception as e:
            self.uhf_reader_instance = GClient()
            self.handle_toggle_connect(self, checked_state)
            logger.error(f"Error in handle_toggle_connect: {e}")

    @pyqtSlot(bool)
    def handle_toggle_play(self, checked_state: bool):
        try:
            if checked_state:
                self.__handle_start_reading()
            else:
                self.__handle_stop_reading()
        except Exception as e:
            logger.error(f"Error in handle_toggle_play: {e}")

    def __handle_stop_reading(self) -> bool:
        self.toggle_play_button.setIcon(self.play_icon)
        self.toggle_play_button.setToolTip("Bắt đầu đọc")
        res = self.uhf_reader_instance.sendSynMsg(MsgBaseStop())
        if isinstance(res, int):
            logger.debug(f"Stop reading signal :>>>> {res}")

    def __handle_start_reading(self):
        self.toggle_play_button.setToolTip(I18nService.t("actions.stop_reading"))
        self.toggle_play_button.setIcon(self.pause_icon)

        # * Set beep sound
        self.uhf_reader_instance.sendSynMsg(MsgAppSetBeep(0, 0))

        # * Setup reader power
        FALLBACK_POWER_VALUE: int = 10
        reader_power = ConfigService.get_env("UHF_READER_POWER")
        reader_power = (
            FALLBACK_POWER_VALUE
            if reader_power == "" or reader_power is None or not reader_power.isdigit()
            else int(reader_power)
        )
        dict_power = {
            "1": reader_power,
            "2": reader_power,
            "3": reader_power,
            "4": reader_power,
        }
        self.uhf_reader_instance.sendSynMsg(MsgBaseSetPower(**dict_power))

        # * Setup reader antenna
        reader_ant = ConfigService.get_env(
            "UHF_READER_ANT",
        )
        reader_ant = (
            EnumG.AntennaNo_1.value
            if reader_ant == "" or reader_ant is None or not reader_ant.isdigit()
            else int(reader_ant)
        )
        self.uhf_reader_instance.sendSynMsg(
            MsgBaseInventoryEpc(
                antennaEnable=reader_ant,
                inventoryMode=EnumG.InventoryMode_Inventory.value,
            )
        )

    @pyqtSlot()
    def handle_reset_scanned_epc(self, toastify: bool = True):
        self.epc_list.clear()
        # * Update UI on after reset scanned EPCs
        self.empty_state.setVisible(True)
        self.epc_list.setVisible(False)
        self.scanned_epc_counter.setText(
            self.__get_counter_text(combine_form_context["ri_type"], 0)
        )

        __event_emitter__.emit(UserActionEvent.EPC_DATA_CHANGE.value, [])
        if toastify:
            toast = Toaster(
                parent=self.root,
                title=I18nService.t("notification.reset_epc_success_title"),
                text=I18nService.t("notification.reset_epc_success_text"),
            )
            toast.show()
