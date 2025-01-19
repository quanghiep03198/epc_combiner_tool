from helpers.logger import logger
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSql import QSqlQuery
from contexts.combine_form_context import combine_form_context
from contexts.auth_context import auth_context
from database import DATA_SOURCE_ERP
from events import __event_emitter__, UserActionEvent
from i18n import I18nService
from helpers.resolve_path import resolve_path


class OrderAutoCompleteWidget(QPushButton):
    """
    Custom autocomplete for searching manufacturing order
    """

    __is_closing: bool = False

    def __init__(self, root):
        super().__init__(root.container)

        """
        A flag that indicates whether the popover content is closing or not.
        """

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            "height: 36px; background-color: #171717; border: 1px solid #404040; color: #fafafa; text-align: left; padding: 2px 8px; font-weight: 400;"
        )

        chevron_icon = QIcon()
        chevron_icon.addPixmap(
            QPixmap(resolve_path("assets/icons/chevrons-up-down.svg")),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.setIcon(chevron_icon)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setIconSize(QSize(14, 14))
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self.handle_toggle_open)
        self.popover_content = QDialog(self)
        self.popover_content.setGraphicsEffect(None)
        self.popover_content.setStyleSheet(
            "border: 1px solid #404040; border-radius: 4px; background-color: #171717"
        )
        self.popover_content.finished.connect(lambda: self.on_popover_content_close())
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

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            lambda _: self.handle_find_mo_no("")
        )

    def __translate__(self):
        if combine_form_context["mo_no"] is None:
            self.setText(I18nService.t("placeholders.mo_no_placeholder"))
        self.popover_input.setPlaceholderText(
            I18nService.t("placeholders.search_placeholder")
        )

    @pyqtSlot(bool)
    def handle_toggle_open(self, checked_state: bool) -> None:
        """
        Handles the event when the widget is opened.

        This method calculates the geometry of the button and sets the position
        and size of the popover content relative to the button's position. It then
        displays the popover content. If an exception occurs during this process,
        it logs the error.
        """
        if self.__is_closing:
            self.__is_closing = False
            return

        button_geometry = self.geometry()
        global_position = self.mapToGlobal(button_geometry.bottomLeft())
        animation = QPropertyAnimation(self.popover_content, b"geometry")
        animation.setDuration(150)

        if checked_state:
            self.popover_input.setFocus()
            animation.setStartValue(
                QRect(
                    global_position.x() - button_geometry.x(),
                    global_position.y() - 24,
                    button_geometry.width(),
                    0,
                )
            )
            animation.setEndValue(
                QRect(
                    global_position.x() - button_geometry.x(),
                    global_position.y() - 12,
                    button_geometry.width(),
                    250,
                )
            )
            animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            animation.start()

            self.popover_content.exec()

        else:
            self.__is_closing = True
            animation.setStartValue(
                QRect(
                    global_position.x() - button_geometry.x(),
                    global_position.y(),
                    button_geometry.width(),
                    250,
                )
            )
            animation.setEndValue(
                QRect(
                    global_position.x() - button_geometry.x(),
                    global_position.y(),
                    button_geometry.width(),
                    0,
                )
            )
            animation.setEasingCurve(QEasingCurve.Type.InQuad)
            animation.setEasingCurve(QEasingCurve.Type.InQuad)
            animation.start()

    @pyqtSlot()
    def on_popover_content_close(self):
        self.__is_closing = True
        self.setChecked(False)

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
        """
        value = item.text()
        self.setText(value)
        self.popover_content.close()
        combine_form_context.update(mo_no=value)
        __event_emitter__.emit(UserActionEvent.MO_NO_CHANGE.value, value)

    # * Handle find manufacturing order from database

    @pyqtSlot(str)
    def handle_find_mo_no(self, q: str) -> None:
        try:
            query = QSqlQuery(DATA_SOURCE_ERP)
            query.prepare(
                f"""--sql
                    SELECT TOP 5 mo_no
                    FROM (
                        SELECT DISTINCT mo_no, created
                        FROM wuerp_vnrd.dbo.ta_manufacturmst
                        WHERE mo_no LIKE :search
                        AND cofactory_code = :factory_code
                    ) AS subquery
                    ORDER BY created DESC
                """,
            )
            query.bindValue(":search", f"%{q}%")
            query.bindValue(":factory_code", auth_context.get("factory_code"))
            query.exec()

            self.popover_menu_list.clear()
            while query.next():
                self.popover_menu_list.addItem(QListWidgetItem(query.value("mo_no")))
        except Exception as e:
            logger.error(e)
