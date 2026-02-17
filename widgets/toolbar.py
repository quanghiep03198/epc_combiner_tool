from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pyqttoast import *
from widgets.toaster import Toaster
from helpers.resolve_path import resolve_path
from contexts.auth_context import auth_context
from events import __event_emitter__, UserActionEvent
from i18n import __languages__, I18nService, I18nContext
from themes.colors import Theme, get_color
from themes.theme_manager import theme_manager
from helpers.configuration import ConfigService, ConfigSection

# from qtwidgets import AnimatedToggle


class AppToolBar(QToolBar, I18nContext):
    """
    Custom QMenuBar for the application
    """

    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setObjectName("toolbar")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        self.user_locale_layout = QHBoxLayout()
        self.user_locale_layout.setContentsMargins(4, 0, 0, 0)
        self.user_locale_layout.setSpacing(8)
        self.user_locale = QWidget()
        self.user_locale.setLayout(self.user_locale_layout)

        self.globe_icon = QLabel()

        pixmap = QPixmap(resolve_path("assets/icons/globe.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.globe_icon.setPixmap(pixmap)

        self.user_locale_text = QLabel()
        self.user_locale_layout.addWidget(self.globe_icon)
        self.user_locale_layout.addWidget(self.user_locale_text)
        self.addWidget(self.user_locale)

        # Theme selector
        self.theme_selector_layout = QHBoxLayout()
        self.theme_selector_layout.setContentsMargins(8, 0, 0, 0)
        self.theme_selector_layout.setSpacing(8)
        self.theme_selector_widget = QWidget()
        self.theme_selector_widget.setLayout(self.theme_selector_layout)

        self.theme_icon = QLabel()
        theme_pixmap = QPixmap(resolve_path("assets/icons/palette.svg")).scaled(
            20,
            20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.theme_icon.setPixmap(theme_pixmap)

        self.theme_selector = QComboBox()
        self.theme_selector.setFixedHeight(32)
        self.theme_selector.setFixedWidth(120)
        self.theme_selector.addItem(
            "", Theme.DARK.value
        )  # Placeholder text, will be updated by __translate__
        self.theme_selector.addItem(
            "", Theme.LIGHT.value
        )  # Placeholder text, will be updated by __translate__
        self.theme_selector.currentIndexChanged.connect(self.on_theme_selector_change)

        # Set current theme
        current_theme = ConfigService.get_conf(
            ConfigSection.UI.value, "theme", Theme.DARK.value
        )
        index = self.theme_selector.findData(current_theme)
        if index >= 0:
            self.theme_selector.setCurrentIndex(index)

        self.theme_selector_layout.addWidget(self.theme_icon)
        self.theme_selector_layout.addWidget(self.theme_selector)
        self.addWidget(self.theme_selector_widget)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.addWidget(self.spacer)

        # region Users actions
        self.factory_icon = QLabel()

        pixmap = QPixmap(resolve_path("assets/icons/factory.svg")).scaled(
            24,
            24,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.factory_icon.setPixmap(pixmap)

        self.user_factory_layout = QHBoxLayout()
        self.user_factory_layout.setSpacing(4)
        self.user_factory = QFrame()
        self.user_factory.setLayout(self.user_factory_layout)
        self.user_factory.setLayout(self.user_factory_layout)

        self.user_factory_text = QLabel("N/A")
        self.user_factory_layout.addWidget(self.factory_icon)
        self.user_factory_layout.addWidget(self.user_factory_text)

        self.addWidget(self.user_factory)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setFixedHeight(24)
        self.addWidget(self.separator)

        self.user_info_layout = QHBoxLayout()
        self.user_info_layout.setSpacing(4)
        self.user_info_layout.setContentsMargins(0, 0, 0, 0)
        self.user_info = QFrame()
        self.user_info.setLayout(self.user_info_layout)

        self.user_icon = QLabel()
        pixmap = QPixmap(resolve_path("assets/icons/user.svg")).scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.user_icon.setPixmap(pixmap)
        self.user_info_layout.addWidget(self.user_icon)

        self.user_display_name_text = QLabel()
        self.user_info_layout.addWidget(self.user_display_name_text)

        self.addWidget(self.user_info)

        logout_icon = QIcon()
        pixmap = QPixmap(resolve_path("assets/icons/log-out.svg"))
        logout_icon.addPixmap(
            pixmap.scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.logout_action = QAction(icon=logout_icon, text="Logout", parent=self)
        self.logout_action.setObjectName("logout_act")
        self.logout_action.triggered.connect(self.handle_logout)

        __event_emitter__.on(UserActionEvent.LANGUAGE_CHANGE.value)(self.__translate__)
        __event_emitter__.on(UserActionEvent.AUTH_STATE_CHANGE.value)(
            self.on_auth_state_change
        )
        __event_emitter__.on(UserActionEvent.THEME_CHANGE.value)(
            self.update_theme_styles
        )

        # Apply initial theme styles after all widgets are created
        self.update_theme_styles()

    def __translate__(self):
        curr_lang = I18nService.get_i18n_context()
        self.user_locale_text.setText(curr_lang["label"])
        self.logout_action.setToolTip(I18nService.t("actions.logout"))
        if not auth_context["is_authenticated"]:
            self.user_display_name_text.setText(I18nService.t("actions.login"))

        # Update theme selector items
        current_index = self.theme_selector.currentIndex()
        self.theme_selector.setItemText(0, I18nService.t("themes.dark"))
        self.theme_selector.setItemText(1, I18nService.t("themes.light"))

    def on_auth_state_change(self, data):
        if data["is_authenticated"]:
            self.user_factory_text.setText(data["factory_name"])
            self.user_display_name_text.setText(data["employee_name"])
            self.addAction(self.logout_action)
        else:
            self.user_factory_text.setText("N/A")
            self.user_display_name_text.setText(I18nService.t("login"))
            self.removeAction(self.logout_action)

    def handle_logout(self):
        auth_context.update(is_authenticated=False)
        auth_context.update(employee_code=None)
        auth_context.update(employee_name=None)
        auth_context.update(factory_code=None)
        auth_context.update(factory_name=None)
        toast = Toaster(
            parent=self.root,
            title=I18nService.t("notification.logout_success_title"),
            text=I18nService.t("notification.logout_success_text"),
            preset=ToastPreset.SUCCESS_DARK,
        )
        toast.show()
        __event_emitter__.emit(UserActionEvent.AUTH_STATE_CHANGE.value, auth_context)

    def on_theme_selector_change(self, index: int):
        """Handle theme selector change"""
        theme_value = self.theme_selector.itemData(index)
        try:
            theme = Theme(theme_value)
            __event_emitter__.emit(UserActionEvent.THEME_CHANGE.value, theme)
        except ValueError:
            pass

    def update_theme_styles(self, theme: Theme = None):
        """Update toolbar colors based on current theme"""
        if theme is None:
            theme = theme_manager.current_theme

        toolbar_bg = get_color(theme, "card")
        separator_bg = get_color(theme, "secondary")
        border_color = get_color(theme, "border")

        self.setStyleSheet(
            f"""
            QToolBar{{
                padding-left: 8px;
                padding-right: 8px;
                spacing: 8px;
                background-color: {toolbar_bg};
                border-bottom: 1px solid {border_color};
            }}
        """
        )
        self.separator.setStyleSheet(f"background-color: {separator_bg};")

        # Force update to apply new styles
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
