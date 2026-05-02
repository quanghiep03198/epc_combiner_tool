from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from typing import Callable

from repositories.sizing_repository import SizingRepository
from helpers.logger import logger
from events import __event_emitter__, UserActionEvent
from widgets.loading_widget import LoadingWidget
from i18n import I18nService, I18nContext
from widgets.toaster import Toaster, ToastPreset

from contexts.combine_form_context import combine_form_context
from themes.theme_manager import theme_manager
from themes.colors import get_color


class WorkerSignals(QObject):
    """
    Defines the signals available for storing data worker thread.
    """

    fulfill = pyqtSignal(int)
    error = pyqtSignal(Exception)


class SuborderMigrationWorker(QRunnable):
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
            query_result = SizingRepository.migrate_to_suborder(self.payload)
            logger.debug(f"Query result: {query_result}, type: {type(query_result)}")
            if isinstance(query_result, int):
                self.signals.fulfill.emit(query_result)
            else:
                logger.error(f"Query result is not an int, it's {type(query_result)}")
                self.signals.fulfill.emit(0)
        except Exception as e:
            logger.error(e.args)
            self.signals.error.emit(e)


class AdditionalQtyDelegate(QStyledItemDelegate):
    """Custom delegate cho ô additional_qty với placeholder và validation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent  # Lưu parent để dùng sau này
        self.max_values = {}  # Lưu max value cho mỗi cột: {col: max_value}
        self.size_codes = {}  # Lưu size_numcode cho mỗi cột: {col: size_code}
        self.current_editing_col = None  # Lưu column đang edit
        self.current_editing_row = 6  # Row của additional_qty luôn là 6
        self.enter_pressed = False  # Flag để check xem có phải Enter được nhấn không

    def set_max_value(self, col: int, max_value: int):
        """Set max value cho một column"""
        self.max_values[col] = max_value

    def set_size_code(self, col: int, size_code: str):
        """Set size_numcode cho một column"""
        self.size_codes[col] = size_code

    def createEditor(self, parent, option, index):
        """Tạo editor với validation"""
        editor = QLineEdit(parent)

        # Lấy max value cho column này
        max_value = self.max_values.get(index.column(), 999)

        # Set placeholder
        editor.setPlaceholderText(f"Max: {max_value}")

        # Validator: chỉ cho phép số từ 1 đến max_value
        validator = QIntValidator(1, max_value, editor)
        editor.setValidator(validator)

        # Set geometry để chiếm full width của cell
        editor.setGeometry(option.rect)

        # Style cho editor - full width
        # Theme-aware styles
        card_bg = get_color(theme_manager.current_theme, "card")
        fg = get_color(theme_manager.current_theme, "foreground")
        accent = get_color(theme_manager.current_theme, "accent")
        muted_fg = get_color(theme_manager.current_theme, "muted-foreground")

        editor.setStyleSheet(f"""
            QLineEdit {{
                width: 100%;
                padding: 6px 8px;
                border: 2px solid {accent};
                background-color: {card_bg};
                color: {fg};
                font-size: 14px;
            }}
            QLineEdit::placeholder {{
                width: 100%;
                color: {muted_fg};
                font-size: 14px;
            }}
        """)

        # Connect signal để validate realtime
        editor.textChanged.connect(
            lambda text: self._on_text_changed(editor, text, max_value)
        )

        # Connect returnPressed để bắt sự kiện Enter
        editor.returnPressed.connect(lambda: self._on_enter_pressed())

        return editor

    def _on_enter_pressed(self):
        """Được gọi khi user nhấn Enter"""
        self.enter_pressed = True

    def _on_text_changed(self, editor: QLineEdit, text: str, max_value: int):
        """Validate realtime khi user đang nhập"""
        if not text:
            return

        try:
            value = int(text)
            # Nếu vượt quá max, block và reset
            if value > max_value:
                # Lấy text trước đó (bỏ ký tự cuối)
                editor.setText(text[:-1])
                destructive = get_color(theme_manager.current_theme, "destructive")
                card_bg = get_color(theme_manager.current_theme, "card")
                muted_fg = get_color(theme_manager.current_theme, "muted-foreground")
                fg = get_color(theme_manager.current_theme, "foreground")

                editor.setStyleSheet(f"""
                    QLineEdit {{
                        width: 100%;
                        padding: 6px 8px;
                        border: 2px solid {destructive};
                        background-color: {card_bg};
                        color: {fg};
                        font-size: 14px;
                    }}
                    QLineEdit::placeholder {{
                        width: 100%;
                        color: {muted_fg};
                        font-size: 14px;
                    }}
                """)
            elif value < 1:
                destructive = get_color(theme_manager.current_theme, "destructive")
                card_bg = get_color(theme_manager.current_theme, "card")
                muted_fg = get_color(theme_manager.current_theme, "muted-foreground")
                editor.setStyleSheet(f"""
                    QLineEdit {{
                        width: 100%;
                        padding: 6px 8px;
                        border: 2px solid {destructive};
                        background-color: {card_bg};
                        color: {fg};
                        font-size: 14px;
                    }}
                    QLineEdit::placeholder {{
                        width: 100%;
                        color: {muted_fg};
                        font-size: 14px;
                    }}
                """)
            else:
                # Valid
                success = get_color(theme_manager.current_theme, "success")
                card_bg = get_color(theme_manager.current_theme, "card")
                muted_fg = get_color(theme_manager.current_theme, "muted-foreground")
                editor.setStyleSheet(f"""
                    QLineEdit {{
                        width: 100%;
                        padding: 6px 8px;
                        border: 2px solid {success};
                        background-color: {card_bg};
                        color: {fg};
                        font-size: 14px;
                    }}
                    QLineEdit::placeholder {{
                        width: 100%;
                        color: {muted_fg};
                        font-size: 14px;
                    }}
                """)
        except ValueError:
            pass

    def updateEditorGeometry(self, editor, option, index):
        """Update geometry để editor chiếm full width"""
        editor.setGeometry(option.rect)

    def setEditorData(self, editor, index):
        """Set data vào editor khi bắt đầu edit"""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)

        # Nếu giá trị là placeholder hoặc rỗng thì không set
        if value and not str(value).startswith("Max:"):
            editor.setText(str(value))
        else:
            editor.clear()

    def setModelData(self, editor, model, index):
        """Lưu data từ editor vào model"""
        text = editor.text().strip()
        col = index.column()
        max_value = self.max_values.get(col, 999)

        # Nếu rỗng, set lại placeholder
        if not text:
            model.setData(index, f"Max: {max_value}", Qt.ItemDataRole.DisplayRole)
            return

        # Validate lần cuối
        try:
            value = int(text)

            if value < 1:
                # Hiển thị lỗi
                QMessageBox.warning(
                    editor,
                    I18nService.t("messages.invalid_value"),
                    I18nService.t("messages.quantity_must_be_at_least_one"),
                )
                model.setData(index, f"Max: {max_value}", Qt.ItemDataRole.DisplayRole)
                return

            if value > max_value:
                # Hiển thị lỗi
                QMessageBox.warning(
                    editor,
                    I18nService.t("messages.invalid_value"),
                    I18nService.t("messages.quantity_cannot_exceed_max").replace(
                        "{max_value}", str(max_value)
                    ),
                )
                model.setData(index, f"Max: {max_value}", Qt.ItemDataRole.DisplayRole)
                return

            # Giá trị hợp lệ - Lưu vào model
            model.setData(index, value, Qt.ItemDataRole.EditRole)

            # Chỉ submit khi Enter được nhấn
            if self.enter_pressed:
                # Hiển thị dialog xác nhận
                reply = QMessageBox.question(
                    editor,
                    I18nService.t(key="actions.confirm_save"),
                    I18nService.t(
                        key="notification.confirm_migrate_suborder",
                        plurals={
                            "mo_noseq": combine_form_context.get("mo_noseq"),
                            "size_numcode": self.size_codes.get(col, "Unknown"),
                            "additional_qty": str(value),
                        },
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Lưu column đang edit để reset sau khi thành công
                    self.current_editing_col = col

                    # Log data
                    size_code = self.size_codes.get(col, "Unknown")
                    self.migrateToCurrentSubOrder(size_code, value)
                else:
                    # User chọn No - reset về placeholder
                    model.setData(
                        index, f"Max: {max_value}", Qt.ItemDataRole.DisplayRole
                    )

                # Reset flag
                self.enter_pressed = False

        except ValueError:
            # Không phải số hợp lệ
            model.setData(index, f"Max: {max_value}", Qt.ItemDataRole.DisplayRole)

    def migrateToCurrentSubOrder(self, size_numcode: str, quantity: int):
        """Log data người dùng đã nhập"""
        data = {
            "mo_no": combine_form_context.get("mo_no"),
            "mo_noseq": combine_form_context.get("mo_noseq"),
            "size_numcode": size_numcode,
            "additional_qty": quantity,
        }
        logger.info(f"[AdditionalQtyDelegate] User input: {data}")
        worker = SuborderMigrationWorker(
            data, self.on_mutate_success, self.on_mutate_error
        )
        QThreadPool.globalInstance().start(worker)

    @pyqtSlot(int)
    def on_mutate_success(self, numRowsAffected: int):
        # Reset cell về placeholder
        if self.parent_widget and self.current_editing_col is not None:
            max_value = self.max_values.get(self.current_editing_col, 999)
            item = self.parent_widget.item(
                self.current_editing_row, self.current_editing_col
            )
            if item:
                item.setText(f"Max: {max_value}")
                item.setForeground(
                    QBrush(
                        QColor(
                            get_color(theme_manager.current_theme, "muted-foreground")
                        )
                    )
                )

        # Refetch data table
        __event_emitter__.emit(
            UserActionEvent.MO_NOSEQ_CHANGE.value, combine_form_context["mo_noseq"]
        )

        Toaster(
            parent=self.parent_widget.root,
            title=I18nService.t("notification.migrate_to_suborder_success_title"),
            text=I18nService.t(
                "notification.migrate_to_suborder_success_text",
                plurals={
                    "quantity": str(numRowsAffected),
                    "mo_noseq": combine_form_context["mo_noseq"],
                },
            ),
            preset=ToastPreset.SUCCESS_DARK,
        ).show()

    @pyqtSlot(Exception)
    def on_mutate_error(self, error: Exception):
        logger.error(error)
        if self.parent_widget and hasattr(self.parent_widget, "root"):
            Toaster(
                parent=self.parent_widget.root,
                title=I18nService.t("notification.migrate_to_suborder_failure_title"),
                text=I18nService.t("notification.migrate_to_suborder_failure_text"),
                preset=ToastPreset.ERROR_DARK,
            ).show()

    def displayText(self, value, locale):
        """Hiển thị text trong cell"""
        # Nếu là placeholder format thì giữ nguyên
        if isinstance(value, str) and value.startswith("Max:"):
            return value
        # Nếu là số thì convert sang string
        return str(value) if value else ""

    def paint(self, painter, option, index):
        """Custom paint để hiển thị placeholder với style khác"""
        value = index.data(Qt.ItemDataRole.DisplayRole)

        # Nếu là placeholder
        if isinstance(value, str) and value.startswith("Max:"):
            # Vẽ background
            painter.save()
            # Use theme card color for editor background and muted color for placeholder
            painter.fillRect(
                option.rect, QColor(get_color(theme_manager.current_theme, "card"))
            )

            # Vẽ text với màu placeholder
            painter.setPen(
                QColor(get_color(theme_manager.current_theme, "muted-foreground"))
            )
            font = painter.font()
            font.setPointSize(11)  # Giảm cỡ chữ cho placeholder
            painter.setFont(font)

            # Tạo rect với padding bên trái để text không sát mép
            text_rect = option.rect.adjusted(8, 0, 0, 0)

            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                value,
            )
            painter.restore()
        else:
            # Vẽ bình thường
            super().paint(painter, option, index)


class FetchSizeDataWorker(
    QRunnable,
):
    def __init__(self, params: dict, callback: Callable[[list[dict]], None]):
        super().__init__()
        self.mo_no = params["mo_no"]
        self.mo_noseq = params["mo_noseq"]
        self.callback = callback

    @pyqtSlot()
    def run(self):
        query_result = SizingRepository.find_size_qty(
            {"mo_no": self.mo_no, "mo_noseq": self.mo_noseq}
        )
        self.callback(query_result)


class SizingDetailTableWidget(QTableWidget, I18nContext):
    """
    Table for displaying sizing details
    """

    def __init__(self, root):
        super().__init__(root.container)
        self.root = root

        # Tạo delegate cho hàng 6
        self.additional_qty_delegate = AdditionalQtyDelegate(self)

        self.setContentsMargins(2, 2, 2, 2)
        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.setMidLineWidth(1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setFont(QFont("Inter", 12, QFont.Weight.Bold))

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.COMBINED_EPC_CREATED.value)(
            self.on_combined_epc_created
        )
        __event_emitter__.on(UserActionEvent.MO_NO_CHANGE.value)(
            lambda _: self.handle_fetch_size_data(
                {
                    "mo_no": combine_form_context["mo_no"],
                    "mo_noseq": combine_form_context["mo_noseq"],
                }
            )
        )
        __event_emitter__.on(UserActionEvent.MO_NOSEQ_CHANGE.value)(
            self.on_mo_noseq_change
        )

    def __translate__(self):
        self.__handle_update_table_display()

    def __handle_update_table_display(self):
        self.vertical_header_labels: list[str] = [
            I18nService.t("fields.size_numcode"),
            I18nService.t("fields.size_qty"),
            I18nService.t("fields.combined_qty"),
            I18nService.t("fields.in_use_qty"),
            I18nService.t("fields.compensated_qty"),
            I18nService.t("fields.cancelled_qty"),
        ]
        if (
            combine_form_context["mo_noseq"] is not None
            and combine_form_context["mo_noseq"] != "all"
            and combine_form_context["mo_noseq"] != "001"
        ):
            self.vertical_header_labels.append(I18nService.t("fields.additional_qty"))
        self.setRowCount(len(self.vertical_header_labels))
        for row in range(len(self.vertical_header_labels)):
            self.setRowHeight(row, 36)
        self.resizeRowsToContents()
        self.setVerticalHeaderLabels(self.vertical_header_labels)

    def on_mo_noseq_change(self, value: str):
        self.__handle_update_table_display()
        self.handle_fetch_size_data(
            {
                "mo_no": combine_form_context["mo_no"],
                "mo_noseq": value,
            }
        )

    def handle_fetch_size_data(self, data: dict):
        try:
            self.loading = LoadingWidget(self)
            self.loading.show_loading()
            worker = FetchSizeDataWorker(data, self.on_fetch_size_data_success)
            QThreadPool.globalInstance().start(worker)
        except Exception as e:
            logger.error(f"[SizingDetailTableWidget] Error reading SQL file: {e}")

    def on_fetch_size_data_success(self, result: list[dict]):
        try:
            self.setColumnCount(len(result))
            __event_emitter__.emit(UserActionEvent.SIZE_LIST_CHANGE.value, result)
            col: int = 0
            for record in result:
                # Tạo các items cho từng hàng
                self.setItem(0, col, QTableWidgetItem(str(record["size_numcode"])))
                self.setItem(1, col, QTableWidgetItem(str(record["size_qty"])))
                self.setItem(2, col, QTableWidgetItem(str(record["combined_qty"])))
                self.setItem(3, col, QTableWidgetItem(str(record["in_use_qty"])))
                self.setItem(4, col, QTableWidgetItem(str(record["compensated_qty"])))
                self.setItem(5, col, QTableWidgetItem(str(record["cancelled_qty"])))

                # Set tất cả các ô từ hàng 0-5 là read-only
                for row in range(6):
                    if self.item(row, col):
                        self.item(row, col).setFlags(
                            Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                        )

                # Chỉ hàng 6 mới editable (khi có sub-order hợp lệ)
                if (
                    combine_form_context["mo_noseq"] is not None
                    and combine_form_context["mo_noseq"] != "all"
                    and combine_form_context["mo_noseq"] != "001"
                ):
                    # Hàng 6: Set placeholder "Max: X"
                    max_add_qty = record["max_add_qty"]
                    size_numcode = record["size_numcode"]

                    # Tạo placeholder item
                    placeholder_item = QTableWidgetItem(f"Max: {max_add_qty}")
                    placeholder_item.setForeground(QBrush(QColor("#737373")))
                    placeholder_item.setFont(
                        QFont("Inter", 10, QFont.Weight.Normal, False)
                    )
                    self.setItem(6, col, placeholder_item)

                    # Set max value và size_code cho delegate
                    self.additional_qty_delegate.set_max_value(col, max_add_qty)
                    self.additional_qty_delegate.set_size_code(col, size_numcode)

                    # Set flags để có thể edit
                    self.item(6, col).setFlags(
                        Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsEditable
                    )

                    # Set delegate cho hàng 6
                    self.setItemDelegateForRow(6, self.additional_qty_delegate)

                self.handle_highlight_qty(
                    2, col, record["size_qty"], record["combined_qty"]
                )
                self.handle_highlight_qty(
                    3, col, record["size_qty"], record["in_use_qty"]
                )

                if (
                    combine_form_context["size_numcode"] is not None
                    and record["size_numcode"] == combine_form_context["size_numcode"]
                ):
                    combine_form_context.update(combined_qty=record["combined_qty"])
                    combine_form_context.update(in_use_qty=record["in_use_qty"])

                col += 1
        except Exception as e:
            logger.error(e)
        finally:
            self.loading.close_loading()

    def on_combined_epc_created(self, data: dict):
        self.handle_fetch_size_data(
            {
                "mo_no": data.get("mo_no"),
                "mo_noseq": data.get("mo_noseq"),
            }
        )

    def handle_highlight_qty(
        self, row: int, col: int, original_qty: int, actual_qty: int
    ):
        if actual_qty == original_qty:
            self.item(row, col).setForeground(
                QBrush(QColor(get_color(theme_manager.current_theme, "success")))
            )
        elif actual_qty > original_qty:
            self.item(row, col).setForeground(
                QBrush(QColor(get_color(theme_manager.current_theme, "destructive")))
            )
        else:
            self.item(row, col).setForeground(
                QBrush(QColor(get_color(theme_manager.current_theme, "warning")))
            )
