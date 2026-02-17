from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from helpers.configuration import ConfigService, ConfigSection
from helpers.resolve_path import resolve_path
from widgets.switch import QToggle
from events import __event_emitter__, UserActionEvent
from i18n import I18nService, I18nContext
from helpers.disutils import strtobool
from themes.theme_manager import theme_manager
from themes.colors import Theme, get_color


class StatusBar(QToolBar, I18nContext):
    def __init__(self, parent=QMainWindow):
        super().__init__(parent)
        self.configurations = ConfigService.load_configs()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setFloatable(False)
        self.setObjectName("status_bar")
        self.setFixedHeight(50)

        # Database connection status
        # Primary database connection status
        self.db_primary_connection_layout = QHBoxLayout()
        self.db_primary_connection_layout.setContentsMargins(0, 0, 0, 0)
        self.db_primary_connection_layout.setSpacing(4)
        self.db_primary_connection_status = QWidget()
        self.db_primary_connection_status.setLayout(self.db_primary_connection_layout)
        self.db_primary_text = QLabel(text=self.configurations.get("DB_SERVER", "N/A"))
        database_icon = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/database.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        database_icon.setPixmap(pixmap)
        self.db_primary_connection_layout.addWidget(database_icon)
        self.db_primary_connection_layout.addWidget(self.db_primary_text)
        self.addWidget(self.db_primary_connection_status)

        # UHF Reader connection status
        self.reader_connection_layout = QHBoxLayout()
        self.reader_connection_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_connection_layout.setSpacing(4)
        self.reader_connection_status = QWidget()
        self.reader_connection_status.setLayout(self.reader_connection_layout)
        self.reader_icon = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/hard-drive.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.reader_icon.setPixmap(pixmap)
        self.reader_connection_text = QLabel(
            text=self.configurations.get("UHF_READER_TCP_IP", "N/A")
        )

        self.reader_connection_layout.addWidget(self.reader_icon)
        self.reader_connection_layout.addWidget(self.reader_connection_text)

        self.addWidget(self.reader_connection_status)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.addWidget(self.spacer)

        # Auto save toggle
        self.auto_save_form_layout = QHBoxLayout()
        self.auto_save_form_layout.setContentsMargins(0, 0, 0, 0)
        self.auto_save_form_layout.setSpacing(8)
        self.auto_save_form = QWidget()
        self.auto_save_form.setLayout(self.auto_save_form_layout)

        self.auto_save_label = QLabel()
        self.auto_save_toggle = QToggle()
        self.auto_save_toggle.setChecked(
            ConfigService.get_conf(
                section=ConfigSection.DATA.value,
                key="AUTO_SAVE",
                serializer=lambda value: strtobool(value),
            )
        )
        self.auto_save_toggle.checkStateChanged.connect(self.update_auto_save)
        self.auto_save_form_layout.addWidget(self.auto_save_label)
        self.auto_save_form_layout.addWidget(self.auto_save_toggle)

        self.addWidget(self.auto_save_form)
        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value, self.__translate__)
        __event_emitter__.on(
            UserActionEvent.THEME_CHANGE.value, self.update_theme_styles
        )

        # Apply initial theme styles after all widgets are created
        self.update_theme_styles()

    def __translate__(self):
        self.auto_save_label.setText(I18nService.t("labels.auto_save"))

    def update_theme_styles(self, theme: Theme = None):
        """Update status bar colors based on current theme"""
        if theme is None:
            theme = theme_manager.current_theme

        bg_color = get_color(theme, "card")
        border_color = get_color(theme, "border")
        self.setStyleSheet(
            f"""
            QToolBar{{
                padding:4px 8px;
                spacing: 24px;
                background-color: {bg_color};
                border-top: 1px solid {border_color};
            }}
        """
        )

        # Force update to apply new styles
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @pyqtSlot(Qt.CheckState)
    def update_auto_save(self, state: Qt.CheckState):
        is_auto_save: bool = state == Qt.CheckState.Checked
        ConfigService.set_conf(ConfigSection.DATA.value, "AUTO_SAVE", is_auto_save)
