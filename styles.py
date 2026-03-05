# styles.py

APP_QSS = r"""
/* =========================
   Global
   ========================= */
QWidget {
  font-family: "Segoe UI";
  font-size: 10.5pt;
  color: #1f2a37;
  background: #f5f7fb;
}

QLabel { 
  background: transparent; /* prevents “gray fill behind text” */
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

/* =========================
   Cards / Top Bar
   ========================= */
QFrame#Card, QFrame#TopBar {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 14px;
}

QLabel#Title { font-size: 13pt; font-weight: 600; }
QLabel#Muted { color: #667085; background: transparent; }

/* =========================
   Buttons
   ========================= */
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

QPushButton#Danger {
  background: #ffffff;
  border: 1px solid rgba(239,68,68,0.35);
  color: #b91c1c;
  border-radius: 12px;
  padding: 12px 14px;
  font-weight: 600;
}
QPushButton#Danger:hover { background: rgba(239,68,68,0.08); }
QPushButton#Danger:pressed { background: rgba(239,68,68,0.14); }

/* =========================
   Tiles
   ========================= */
QPushButton#Tile {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 16px;
  padding: 14px;
  text-align: left;
  min-height: 92px;
}
QPushButton#Tile:hover { background: #f3f6fb; }
QPushButton#Tile:checked {
  border: 1px solid rgba(37,99,235,0.35);
  background: #f3f6ff;
}

QFrame#TileIconFrame {
  background: #eef2f8;
  border: 1px solid #e3e8f1;
  border-radius: 12px;
}

QLabel#TileTitle {
  font-weight: 800;
  color: #0f172a;
  background: transparent;
}

QLabel#TileSub {
  color: #667085;
  font-size: 9.5pt;
  background: transparent;
}

/* =========================
   Inputs
   ========================= */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 10px;
  padding: 8px 10px;
  selection-background-color: rgba(37,99,235,0.18);
  selection-color: #0f172a;
}

/* ComboBox styled (field + arrow + popup) */
QComboBox {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 10px;
  padding: 8px 34px 8px 10px; /* room for arrow */
}
QComboBox:hover { background: #f3f6fb; }
QComboBox:focus { border: 1px solid rgba(37,99,235,0.45); }

QComboBox::drop-down {
  subcontrol-origin: padding;
  subcontrol-position: top right;
  width: 30px;
  border-left: 1px solid #e3e8f1;
  border-top-right-radius: 10px;
  border-bottom-right-radius: 10px;
  background: #ffffff;
}
QComboBox:hover::drop-down { background: #f3f6fb; }

QComboBox::down-arrow {
  image: none;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid #667085; /* caret */
}

/* Popup list */
QComboBox QAbstractItemView {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 12px;
  padding: 6px;
  outline: none;
  selection-background-color: rgba(37,99,235,0.14);
  selection-color: #0f172a;
}
QComboBox QAbstractItemView::item {
  padding: 8px 10px;
  border-radius: 8px;
  background: transparent;
}
QComboBox QAbstractItemView::item:hover { background: #f3f6fb; }
QComboBox QAbstractItemView::item:selected { background: rgba(37,99,235,0.14); }

/* =========================
   Scroll Areas / Scrollbars
   ========================= */
QScrollArea { border: none; background: transparent; }
QScrollArea QWidget { background: transparent; }

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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; width: 0; background: transparent; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
  border: none;
  height: 12px;
  margin: 4px 6px 4px 6px;
  background: transparent;
}
QScrollBar::handle:horizontal {
  border-radius: 6px;
  background: #d7deeb;
  min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #c8d0e0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { height: 0; width: 0; background: transparent; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* =========================
   GroupBox
   ========================= */
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
  font-weight: 700;
  background: transparent;
}

/* =========================
   Label Preview
   ========================= */
QFrame#LabelPreview {
  background: #ffffff;
  border: 2px solid #e3e8f1;
  border-radius: 18px;
}
QLabel#LabelName {
  font-size: 13pt;
  font-weight: 800;
  color: #0f172a;
  background: transparent;
}
QLabel#LabelMeta {
  font-size: 9.5pt;
  color: #475569;
  background: transparent;
}

/* =========================
   Status Dot
   ========================= */
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

/* =========================
   Pills (badges)
   ========================= */
QLabel#PillOk, QLabel#PillBad, QLabel#PillGhost {
  border-radius: 999px;
  padding: 6px 12px;
  font-weight: 700;
  background: transparent;
}

QLabel#PillOk {
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.35);
  color: #16a34a;
}

QLabel#PillBad {
  background: rgba(239,68,68,0.10);
  border: 1px solid rgba(239,68,68,0.35);
  color: #b91c1c;
}

QLabel#PillGhost {
  background: #eef2f8;
  border: 1px solid #e3e8f1;
  color: #667085;
}

/* =========================
   Tables (clean + readable)
   ========================= */
QTableWidget, QTableView {
  background: #ffffff;
  border: 1px solid #e3e8f1;
  border-radius: 12px;
  gridline-color: #e3e8f1;
  selection-background-color: rgba(37,99,235,0.14);
  selection-color: #0f172a;
}

QTableWidget::item, QTableView::item {
  padding: 8px 10px;
  color: #0f172a;
  background: #ffffff; /* force white base */
}
QTableWidget::item:alternate, QTableView::item:alternate {
  background: #f8fafc; /* light zebra only (no dark rows) */
}
QTableWidget::item:selected, QTableView::item:selected {
  background: rgba(37,99,235,0.14);
  color: #0f172a;
}

QHeaderView::section {
  background: #f3f6fb;
  color: #667085;
  border: none;
  border-bottom: 1px solid #e3e8f1;
  padding: 8px 10px;
  font-weight: 700;
}
QTableCornerButton::section {
  background: #f3f6fb;
  border: none;
  border-bottom: 1px solid #e3e8f1;
}

QTableWidget:focus, QTableView:focus { outline: none; }

/* =========================
   Tooltips
   ========================= */
QToolTip {
  background: #0f172a;
  color: #ffffff;
  border: none;
  padding: 8px 10px;
  border-radius: 10px;
}
"""