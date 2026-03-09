from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTextEdit, QMessageBox, QGridLayout, QSizePolicy, QTabWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QLineEdit, QComboBox, QSpinBox, QHeaderView
)

import db
from config_source import get_active_config
from label_print import print_label_direct
from printer_backend import get_printer_state, list_printers


APP_NAME = "Tagify"


def appdata_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / APP_NAME


def local_config_path() -> Path:
    return appdata_dir() / "agent_config.json"


def state_path() -> Path:
    return appdata_dir() / "agent_state.json"


def runtime_files() -> list[Path]:
    base = appdata_dir()
    files = [
        local_config_path(),
        state_path(),
    ]
    return [p for p in files if p.exists()]


def safe_open_path(path: Path):
    if not path.exists():
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


class DeveloperTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self._config = {}
        self._source_name = ""
        self._source_path = None
        self._active_db_path = self._guess_db_path()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("Card")
        header_l = QVBoxLayout(header)
        header_l.setContentsMargins(14, 14, 14, 14)
        header_l.setSpacing(6)

        title = QLabel("Developer Tools")
        title.setObjectName("Title")
        subtitle = QLabel("Advanced diagnostics, support utilities, and recovery actions")
        subtitle.setObjectName("Muted")

        header_l.addWidget(title)
        header_l.addWidget(subtitle)
        root.addWidget(header)

        info = QFrame()
        info.setObjectName("Card")
        info_l = QVBoxLayout(info)
        info_l.setContentsMargins(14, 14, 14, 14)
        info_l.setSpacing(10)

        self.lbl_source = QLabel("Active config source: —")
        self.lbl_source.setObjectName("Muted")

        self.lbl_path = QLabel("Config path: —")
        self.lbl_path.setObjectName("Muted")
        self.lbl_path.setWordWrap(True)

        self.lbl_dev = QLabel("Developer mode: —")
        self.lbl_dev.setObjectName("Muted")

        self.lbl_db = QLabel("Detected database: —")
        self.lbl_db.setObjectName("Muted")
        self.lbl_db.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_reload = QPushButton("Reload Config")
        self.btn_reload.clicked.connect(self.reload_config)

        self.btn_open_config = QPushButton("Open Active Config Folder")
        self.btn_open_config.clicked.connect(self.open_active_config_folder)

        self.btn_open_appdata = QPushButton("Open Local AppData Folder")
        self.btn_open_appdata.clicked.connect(self.open_appdata)

        self.btn_open_project = QPushButton("Open Project Folder")
        self.btn_open_project.clicked.connect(self.open_project_folder)

        btn_row.addWidget(self.btn_reload)
        btn_row.addWidget(self.btn_open_config)
        btn_row.addWidget(self.btn_open_appdata)
        btn_row.addWidget(self.btn_open_project)

        info_l.addWidget(self.lbl_source)
        info_l.addWidget(self.lbl_path)
        info_l.addWidget(self.lbl_dev)
        info_l.addWidget(self.lbl_db)
        info_l.addLayout(btn_row)
        root.addWidget(info)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.tab_overview = QWidget()
        self.tab_db = QWidget()
        self.tab_print = QWidget()
        self.tab_sync = QWidget()
        self.tab_cache = QWidget()
        self.tab_printer = QWidget()
        self.tab_bundle = QWidget()

        self.tabs.addTab(self.tab_overview, "Overview")
        self.tabs.addTab(self.tab_db, "Database Viewer")
        self.tabs.addTab(self.tab_print, "Label Test")
        self.tabs.addTab(self.tab_sync, "Sync Tools")
        self.tabs.addTab(self.tab_cache, "Cache / Reset")
        self.tabs.addTab(self.tab_printer, "Printer Diagnostics")
        self.tabs.addTab(self.tab_bundle, "Support Bundle")

        self._build_overview_tab()
        self._build_db_tab()
        self._build_print_tab()
        self._build_sync_tab()
        self._build_cache_tab()
        self._build_printer_tab()
        self._build_bundle_tab()

        self.reload_config()

    # ---------- builders ----------

    def _build_overview_tab(self):
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        tools = QFrame()
        tools.setObjectName("Card")
        tools_l = QVBoxLayout(tools)
        tools_l.setContentsMargins(14, 14, 14, 14)
        tools_l.setSpacing(10)

        tools_title = QLabel("Support Actions")
        tools_title.setStyleSheet("font-weight: 600;")
        tools_l.addWidget(tools_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.btn_license_refresh = QPushButton("Force License Refresh")
        self.btn_license_refresh.clicked.connect(self.force_license_refresh)

        self.btn_printer_refresh = QPushButton("Force Printer Refresh")
        self.btn_printer_refresh.clicked.connect(self.force_printer_refresh)

        self.btn_restart_agent = QPushButton("Restart Agent")
        self.btn_restart_agent.clicked.connect(self.restart_agent)

        self.btn_clear_local_cfg = QPushButton("Clear Local Fallback Config")
        self.btn_clear_local_cfg.clicked.connect(self.clear_local_fallback)

        self.btn_show_state = QPushButton("Show State File")
        self.btn_show_state.clicked.connect(self.show_state_file)

        self.btn_copy_summary = QPushButton("Copy Debug Summary")
        self.btn_copy_summary.clicked.connect(self.copy_debug_summary)

        grid.addWidget(self.btn_license_refresh, 0, 0)
        grid.addWidget(self.btn_printer_refresh, 0, 1)
        grid.addWidget(self.btn_restart_agent, 1, 0)
        grid.addWidget(self.btn_clear_local_cfg, 1, 1)
        grid.addWidget(self.btn_show_state, 2, 0)
        grid.addWidget(self.btn_copy_summary, 2, 1)

        tools_l.addLayout(grid)
        layout.addWidget(tools)

        viewer = QFrame()
        viewer.setObjectName("Card")
        viewer_l = QVBoxLayout(viewer)
        viewer_l.setContentsMargins(14, 14, 14, 14)
        viewer_l.setSpacing(10)

        viewer_title = QLabel("Active Config JSON")
        viewer_title.setStyleSheet("font-weight: 600;")
        viewer_l.addWidget(viewer_title)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMinimumHeight(260)
        self.config_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        viewer_l.addWidget(self.config_text)
        layout.addWidget(viewer, 1)

    def _build_db_tab(self):
        layout = QVBoxLayout(self.tab_db)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        top = QFrame()
        top.setObjectName("Card")
        top_l = QVBoxLayout(top)
        top_l.setContentsMargins(14, 14, 14, 14)
        top_l.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.db_path_input = QLineEdit(str(self._active_db_path) if self._active_db_path else "")
        self.db_path_input.setPlaceholderText("Path to sqlite database")

        self.btn_db_browse = QPushButton("Browse")
        self.btn_db_browse.clicked.connect(self.browse_db)

        self.btn_db_refresh = QPushButton("Reload Tables")
        self.btn_db_refresh.clicked.connect(self.refresh_db_tables)

        self.db_table_select = QComboBox()
        self.db_table_select.currentIndexChanged.connect(self.load_selected_db_table)

        row.addWidget(self.db_path_input, 1)
        row.addWidget(self.btn_db_browse)
        row.addWidget(self.btn_db_refresh)
        row.addWidget(self.db_table_select)

        top_l.addLayout(row)
        layout.addWidget(top)

        self.db_table = QTableWidget(0, 0)
        self.db_table.setObjectName("DataTable")
        self.db_table.setAlternatingRowColors(True)
        self.db_table.verticalHeader().setVisible(False)
        self.db_table.horizontalHeader().setStretchLastSection(True)
        self.db_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.db_table, 1)

    def _build_print_tab(self):
        layout = QVBoxLayout(self.tab_print)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        form1 = QHBoxLayout()
        form1.setSpacing(10)

        self.test_item_name = QLineEdit()
        self.test_item_name.setPlaceholderText("Label item name")
        self.test_item_name.setText("TEST LABEL")

        self.test_expire_days = QSpinBox()
        self.test_expire_days.setRange(0, 3650)
        self.test_expire_days.setValue(3)
        self.test_expire_days.setButtonSymbols(QSpinBox.NoButtons)

        self.test_copies = QSpinBox()
        self.test_copies.setRange(1, 99)
        self.test_copies.setValue(1)
        self.test_copies.setButtonSymbols(QSpinBox.NoButtons)

        form1.addWidget(QLabel("Item"))
        form1.addWidget(self.test_item_name, 1)
        form1.addWidget(QLabel("Expire Days"))
        form1.addWidget(self.test_expire_days)
        form1.addWidget(QLabel("Copies"))
        form1.addWidget(self.test_copies)

        form2 = QHBoxLayout()
        form2.setSpacing(10)

        self.test_printer_select = QComboBox()
        self.refresh_printer_list_for_test()

        self.btn_test_print = QPushButton("Send Test Print")
        self.btn_test_print.clicked.connect(self.send_test_print)

        form2.addWidget(QLabel("Printer"))
        form2.addWidget(self.test_printer_select, 1)
        form2.addWidget(self.btn_test_print)

        self.print_result = QTextEdit()
        self.print_result.setReadOnly(True)
        self.print_result.setMinimumHeight(180)

        card_l.addLayout(form1)
        card_l.addLayout(form2)
        card_l.addWidget(self.print_result)
        layout.addWidget(card)

    def _build_sync_tab(self):
        layout = QVBoxLayout(self.tab_sync)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_sync_location = QPushButton("Force Sync Location From Server")
        self.btn_sync_location.clicked.connect(self.force_sync_location)

        self.btn_refresh_header = QPushButton("Refresh Main Header")
        self.btn_refresh_header.clicked.connect(self.refresh_main_header)

        self.btn_refresh_license = QPushButton("Refresh License State")
        self.btn_refresh_license.clicked.connect(self.force_license_refresh)

        row.addWidget(self.btn_sync_location)
        row.addWidget(self.btn_refresh_header)
        row.addWidget(self.btn_refresh_license)

        self.sync_result = QTextEdit()
        self.sync_result.setReadOnly(True)
        self.sync_result.setMinimumHeight(220)

        card_l.addLayout(row)
        card_l.addWidget(self.sync_result)
        layout.addWidget(card)

    def _build_cache_tab(self):
        layout = QVBoxLayout(self.tab_cache)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        row = QGridLayout()
        row.setSpacing(10)

        self.btn_delete_local_config = QPushButton("Delete Local Config")
        self.btn_delete_local_config.clicked.connect(self.clear_local_fallback)

        self.btn_delete_state = QPushButton("Delete State File")
        self.btn_delete_state.clicked.connect(self.delete_state_file)

        self.btn_open_cache_dir = QPushButton("Open AppData Cache Folder")
        self.btn_open_cache_dir.clicked.connect(self.open_appdata)

        self.btn_reload_everything = QPushButton("Reload Config + Header + License")
        self.btn_reload_everything.clicked.connect(self.reload_everything)

        row.addWidget(self.btn_delete_local_config, 0, 0)
        row.addWidget(self.btn_delete_state, 0, 1)
        row.addWidget(self.btn_open_cache_dir, 1, 0)
        row.addWidget(self.btn_reload_everything, 1, 1)

        self.cache_result = QTextEdit()
        self.cache_result.setReadOnly(True)
        self.cache_result.setMinimumHeight(180)

        card_l.addLayout(row)
        card_l.addWidget(self.cache_result)
        layout.addWidget(card)

    def _build_printer_tab(self):
        layout = QVBoxLayout(self.tab_printer)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.diag_printer_select = QComboBox()
        self.refresh_printer_diag_list()

        self.btn_diag_refresh = QPushButton("Refresh Printer List")
        self.btn_diag_refresh.clicked.connect(self.refresh_printer_diag_list)

        self.btn_run_diag = QPushButton("Run Diagnostics")
        self.btn_run_diag.clicked.connect(self.run_printer_diagnostics)

        top.addWidget(QLabel("Printer"))
        top.addWidget(self.diag_printer_select, 1)
        top.addWidget(self.btn_diag_refresh)
        top.addWidget(self.btn_run_diag)

        self.printer_diag_output = QTextEdit()
        self.printer_diag_output.setReadOnly(True)
        self.printer_diag_output.setMinimumHeight(240)

        card_l.addLayout(top)
        card_l.addWidget(self.printer_diag_output)
        layout.addWidget(card)

    def _build_bundle_tab(self):
        layout = QVBoxLayout(self.tab_bundle)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_export_bundle = QPushButton("Export Support Bundle")
        self.btn_export_bundle.clicked.connect(self.export_support_bundle)

        self.btn_open_bundle_source = QPushButton("Open AppData Source")
        self.btn_open_bundle_source.clicked.connect(self.open_appdata)

        row.addWidget(self.btn_export_bundle)
        row.addWidget(self.btn_open_bundle_source)

        self.bundle_output = QTextEdit()
        self.bundle_output.setReadOnly(True)
        self.bundle_output.setMinimumHeight(220)

        card_l.addLayout(row)
        card_l.addWidget(self.bundle_output)
        layout.addWidget(card)

    # ---------- general helpers ----------

    def reload_config(self):
        try:
            config, source_name, source_path = get_active_config()
            self._config = config
            self._source_name = source_name
            self._source_path = Path(source_path)

            self.lbl_source.setText(f"Active config source: {source_name.upper()}")
            self.lbl_path.setText(f"Config path: {self._source_path}")
            self.lbl_dev.setText(f"Developer mode: {bool(config.get('developer', False))}")
            self.lbl_db.setText(f"Detected database: {self._active_db_path if self._active_db_path else '(not found)'}")

            pretty = json.dumps(config, indent=2)
            self.config_text.setPlainText(pretty)

            if hasattr(self, "db_path_input"):
                self.db_path_input.setText(str(self._active_db_path) if self._active_db_path else "")
                self.refresh_db_tables()
        except Exception as e:
            QMessageBox.critical(self, "Reload failed", str(e))

    def open_path(self, path: Path):
        try:
            safe_open_path(path)
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))

    def open_active_config_folder(self):
        self.reload_config()
        self.open_path(self._source_path.parent)

    def open_appdata(self):
        self.open_path(appdata_dir())

    def open_project_folder(self):
        self.open_path(Path(__file__).resolve().parent)

    # ---------- overview actions ----------

    def force_license_refresh(self):
        try:
            if self.main_window and getattr(self.main_window, "_license_overlay", None) is not None:
                self.main_window._license_overlay.refresh_status()
                QMessageBox.information(self, "Done", "License status refresh triggered.")
            elif self.main_window and hasattr(self.main_window, "show_license_block"):
                self.main_window.show_license_block()
                QMessageBox.information(self, "Done", "License gate refresh triggered.")
            else:
                QMessageBox.warning(self, "Unavailable", "License overlay is not available.")
        except Exception as e:
            QMessageBox.warning(self, "Refresh failed", str(e))

    def force_printer_refresh(self):
        try:
            if self.main_window and hasattr(self.main_window, "main_tab"):
                self.main_window.main_tab.refresh_printer_status()
                QMessageBox.information(self, "Done", "Printer status refresh triggered.")
            else:
                QMessageBox.warning(self, "Unavailable", "Main tab is not available.")
        except Exception as e:
            QMessageBox.warning(self, "Refresh failed", str(e))

    def restart_agent(self):
        try:
            if self.main_window and hasattr(self.main_window, "start_agent"):
                proc = getattr(self.main_window, "_agent_process", None)
                if proc is not None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                self.main_window.start_agent()
                QMessageBox.information(self, "Done", "Telemetry agent restart requested.")
            else:
                QMessageBox.warning(self, "Unavailable", "Agent restart hook is not available.")
        except Exception as e:
            QMessageBox.warning(self, "Restart failed", str(e))

    def clear_local_fallback(self):
        path = local_config_path()
        if not path.exists():
            QMessageBox.information(self, "Nothing to clear", "Local fallback config does not exist.")
            return

        if QMessageBox.question(
            self,
            "Clear local fallback config",
            f"Delete local fallback config?\n\n{path}"
        ) != QMessageBox.Yes:
            return

        try:
            path.unlink()
            QMessageBox.information(self, "Deleted", "Local fallback config deleted.")
            self.cache_result_append(f"Deleted local fallback config: {path}")
            self.reload_config()
        except Exception as e:
            QMessageBox.warning(self, "Delete failed", str(e))

    def show_state_file(self):
        p = state_path()
        if not p.exists():
            QMessageBox.information(self, "State file", "No state file exists yet.")
            return

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            QMessageBox.information(self, "State file", json.dumps(data, indent=2))
        except Exception as e:
            QMessageBox.warning(self, "Read failed", str(e))

    def copy_debug_summary(self):
        self.reload_config()
        summary = (
            f"Source: {self._source_name}\n"
            f"Config path: {self._source_path}\n"
            f"Developer: {self._config.get('developer', False)}\n"
            f"Location: {self._config.get('location_name', '')}\n"
            f"Code: {self._config.get('location_code', '')}\n"
            f"App Version: {self._config.get('app_version', '')}\n"
            f"Printer: {self._config.get('printer_name', '')}\n"
            f"Enabled: {self._config.get('enabled', True)}\n"
            f"Database: {self._active_db_path if self._active_db_path else '(not found)'}"
        )
        QApplication.clipboard().setText(summary)
        QMessageBox.information(self, "Copied", "Debug summary copied to clipboard.")

    # ---------- database viewer ----------

    def _guess_db_path(self) -> Path | None:
        candidates = [
            Path(__file__).resolve().parent / "tagify.db",
            Path(__file__).resolve().parent / "database.db",
            Path(__file__).resolve().parent / "prep_sticker.db",
            appdata_dir() / "tagify.db",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def browse_db(self):
        p, _ = QFileDialog.getOpenFileName(self, "Choose SQLite DB", "", "SQLite DB (*.db *.sqlite *.sqlite3);;All Files (*.*)")
        if p:
            self._active_db_path = Path(p)
            self.db_path_input.setText(p)
            self.refresh_db_tables()

    def refresh_db_tables(self):
        self.db_table_select.blockSignals(True)
        self.db_table_select.clear()

        db_path_text = self.db_path_input.text().strip()
        if not db_path_text:
            self.db_table_select.blockSignals(False)
            return

        db_path = Path(db_path_text)
        if not db_path.exists():
            self.db_table_select.blockSignals(False)
            return

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [r[0] for r in cur.fetchall()]
            conn.close()

            for t in tables:
                self.db_table_select.addItem(t)

            self.db_table_select.blockSignals(False)
            if tables:
                self.load_selected_db_table()
        except Exception as e:
            self.db_table_select.blockSignals(False)
            QMessageBox.warning(self, "DB load failed", str(e))

    def load_selected_db_table(self):
        table_name = self.db_table_select.currentText().strip()
        db_path_text = self.db_path_input.text().strip()

        if not table_name or not db_path_text:
            return

        try:
            conn = sqlite3.connect(db_path_text)
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM [{table_name}] LIMIT 500")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            conn.close()

            self.db_table.setColumnCount(len(cols))
            self.db_table.setHorizontalHeaderLabels(cols)
            self.db_table.setRowCount(len(rows))

            for r_idx, row in enumerate(rows):
                for c_idx, value in enumerate(row):
                    self.db_table.setItem(r_idx, c_idx, QTableWidgetItem("" if value is None else str(value)))
        except Exception as e:
            QMessageBox.warning(self, "Table load failed", str(e))

    # ---------- label print test ----------

    def refresh_printer_list_for_test(self):
        self.test_printer_select.clear()
        try:
            for p in list_printers():
                self.test_printer_select.addItem(p)
        except Exception:
            pass

        try:
            con = db.connect()
            selected = db.get_setting(con, "printer_name") or ""
            con.close()
            idx = self.test_printer_select.findText(selected)
            if idx >= 0:
                self.test_printer_select.setCurrentIndex(idx)
        except Exception:
            pass

    def send_test_print(self):
        printer_name = self.test_printer_select.currentText().strip()
        item_name = self.test_item_name.text().strip() or "TEST LABEL"
        expire_days = int(self.test_expire_days.value())
        copies = int(self.test_copies.value())

        prepped = date.today()
        expires = prepped + timedelta(days=expire_days)

        try:
            result = print_label_direct(
                printer_name=printer_name,
                item_name=item_name,
                prepped=prepped,
                expires=expires,
                copies=copies,
            )
            self.print_result.setPlainText(
                f"Printer: {printer_name}\n"
                f"Item: {item_name}\n"
                f"Prepped: {prepped}\n"
                f"Expires: {expires}\n"
                f"Copies: {copies}\n\n"
                f"Result: {'OK' if result.ok else 'FAILED'}\n"
                f"Message: {result.message}"
            )
        except Exception as e:
            self.print_result.setPlainText(f"Print test failed:\n{e}")

    # ---------- sync tools ----------

    def force_sync_location(self):
        try:
            import requests

            config, source_name, source_path = get_active_config()
            server_url = str(config.get("server_url", "")).rstrip("/")
            api_key = str(config.get("api_key", "")).strip()

            if not server_url or not api_key:
                self.sync_result.setPlainText("Missing server_url or api_key in active config.")
                return

            headers = {"X-API-Key": api_key}
            resp = requests.get(f"{server_url}/api/key-info", headers=headers, timeout=10)

            body = f"HTTP {resp.status_code}\n{resp.text}\n"
            self.sync_result.setPlainText(body)

            # Try to reuse agent restart as simplest force-sync path if agent owns writeback
            try:
                self.restart_agent()
            except Exception:
                pass

            self.reload_config()
        except Exception as e:
            self.sync_result.setPlainText(f"Sync failed:\n{e}")

    def refresh_main_header(self):
        try:
            if self.main_window and hasattr(self.main_window, "main_tab"):
                if hasattr(self.main_window.main_tab, "update_location_header"):
                    self.main_window.main_tab.update_location_header()
                self.sync_result.append("Main header refresh triggered.")
                QMessageBox.information(self, "Done", "Main header refresh triggered.")
            else:
                QMessageBox.warning(self, "Unavailable", "Main window or main tab not available.")
        except Exception as e:
            QMessageBox.warning(self, "Refresh failed", str(e))

    # ---------- cache/reset ----------

    def cache_result_append(self, text: str):
        self.cache_result.append(text)

    def delete_state_file(self):
        p = state_path()
        if not p.exists():
            QMessageBox.information(self, "Nothing to delete", "No state file exists.")
            return

        if QMessageBox.question(self, "Delete state file", f"Delete state file?\n\n{p}") != QMessageBox.Yes:
            return

        try:
            p.unlink()
            self.cache_result_append(f"Deleted state file: {p}")
            QMessageBox.information(self, "Deleted", "State file deleted.")
        except Exception as e:
            QMessageBox.warning(self, "Delete failed", str(e))

    def reload_everything(self):
        try:
            self.reload_config()
            self.refresh_main_header()
            self.force_license_refresh()
            self.cache_result_append("Reloaded config, header, and license state.")
        except Exception as e:
            self.cache_result_append(f"Reload failed: {e}")

    # ---------- printer diagnostics ----------

    def refresh_printer_diag_list(self):
        self.diag_printer_select.clear()
        try:
            printers = list_printers()
            for p in printers:
                self.diag_printer_select.addItem(p)
        except Exception as e:
            self.printer_diag_output.setPlainText(f"Failed to list printers:\n{e}")
            return

        try:
            con = db.connect()
            selected = db.get_setting(con, "printer_name") or ""
            con.close()
            idx = self.diag_printer_select.findText(selected)
            if idx >= 0:
                self.diag_printer_select.setCurrentIndex(idx)
        except Exception:
            pass

    def run_printer_diagnostics(self):
        printer_name = self.diag_printer_select.currentText().strip()
        if not printer_name:
            self.printer_diag_output.setPlainText("No printer selected.")
            return

        try:
            state = get_printer_state(printer_name)
            lines = [
                f"Printer: {state.printer_name}",
                f"OK: {state.ok}",
                f"Status: {state.status_text}",
                "",
                "Installed printers:",
            ]
            try:
                for p in list_printers():
                    lines.append(f" - {p}")
            except Exception as e:
                lines.append(f"Could not enumerate full list: {e}")

            self.printer_diag_output.setPlainText("\n".join(lines))
        except Exception as e:
            self.printer_diag_output.setPlainText(f"Diagnostics failed:\n{e}")

    # ---------- support bundle ----------

    def export_support_bundle(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Support Bundle",
            str(Path.home() / "tagify-support-bundle.zip"),
            "Zip Files (*.zip)"
        )
        if not save_path:
            return

        try:
            tmp = Path(tempfile.mkdtemp(prefix="tagify_support_"))

            # config snapshots
            try:
                config, source_name, source_path = get_active_config()
                (tmp / "active_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
                (tmp / "bundle_meta.txt").write_text(
                    f"config_source={source_name}\nconfig_path={source_path}\ndb_path={self._active_db_path}\n",
                    encoding="utf-8"
                )
            except Exception as e:
                (tmp / "config_error.txt").write_text(str(e), encoding="utf-8")

            # state/runtime files
            for p in runtime_files():
                try:
                    shutil.copy2(p, tmp / p.name)
                except Exception:
                    pass

            # db snapshot
            if self._active_db_path and Path(self._active_db_path).exists():
                try:
                    shutil.copy2(self._active_db_path, tmp / Path(self._active_db_path).name)
                except Exception:
                    pass

            # summary
            summary = (
                f"Source: {self._source_name}\n"
                f"Config path: {self._source_path}\n"
                f"Developer: {self._config.get('developer', False)}\n"
                f"Location: {self._config.get('location_name', '')}\n"
                f"Code: {self._config.get('location_code', '')}\n"
                f"App Version: {self._config.get('app_version', '')}\n"
                f"Printer: {self._config.get('printer_name', '')}\n"
                f"Enabled: {self._config.get('enabled', True)}\n"
                f"Database: {self._active_db_path if self._active_db_path else '(not found)'}\n"
            )
            (tmp / "debug_summary.txt").write_text(summary, encoding="utf-8")

            archive_base = str(Path(save_path).with_suffix(""))
            archive_path = shutil.make_archive(archive_base, "zip", root_dir=tmp)

            self.bundle_output.setPlainText(f"Support bundle created:\n{archive_path}")
            QMessageBox.information(self, "Exported", f"Support bundle exported:\n{archive_path}")
        except Exception as e:
            self.bundle_output.setPlainText(f"Export failed:\n{e}")
            QMessageBox.warning(self, "Export failed", str(e))