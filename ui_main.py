from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from printer_backend import get_printer_state


from PySide6.QtCore import Qt, QTimer, QDateTime, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
    QMessageBox, QSpinBox
)

import db
from label_print import generate_1x1_label_pdf, print_label_pdf, make_temp_label_path


@dataclass
class SelectedItem:
    id: int
    name: str
    expire_days: int


class TileButton(QPushButton):
    def __init__(self, label: str, icon_path: str | None, parent=None):
        super().__init__(label, parent)
        self.setObjectName("Tile")
        self.setMinimumHeight(100)
        self.setIconSize(QSize(42, 42))

        if icon_path and Path(icon_path).exists():
            self.setIcon(QIcon(icon_path))
            # slightly smaller text when icon exists
            f = self.font()
            f.setPointSize(max(9, f.pointSize() - 1))
            self.setFont(f)
        else:
            # big name if no icon
            f = QFont(self.font())
            f.setPointSize(f.pointSize() + 3)
            f.setBold(True)
            self.setFont(f)


class MainTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected: SelectedItem | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # --- Top bar ---
        top = QFrame()
        top.setObjectName("TopBar")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(14, 12, 14, 12)
        top_l.setSpacing(10)

        self.status_dot = QFrame()
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setProperty("ok", "false")
        self.status_dot.setToolTip("Printer: (none)\nStatus: No printer selected")

        top_l.addWidget(self.status_dot)
        top_l.addSpacing(6)

        # Printer status polling (after status_dot exists)
        self._printer_timer = QTimer(self)
        self._printer_timer.timeout.connect(self.refresh_printer_status)
        self._printer_timer.start(2000)  # every 2 seconds
        self.refresh_printer_status()

        title = QLabel("🏷️ Prep Sticker Printer")
        title.setObjectName("Title")
        subtitle = QLabel("Main Screen")
        subtitle.setObjectName("Muted")

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        title_box_w = QWidget()
        title_box_w.setLayout(title_box)

        top_l.addWidget(title_box_w)
        top_l.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.user_time = QLabel("Operator  00:00:00")
        self.user_time.setObjectName("Muted")

       # self.btn_print = QPushButton("Print")
       # self.btn_print.setObjectName("Primary")
       # self.btn_print.clicked.connect(self.on_print)

       # top_l.addWidget(self.user_time)
       # top_l.addWidget(self.btn_print)
        top_l.addWidget(self.user_time)
        root.addWidget(top)

        # --- Content row ---
        content = QHBoxLayout()
        content.setSpacing(12)

        # Left pane: count + preview
        self.left = QFrame()
        self.left.setObjectName("Card")
        self.left.setMinimumWidth(360)

        left_l = QVBoxLayout(self.left)
        left_l.setContentsMargins(14, 14, 14, 14)
        left_l.setSpacing(12)

        # Count row
        count_card = QFrame()
        count_card.setObjectName("Card")
        count_l = QHBoxLayout(count_card)
        count_l.setContentsMargins(12, 12, 12, 12)
        count_l.setSpacing(10)

        count_label = QLabel("Print Count")
        count_label.setStyleSheet("font-weight: 600;")

        self.btn_minus = QPushButton("–")
        self.btn_minus.setFixedWidth(42)
        self.btn_minus.clicked.connect(lambda: self.adjust_copies(-1))

        self.copies = QSpinBox()
        self.copies.setButtonSymbols(QSpinBox.NoButtons)
        self.copies.setAlignment(Qt.AlignCenter)
        self.copies.setRange(1, 99)
        self.copies.setValue(1)
        self.copies.setFixedWidth(90)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedWidth(42)
        self.btn_plus.clicked.connect(lambda: self.adjust_copies(+1))

        count_l.addWidget(count_label)
        count_l.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        count_l.addWidget(self.btn_minus)
        count_l.addWidget(self.copies)
        count_l.addWidget(self.btn_plus)

        left_l.addWidget(count_card)

        # Preview card
        preview = QFrame()
        preview.setObjectName("Card")
        prev_l = QVBoxLayout(preview)
        prev_l.setContentsMargins(12, 12, 12, 12)
        prev_l.setSpacing(8)

        prev_title = QLabel("Tag Preview (1x1\")")
        prev_title.setStyleSheet("font-weight: 600;")
        prev_l.addWidget(prev_title)

        label_frame = QFrame()
        label_frame.setObjectName("LabelPreview")

        label_l = QVBoxLayout(label_frame)
        label_l.setContentsMargins(14, 12, 14, 12)
        label_l.setSpacing(6)

        self.prev_name = QLabel("Select an item…")
        self.prev_name.setObjectName("LabelName")

        self.prev_prepped = QLabel("Prepped: —")
        self.prev_prepped.setObjectName("LabelMeta")

        self.prev_expires = QLabel("Expires: —")
        self.prev_expires.setObjectName("LabelMeta")

        label_l.addWidget(self.prev_name)
        label_l.addWidget(self.prev_prepped)
        label_l.addWidget(self.prev_expires)

        prev_l.addWidget(label_frame)

        left_l.addWidget(preview)

        hint = QLabel("Tip: Select an item on the right.\nThen press Print.")
        hint.setObjectName("Muted")
        left_l.addWidget(hint)
        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("Primary")
        self.btn_print.clicked.connect(self.on_print)
        left_l.addWidget(self.btn_print)

        left_l.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right pane: search + category + scroll grid
        self.right = QFrame()
        self.right.setObjectName("Card")
        right_l = QVBoxLayout(self.right)
        right_l.setContentsMargins(14, 14, 14, 14)
        right_l.setSpacing(10)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search items…")
        self.search.textChanged.connect(self.refresh_tiles)

        self.category = QComboBox()
        self.category.currentIndexChanged.connect(self.refresh_tiles)

        filters.addWidget(self.search, 1)
        filters.addWidget(self.category, 0)

        right_l.addLayout(filters)

        # Scroll area with grid inside
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(2, 2, 2, 2)

        self.scroll.setWidget(self.grid_host)
        right_l.addWidget(self.scroll, 1)

        content.addWidget(self.left, 0)
        content.addWidget(self.right, 1)

        root.addLayout(content, 1)

        # Clock
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(250)
        self._tick()

        # Load categories & tiles
        self.reload_categories()
        self.refresh_tiles()

    def refresh_printer_status(self):
        con = db.connect()
        printer_name = db.get_setting(con, "printer_name")
        con.close()

        state = get_printer_state(printer_name)

        self.status_dot.setProperty("ok", "true" if state.ok else "false")
        self.status_dot.setToolTip(
            f"Printer: {state.printer_name or '(none)'}\nStatus: {state.status_text}"
        )

        # force stylesheet to re-evaluate the dynamic property
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
    def _tick(self):
        now = QDateTime.currentDateTime()
        self.user_time.setText(f"Operator  {now.toString('HH:mm:ss')}")

    def adjust_copies(self, delta: int):
        self.copies.setValue(max(1, self.copies.value() + delta))

    def reload_categories(self):
        con = db.connect()
        cats = db.list_categories(con)
        con.close()

        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("All Categories", None)
        for c in cats:
            self.category.addItem(c["name"], c["id"])
        self.category.blockSignals(False)

    def refresh_tiles(self):
        # Clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        search = self.search.text().strip()
        cat_id = self.category.currentData()

        con = db.connect()
        items = db.list_items(con, search=search, category_id=cat_id)
        con.close()

        cols = 3
        r = c = 0
        for it in items:
            btn = TileButton(it["name"], it.get("icon_path"))
            btn.clicked.connect(lambda _=False, item_id=it["id"]: self.on_select(item_id))
            self.grid.addWidget(btn, r, c)
            c += 1
            if c >= cols:
                c = 0
                r += 1

        # padding spacer so last row isn't jammed
        spacer = QWidget()
        spacer.setFixedHeight(10)
        self.grid.addWidget(spacer, r + 1, 0)

    def on_select(self, item_id: int):
        con = db.connect()
        it = db.get_item(con, item_id)
        con.close()
        if not it:
            return

        self.selected = SelectedItem(id=it["id"], name=it["name"], expire_days=int(it["expire_days"]))
        self.update_preview()

    def update_preview(self):
        if not self.selected:
            self.prev_name.setText("Select an item…")
            self.prev_prepped.setText("Prepped: —")
            self.prev_expires.setText("Expires: —")
            return

        prepped = date.today()
        expires = prepped + timedelta(days=self.selected.expire_days)

        self.prev_name.setText(self.selected.name)
        self.prev_prepped.setText(f"Prepped: {prepped.strftime('%m/%d/%Y')}")
        self.prev_expires.setText(f"Expires: {expires.strftime('%m/%d/%Y')}")

    def on_print(self):
        if not self.selected:
            QMessageBox.information(self, "No item selected", "Select an item to print first.")
            return

        con = db.connect()
        printer_name = db.get_setting(con, "printer_name")
        con.close()

        prepped = date.today()
        expires = prepped + timedelta(days=self.selected.expire_days)

        con = db.connect()
        printer_name = db.get_setting(con, "printer_name")
        con.close()

        state = get_printer_state(printer_name)
        if not state.ok:
            QMessageBox.warning(
                self,
                "No printer connected",
                "No printer connected.\n\nPlease navigate to Settings and select/connect to a printer."
            )
            return

        pdf_path = make_temp_label_path()
        generate_1x1_label_pdf(self.selected.name, prepped, expires, pdf_path)

        copies = self.copies.value()
        try:
            for _ in range(copies):
                print_label_pdf(str(pdf_path), printer_name=printer_name)
        except Exception as e:
            QMessageBox.critical(self, "Print failed", str(e))
            return

        QMessageBox.information(self, "Printed", f"Sent {copies} label(s) to printer.")