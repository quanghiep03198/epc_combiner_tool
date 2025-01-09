from helpers.logger import logger
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSql import QSqlQuery
from contexts.combine_form_context import combine_form_context
from database import DATA_SOURCE_ERP
from events import sync_event_emitter, UserActionEvent
from widgets.loading import LoadingWidget

# mo_no_change_event = AsyncIOEventEmitter()


class OrderAutoCompleteWidget(QPushButton):
    """
    Custom autocomplete for searching manufacturing order
    """

    def __init__(self, root):
        super().__init__(root.container)

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            "height: 32px; background-color: #171717; border: 1px solid #404040; color: #fafafa; text-align: left; padding: 2px 8px; font-weight: 400;"
        )

        chevron_icon = QIcon()
        chevron_icon.addPixmap(
            QPixmap("./assets/icons/chevrons-up-down.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.setIcon(chevron_icon)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setIconSize(QSize(14, 14))
        self.setObjectName("manuOrderPopoverTrigger")
        self.clicked.connect(self.on_open)

        self.popover_content = QDialog(self)
        self.popover_content.setGraphicsEffect(None)
        self.popover_content.setStyleSheet(
            "border: 1px solid #404040; border-radius: 4px; background-color: #171717"
        )
        self.popover_content.setMaximumHeight(190)
        self.popover_content.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.popover_content_layout = QVBoxLayout()
        self.popover_content_layout.setContentsMargins(2, 2, 2, 2)
        self.popover_content_layout.setSpacing(0)
        self.popover_content.setLayout(self.popover_content_layout)
        self.popover_input = QLineEdit(self.popover_content)
        self.popover_input.setStyleSheet(
            "border: 0px; border-bottom: 1px solid #404040; border-radius: 0px; height: 32px; padding: 2px 8px; background-color: #171717"
        )
        self.popover_input.setPlaceholderText("Search...")
        self.popover_input.textChanged.connect(self.on_input)

        self.popover_content.layout().addWidget(self.popover_input)
        self.popover_menu_list = QListWidget(self.popover_content)
        self.popover_menu_list.setStyleSheet(
            "border: 0px; padding: 4px; background-color: #171717"
        )

        self.popover_menu_list.clear()
        self.popover_menu_list.itemClicked.connect(
            lambda item: self.on_value_change(item)
        )
        self.popover_content.layout().addWidget(self.popover_menu_list)

        self.loading = LoadingWidget(root, "Đang tải dữ liệu ...")

        if combine_form_context["mo_no"] is None:
            self.setText("Chọn chỉ lệnh")

        self.handle_find_mo_no("")

    @pyqtSlot()
    def on_open(self) -> None:
        """
        Handles the event when the widget is opened.

        This method calculates the geometry of the button and sets the position
        and size of the popover content relative to the button's position. It then
        displays the popover content. If an exception occurs during this process,
        it logs the error.

        Raises:
            Exception: If an error occurs during the execution of the method.
        """
        try:
            button_geometry = self.geometry()
            global_position = self.mapToGlobal(button_geometry.bottomLeft())
            self.popover_input.setFocus()
            self.popover_content.setGeometry(
                global_position.x() - button_geometry.x(),
                global_position.y(),
                button_geometry.width(),
                250,
            )
            self.popover_content.exec()
        except Exception as e:
            logger.error(e)

    @pyqtSlot(str)
    def on_input(self, q: str) -> None:
        if hasattr(self, "debounce_timer") and self.debounce_timer.isActive():
            self.debounce_timer.stop()

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(lambda: self.handle_find_mo_no(q))
        self.debounce_timer.start(200)  # 200ms debounce time

    # * Handle select manufacturing order
    @pyqtSlot(QListWidgetItem)
    def on_value_change(self, item: QListWidgetItem) -> None:
        """
        Handles the event when the value of the item changes.

        This method is triggered when the value of the item changes. It displays a loading indicator,
        retrieves the text value from the item, sets the text value, closes the popover content, emits
        a "mo_no_change" event, processes any pending events, and waits for the event to complete.
        """
        self.loading.open()
        try:
            value = item.text()
            self.setText(value)
            self.popover_content.close()
            combine_form_context.update(mo_no=value)
            sync_event_emitter.emit(UserActionEvent.MO_NO_CHANGE.value, value)
        except Exception as e:
            logger.error(f"Error in on_mo_no_selected: {e}")
        finally:
            self.loading.close()

    # * Handle find manufacturing order from database

    @pyqtSlot(str)
    def handle_find_mo_no(self, q: str) -> None:
        try:
            query = QSqlQuery(DATA_SOURCE_ERP)
            query.prepare(
                f"""
                    SELECT TOP 5 mo_no
                    FROM (
                        SELECT DISTINCT mo_no, created
                        FROM wuerp_vnrd.dbo.ta_manufacturmst
                        WHERE mo_no LIKE :search
                    ) AS subquery
                    ORDER BY created DESC
                """,
            )
            query.bindValue(":search", f"%{q}%")
            query.exec()

            self.popover_menu_list.clear()
            while query.next():
                self.popover_menu_list.addItem(QListWidgetItem(query.value("mo_no")))
        except Exception as e:
            logger.error(e)
