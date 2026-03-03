APP_QSS = """
QWidget {
  font-family: Segoe UI;
  font-size: 10.5pt;
  color: #1f2a37;
  background: #f5f7fb;
}

QTabWidget::pane {
  border: 1px solid #e3e8f1;
  border-radius: 12px;
  background: #f5f7fb;
}

QTabBar::tab {
  padding: 10px 14px;
  margin: 6px 6px 0 6px;
  border: 1px solid #e3e8f1;
  border-bottom: none;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  background: #eef2f8;
}

QTabBar::tab:selected { background: #ffffff; }

QFrame#Card {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 14px;
}

QFrame#TopBar {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 14px;
}

QLabel#Title { font-size: 13pt; font-weight: 600; }
QLabel#Muted { color: #667085; }

QPushButton {
  background: #ffffff;
  border: 1px solid #d5dce9;
  border-radius: 10px;
  padding: 9px 12px;
}

QPushButton:hover { background: #f3f6fb; }
QPushButton:pressed { background: #e9eef7; }

QPushButton#Primary {
  background: #2563eb;
  color: white;
  border: 1px solid #2563eb;
  border-radius: 12px;
  padding: 12px 14px;
  font-weight: 600;
}
QPushButton#Primary:hover { background: #1d4ed8; }
QPushButton#Primary:pressed { background: #1e40af; }

QPushButton#Tile {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 16px;
  padding: 14px;
  text-align: left;
  min-height: 92px;
}
QPushButton#Tile:hover { background: #f3f6fb; }

QLineEdit, QComboBox, QSpinBox, QTextEdit, QTableWidget {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 10px;
  padding: 8px 10px;
}

QScrollArea {
  border: none;
  background: transparent;
}

QScrollBar:vertical {
  border: none;
  width: 12px;
  margin: 6px 4px 6px 4px;
  background: transparent;
}
QScrollBar::handle:vertical {
  border-radius: 6px;
  background: #d7deeb;
  min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #c8d0e0; }

QGroupBox {
  border: 1px solid #e3e8f1;
  border-radius: 12px;
  margin-top: 10px;
  padding: 10px;
  background: #ffffff;
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 4px;
  color: #334155;
  font-weight: 600;
}
QFrame#LabelPreview {
  background: #ffffff;
  border: 2px solid #e3e8f1;
  border-radius: 18px;
}

QLabel#LabelName {
  font-size: 13pt;
  font-weight: 800;
  color: #0f172a;
}
QFrame#StatusDot {
  border-radius: 8px;
  min-width: 16px;
  min-height: 16px;
  max-width: 16px;
  max-height: 16px;
  border: 1px solid #cbd5e1;
  background: #ef4444; /* red default */
}
QFrame#StatusDot[ok="true"] {
  background: #22c55e; /* green */
  border: 1px solid #16a34a;
}
QLabel#LabelMeta {
  font-size: 9.5pt;
  color: #475569;
}
"""