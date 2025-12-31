from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QPushButton
from decorators.debounce import pyqtDebounce
from contexts.combine_form_context import combine_form_context
from events import __event_emitter__, UserActionEvent
from i18n import I18nContext, I18nService


class RefreshButton(QPushButton, I18nContext):
    def __init__(self, parent=None):
        super().__init__("Refetch", parent)
        self.setObjectName("refetch_button")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedWidth(120)
        self.setEnabled(False)
        self.clicked.connect(self.on_click)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.MO_NO_CHANGE.value)(self.on_mo_no_change)
        __event_emitter__.on(UserActionEvent.LOADING_STATE_CHANGE.value)(
            lambda state: self.setEnabled(not state)
        )

    def __translate__(self):
        self.setText(I18nService.t("actions.refetch"))

    @pyqtDebounce(wait=500, immediate=True)
    @pyqtSlot()
    def on_click(self):
        if combine_form_context.get("mo_no") is not None:
            __event_emitter__.emit(
                UserActionEvent.MO_NO_CHANGE.value,
                {"mo_no": combine_form_context.get("mo_no")},
            )

    def on_mo_no_change(self, mo_no: str):
        self.setEnabled(mo_no is not None and mo_no != "")
