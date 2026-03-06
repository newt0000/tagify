import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QResizeEvent
from PySide6.QtCore import QProcess, QTimer

import db
import license_gate
from styles import APP_QSS
from ui_main import MainTab
from ui_settings import SettingsTab
from ui_config import ConfigTab
from license_gate import LicenseBlockOverlay


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

        self._license_overlay = None
        self._agent_process = None
        self._license_timer = QTimer(self)
        self._license_timer.timeout.connect(self.poll_license_status)
        self._license_timer.start(10000)  # every 10 seconds

    def poll_license_status(self):
        if self._license_overlay is None:
            self._license_overlay = LicenseBlockOverlay(self)
            self._license_overlay.unlocked.connect(self.on_license_unlocked)

        self._license_overlay.refresh_status()

        # if invalid, make sure blocker is visible
        if self._license_overlay.isHidden():
            return

        self._license_overlay.setGeometry(self.rect())
        self._license_overlay.show()
        self._license_overlay.raise_()

    def on_data_changed(self):
        self.main_tab.reload_categories()
        self.main_tab.refresh_tiles()
        self.settings_tab.refresh_admin_tables()

    def show_license_block(self):
        if self._license_overlay is None:
            self._license_overlay = LicenseBlockOverlay(self)
            self._license_overlay.unlocked.connect(self.on_license_unlocked)
        self._license_overlay.setGeometry(self.rect())
        self._license_overlay.show()
        self._license_overlay.raise_()
        QTimer.singleShot(200, self._license_overlay.refresh_status)

    def on_license_unlocked(self):
        if self._license_overlay is not None:
            self._license_overlay.hide()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._license_overlay is not None and self._license_overlay.isVisible():
            self._license_overlay.setGeometry(self.rect())

    def start_agent(self):
        """
        Starts the background telemetry agent if tagify_agent.py exists.
        Uses the same Python interpreter that launched Tagify.
        """
        agent_path = Path(__file__).resolve().parent / "tagify_agent.py"
        if not agent_path.exists():
            print("[app] tagify_agent.py not found, skipping agent launch")
            return

        self._agent_process = QProcess(self)
        self._agent_process.setProgram(sys.executable)
        self._agent_process.setArguments([str(agent_path)])
        self._agent_process.start()

        if not self._agent_process.waitForStarted(3000):
            print("[app] failed to start telemetry agent")
        else:
            print("[app] telemetry agent started")


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    w = MainWindow()
    w.start_agent()
    w.show()
    w.show_license_block()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()