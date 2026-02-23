"""
Theme Manager Service
Manages theme switching and generates dynamic stylesheets
"""

from typing import Optional
from PyQt6.QtWidgets import QApplication
from themes.colors import Theme, get_theme_colors, get_color


class ThemeManager:
    """Singleton service for managing application themes"""

    _instance: Optional["ThemeManager"] = None
    _current_theme: Theme = Theme.DARK

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme manager"""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._current_theme = Theme.DARK

    @property
    def current_theme(self) -> Theme:
        """Get current active theme"""
        return self._current_theme

    def set_theme(self, theme: Theme) -> None:
        """
        Set application theme

        Args:
            theme: Theme to apply
        """
        self._current_theme = theme

    def get_color(self, color_name: str) -> str:
        """
        Get color from current theme

        Args:
            color_name: Color variable name (e.g., 'background', 'primary')

        Returns:
            Hex color code
        """
        return get_color(self._current_theme, color_name)

    def generate_stylesheet(self) -> str:
        """
        Generate QSS stylesheet for current theme

        Returns:
            Complete QSS stylesheet string
        """
        colors = get_theme_colors(self._current_theme)

        # Map semantic color names to usage
        bg = colors["background"]
        fg = colors["foreground"]
        card = colors["card"]
        card_fg = colors["card-foreground"]
        primary = colors["primary"]
        primary_fg = colors["primary-foreground"]
        primary_hover = colors["primary-hover"]
        secondary = colors["secondary"]
        secondary_fg = colors["secondary-foreground"]
        muted = colors["muted"]
        muted_fg = colors["muted-foreground"]
        border = colors["border"]
        input_border = colors["input"]
        ring = colors["ring"]
        hover = colors["hover"]
        hover_secondary = colors["hover-secondary"]
        destructive = colors["destructive"]
        destructive_fg = colors["destructive-foreground"]
        success = colors["success"]
        success_fg = colors["success-foreground"]
        disabled = colors["disabled"]
        disabled_fg = colors["disabled-foreground"]

        return f"""
*{{
   border-width: 1px;
   border-color: {border};
   font-family: "Inter";
   font-weight: Normal;
   font-size: 16px;
   color: {fg};
}}

QMainWindow, QDialog, #container{{
   color: {fg};
   background-color: {bg};
}}

QPushButton{{
   height: 36px;
   font-weight: 500;
   background-color: {primary};
   color: {primary_fg};
   border-radius: 4px;
   border: 1px solid {primary};
   spacing: 8px;
}}

QPushButton:hover{{
   background-color: {primary_hover};
   border-color: {primary_hover};
}}

QPushButton:disabled {{
   background-color: {disabled};
   color: {disabled_fg};
   border-color: {disabled};
}}

QPushButton:pressed{{
   background-color: {primary};
   border-color: {primary};
   opacity: 0.9;
}}

QLineEdit{{
   height: 36px;
   background-color: {card};
   color: {fg};
   border: 1px solid {input_border};
   border-radius: 4px;
   padding: 0px 8px;
   selection-background-color: {muted};
   selection-color: {fg};
}}

QLineEdit[valid="True"] {{
   border: 1px solid {success};
}}

QLineEdit[valid="False"] {{
   border: 1px solid {destructive};
}}

QLineEdit[echoMode="2"] {{
   lineedit-password-character: 8226;
}}

QComboBox{{
   height: 36px;
   background-color: {card};
   color: {fg};
   border: 1px solid {input_border};
   border-radius: 4px;
   padding-left: 8px;
}}

QComboBox:on{{
   border: 1px solid {ring};
}}

QComboBox QListView{{
   background-color: {card};
   border: 1px solid {input_border};
   border-radius: 4px;
   padding: 1.5px 3px;
}}

QComboBox QListView:disabled{{
  color: {disabled_fg};
}}

QListView::item{{
   padding: 2px 4px;
   height: 24px;
   border-radius: 4px;
}}

QListView::item:hover{{
   background-color: {hover};
}}

QListView::item:selected{{
   background-color: {muted};
   color: {fg};
   border: 0px;
   outline: 0px;
}}

QComboBox::drop-down{{
   border: 0px;
}}

QComboBox::down-arrow{{
   image: url(./assets/icons/chevron-down.svg);
   width: 14px;
   height: 14px;
   margin-right: 8px;
}}

QListWidget{{
   padding: 4px;
   background-color: {card};
   spacing: 2px;
}}

QListWidget::item{{
   padding: 4px;
}}

QTableWidget {{
   background-color: {card};
   border: 1px solid {border};
   gridline-color: {border};
   border-radius: 4px;
   padding: 1px;
}}

QTableWidget * {{
   background-color: transparent;
}}

QTableView::section {{
   padding: 0px 8px;
   font-weight: 600;
   background-color: transparent;
}}

QHeaderView::section {{
   padding: 0px 8px;
   font-weight: 600;
   background-color: {card};
}}

QTableWidget::item {{
   border: none;
   padding: 0px 8px;
   background-color: {card};
}}

QTableWidget::item:selected {{
   background-color: {muted};
   color: {fg};
}}

QTableWidget::item:hover {{
   background-color: {hover};
}}

QScrollBar:vertical {{
   background-color: {secondary};
   width: 8px;
   margin: 0px 0px 0px 0px;
}}

QScrollBar:horizontal {{
   border: 0px;
   background-color: {secondary};
   height: 8px;
   margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:vertical {{
   background-color: {muted};
   min-height: 20px;
   border-radius: 9999px;
}}

QScrollBar::handle:horizontal {{
   background-color: {muted};
   min-width: 20px;
   border-radius: 9999px;
}}

QScrollBar::add-line:vertical {{
   background: none;
   border: none;
   height: 14px;
   subcontrol-position: bottom;
   subcontrol-origin: margin;
}}

QScrollBar::sub-line:vertical {{
   background: none;
   border: none;
   height: 14px;
   subcontrol-position: bottom;
   subcontrol-origin: margin;
}}

QScrollBar::add-line:horizontal {{
   background: none;
   width: 14px;
   subcontrol-position: right;
   subcontrol-origin: margin;
}}

QScrollBar::sub-line:horizontal {{
   background: none;
   width: 14px;
   subcontrol-position: left;
   subcontrol-origin: margin;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
   background: none;
}}

QHeaderView::section{{
   font-weight: 500;
   height: 32px;
   background-color: {card};
   border: 0px;
   border-bottom: 1px solid {border};
   border-right: 1px solid {border};
}}

QMessageBox{{
   background-color: {card};
   color: {fg};
   border: 1px solid {border};
   border-radius: 4px;
   font-size: 14px;
}}

QMessageBox QPushButton{{
   height: 32px;
   width: 96px;
   font-size: 14px;
   font-weight: 500;
   background-color: {primary};
   color: {primary_fg};
   border: 1px solid {primary};
   border-radius: 4px;
   alternate-background-color: {secondary};
}}

QMessageBox QPushButton[text="&No"], QPushButton[text="&Cancel"]{{
   background: transparent;
   border: 1px solid {border};
   color: {fg};
}}

QMessageBox QPushButton[text="&No"]:hover, QPushButton[text="&Cancel"]:hover {{
   background-color: {hover};
}}

QMenuBar{{
   background-color: {card};
}}

QMenuBar::item {{
   color: {muted_fg};
   font-size: 12px;
}}

QMenuBar::item:selected {{
   color: {fg};
}}

QMenu{{
   background-color: {card};
   border-radius: 4px;
   font-size: 14px;
   border: 1px solid {border};
}}

QMenu::item{{
   border-radius: 2px;
   height: 28px;
}}

QMenu::item:selected{{
   background-color: {hover};
}}

QToolBar::handle {{
   image: url(./assets/icons/grip.svg);
   width: 18px;
   height: 18px;
   margin-bottom: 4px;
   margin-right: 4px;
}}

* QToolTip {{
   color: white;
   border: 1px solid {border};
   border-radius: 4px;
   font-size: 14px;
}}

QSlider::groove:horizontal {{
   height: 4px;
   background: {secondary};
   border-radius: 2px;
}}

QSlider::handle:horizontal {{
   width: 12px;
   height: 12px;
   background: {primary};
   border: 1px solid {ring};
   border-radius: 6px;
   margin: -4px 0;
}}

QSlider::sub-page:horizontal {{
   background: {primary};
   border-radius: 2px;
}}

QSlider::add-page:horizontal {{
   background: {card};
   border-radius: 2px;
}}

#toast-close-button, #toast-icon-widget {{
   background: transparent;
   border: none;
   height: auto;
   spacing: 0px;
}}

#toast-close-button:hover, #toast-icon-widget:hover {{
   background: transparent;
}}

#overlay{{
   background-color: {bg};
   background-opacity: 0.5
}}

#epc_reader_playground{{
   border: 1px solid {border};
   border-radius: 4px;
   background-color: {bg};
}}

#epc_counter_box {{
   background-color: {bg};
   border-radius: 4px;
}}

#reader_actions_group {{
   background-color: {bg};
   border-radius: 4px;
}}

#epc_reader_playground #epc_list{{
   border: 0px;
   border-radius: 4px;
   font-weight: 600;
}}

#epc_list_box #epc_list::item{{
   font-weight: 500;
}}

#pagination_group QPushButton, #epc_list_action_group QPushButton{{
   background: transparent;
   color: {fg};
}}

#epc_list_action_group QPushButton{{
   border: 0px;
}}

#pagination_group QPushButton {{
   border: 1px solid {border};
}}

#pagination_group QPushButton:hover, #epc_list_action_group QPushButton:hover{{
   background-color: {hover};
}}

#pagination_group QPushButton:disabled, #epc_list_action_group QPushButton:disabled{{
   color: {disabled_fg};
}}

#header_top_title, #playground_section_title{{
   font-family: "Inter";
   font-weight: 600;
   font-style: normal;
   font-size: 16px;
}}

#settings_dialog #fieldset_legend{{
   font-family: "Inter";
   font-weight: 600;
   font-style: normal;
   font-size: 14px;
   color: {muted_fg};
}}

#delete_button {{
   border: 1px solid {destructive};
   background-color: {destructive};
   color: {destructive_fg};
}}

#delete_button:hover {{
   background-color: {destructive};
   opacity: 0.8;
}}

#delete_button:disabled {{
   background-color: {destructive};
   opacity: 0.5;
   color: {primary_fg};
}}
"""

    def apply_theme(self, app: QApplication, theme: Theme) -> None:
        """
        Apply theme to QApplication

        Args:
            app: QApplication instance
            theme: Theme to apply
        """
        self.set_theme(theme)
        stylesheet = self.generate_stylesheet()
        app.setStyleSheet(stylesheet)


# Singleton instance
theme_manager = ThemeManager()
