from __future__ import annotations

from typing import Any

import requests
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout
)

from config_source import get_active_config, write_api_key


def validate_key_direct(config: dict[str, Any]) -> dict[str, Any]:
    server_url = str(config.get("server_url", "")).rstrip("/")
    api_key = str(config.get("api_key", "")).strip()

    if not server_url:
        return {
            "allow_run": False,
            "status": "missing_server",
            "message": "Dashboard URL not configured"
        }

    if not api_key:
        return {
            "allow_run": False,
            "status": "missing",
            "message": "No API key registered, please request a key."
        }

    url = f"{server_url}/api/validate"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    body = {
        "location_name": config.get("location_name", "Unknown"),
        "location_code": config.get("location_code", "unknown"),
        "app_version": config.get("app_version", "1.0.0"),
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=10)
    except Exception as e:
        return {
            "allow_run": False,
            "status": "server_unreachable",
            "message": f"Could not reach dashboard: {e}"
        }

    try:
        data = resp.json()
    except Exception:
        return {
            "allow_run": False,
            "status": "invalid_response",
            "message": f"Dashboard returned HTTP {resp.status_code}"
        }

    return {
        "allow_run": bool(data.get("allow_run", False)),
        "status": data.get("status", "unknown"),
        "message": data.get("message", "Unknown validation result"),
    }


class LicenseBlockOverlay(QWidget):
    unlocked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
              background: rgba(245,247,251,0.98);
            }
            QLabel#Title {
              font-family: "Segoe UI";
              font-size: 18pt;
              font-weight: 700;
              color: #b91c1c;
              background: transparent;
            }
            QLabel#Body {
              font-family: "Segoe UI";
              font-size: 11pt;
              color: #1f2a37;
              background: transparent;
            }
            QLabel#Muted {
              font-family: "Segoe UI";
              font-size: 10pt;
              color: #667085;
              background: transparent;
            }
            QLineEdit {
              background: #ffffff;
              border: 1px solid #e3e8f1;
              border-radius: 10px;
              padding: 10px 12px;
              font-family: "Segoe UI";
              font-size: 10.5pt;
              color: #1f2a37;
            }
            QPushButton {
              background: #ffffff;
              border: 1px solid #d5dce9;
              border-radius: 12px;
              padding: 10px 14px;
              font-family: "Segoe UI";
              font-size: 10.5pt;
            }
            QPushButton:hover {
              background: #f3f6fb;
            }
            QPushButton#Primary {
              background: #2563eb;
              color: white;
              border: 1px solid #2563eb;
            }
            QPushButton#Primary:hover {
              background: #1d4ed8;
            }
            QPushButton#LinkBtn {
              background: transparent;
              border: none;
              color: #2563eb;
              text-decoration: underline;
              padding: 0;
            }
        """)

        self.config, self.config_source, self.config_path = get_active_config()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(12)

        self.title = QLabel("Tagify blocked")
        self.title.setObjectName("Title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.body = QLabel("")
        self.body.setObjectName("Body")
        self.body.setWordWrap(True)
        self.body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.setMaximumWidth(640)

        self.current_key = QLabel("")
        self.current_key.setObjectName("Muted")
        self.current_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_key.setWordWrap(True)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter API key")
        self.key_input.setMaximumWidth(520)
        self.key_input.setText(str(self.config.get("api_key", "")).strip())
        self.key_input.returnPressed.connect(self.submit_key)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.submit_btn = QPushButton("Submit Key")
        self.submit_btn.setObjectName("Primary")
        self.submit_btn.clicked.connect(self.submit_key)

        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_status)

        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.submit_btn)

        self.request_label = QLabel("No API key registered, please click this link to request a key.")
        self.request_label.setObjectName("Muted")
        self.request_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.request_btn = QPushButton("Request a key")
        self.request_btn.setObjectName("LinkBtn")
        self.request_btn.clicked.connect(self.open_request_page)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_app)

        root.addWidget(self.title)
        root.addWidget(self.body)
        root.addWidget(self.current_key)
        root.addWidget(self.key_input, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addLayout(btn_row)
        root.addWidget(self.request_label)
        root.addWidget(self.request_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        QTimer.singleShot(200, self.refresh_status)

    def request_url(self) -> str:
        server_url = str(self.config.get("server_url", "")).rstrip("/")
        return f"{server_url}/request-key"

    def open_request_page(self):
        QDesktopServices.openUrl(QUrl(self.request_url()))

    def close_app(self):
        window = self.window()
        if window:
            window.close()

    def submit_key(self):
        new_key = self.key_input.text().strip()
        self.config, self.config_source, self.config_path = write_api_key(new_key)
        self.refresh_status()

    def refresh_status(self):
        self.config, self.config_source, self.config_path = get_active_config()

        key = str(self.config.get("api_key", "")).strip()
        self.current_key.setText(
            f"Configured key: {key if key else '(none)'}   |   Source: {self.config_source.upper()}   |   {self.config_path}"
        )

        if self.key_input.text().strip() != key:
            self.key_input.setText(key)

        result = validate_key_direct(self.config)
        self.body.setText(result.get("message", "Validation failed"))

        no_key = result.get("status") == "missing"
        self.request_label.setVisible(no_key)
        self.request_btn.setVisible(no_key)

        if result.get("allow_run", False):
            self.hide()
            self.unlocked.emit()
        else:
            self.show()
            self.raise_()