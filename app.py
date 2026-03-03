import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

import db
from styles import APP_QSS
from ui_main import MainTab
from ui_settings import SettingsTab
from ui_config import ConfigTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prep Sticker Printer")
        self.resize(1240, 780)

        self.tabs = QTabWidget()

        self.main_tab = MainTab()
        self.settings_tab = SettingsTab(self.on_data_changed)
        self.config_tab = ConfigTab(self.on_data_changed)

        self.tabs.addTab(self.main_tab, "Main")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.config_tab, "Config")

        self.setCentralWidget(self.tabs)

    def on_data_changed(self):
        # When admin edits items/categories or config import runs, refresh main UI.
        self.main_tab.reload_categories()
        self.main_tab.refresh_tiles()
        self.settings_tab.refresh_admin_tables()


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    w = MainWindow()
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()