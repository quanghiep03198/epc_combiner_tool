from PyQt6.QtWidgets import *
from widgets.settings_dialog import *


class AppMenuBar(QMenuBar):
    """
    Custom QMenuBar for the application
    """

    def __init__(self, root):
        super().__init__()

        self.root = root

        self.setObjectName("menubar")

        self.file_menu = QMenu(self)
        self.file_menu.setObjectName("file_menu")
        self.view_menu = QMenu(self)
        self.view_menu.setObjectName("view_menu")
        self.setting_menu = QMenu(self)
        self.setting_menu.setObjectName("setting_menu")
        self.help_menu = QMenu(self)
        self.help_menu.setObjectName("help_menu")

        self.addAction(self.file_menu.menuAction())
        self.addAction(self.view_menu.menuAction())
        self.addAction(self.setting_menu.menuAction())
        self.addAction(self.help_menu.menuAction())

        self.file_menu.setTitle("File")
        self.view_menu.setTitle("View")
        self.setting_menu.setTitle("Setting")
        self.help_menu.setTitle("Help")

        self.connection_setting = self.setting_menu.addAction("Connection")

        self.connection_setting.triggered.connect(self.show_settings_window)

    def show_settings_window(self):
        self.setting_window = AppSettingsDialog(self.root)
