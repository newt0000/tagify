from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from label_print import print_label_direct

from PySide6.QtCore import Qt, QTimer, QDateTime, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
    QMessageBox, QSpinBox, QButtonGroup
)

import db
from printer_backend import get_printer_state
#from label_print import generate_1x1_label_pdf, print_label_pdf, make_temp_label_path


@dataclass
class SelectedItem:
    id: int
    name: str
    expire_days: int


class TileButton(QPushButton):
    """
    A polished tile button with:
    - optional icon bubble (42x42)
    - bold title
    - muted subtitle
    Uses checkable state for "selected" styling.
    """
    def __init__(self, title: str, icon_path: str | None, subtitle: str = "", parent=None):
        super().__init__("", parent)
        self.setObjectName("Tile")
        self.setCheckable(True)
        self.setMinimumHeight(92)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        # icon frame
        icon_frame = QFrame()
        icon_frame.setFixedSize(42, 42)
        icon_frame.setObjectName("TileIconFrame")
        icon_l = QVBoxLayout(icon_frame)
        icon_l.setContentsMargins(0, 0, 0, 0)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setObjectName("TileIcon")

        if icon_path and Path(icon_path).exists():
            pm = QIcon(icon_path).pixmap(32, 32)
            self.icon_lbl.setPixmap(pm)
        else:
            self.icon_lbl.setText("🏷️")

        icon_l.addWidget(self.icon_lbl)

        # text stack
        text_stack = QVBoxLayout()
        text_stack.setContentsMargins(0, 0, 0, 0)
        text_stack.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("TileTitle")
        self.title_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        self.title_lbl.setWordWrap(False)

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setObjectName("TileSub")
        self.sub_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        self.sub_lbl.setWordWrap(False)
        self.sub_lbl.setVisible(bool(subtitle))

        text_stack.addWidget(self.title_lbl)
        text_stack.addWidget(self.sub_lbl)

        text_wrap = QWidget()
        text_wrap.setLayout(text_stack)

        lay.addWidget(icon_frame)
        lay.addWidget(text_wrap, 1)


class MainTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected: SelectedItem | None = None
        self._tile_btns: list[TileButton] = []
        self._tile_group = QButtonGroup(self)
        self._tile_group.setExclusive(True)

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

        self.user_time = QLabel("Operator  00:00:00")
        self.user_time.setObjectName("Muted")

        top_l.addWidget(self.status_dot)
        top_l.addSpacing(6)
        top_l.addWidget(title_box_w)
        top_l.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        top_l.addWidget(self.user_time)
        root.addWidget(top)

        # printer status refresh
        self._printer_timer = QTimer(self)
        self._printer_timer.timeout.connect(self.refresh_printer_status)
        self._printer_timer.start(2000)
        self.refresh_printer_status()

        # --- Content row ---
        content = QHBoxLayout()
        content.setSpacing(12)

        # Left pane
        self.left = QFrame()
        self.left.setObjectName("Card")
        self.left.setMinimumWidth(360)
        left_l = QVBoxLayout(self.left)
        left_l.setContentsMargins(14, 14, 14, 14)
        left_l.setSpacing(12)

        # Print count card
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
        preview_card = QFrame()
        preview_card.setObjectName("Card")
        prev_l = QVBoxLayout(preview_card)
        prev_l.setContentsMargins(12, 12, 12, 12)
        prev_l.setSpacing(8)

        prev_title = QLabel("Tag Preview (1x1\")")
        prev_title.setStyleSheet("font-weight: 600;")
        prev_l.addWidget(prev_title)

        label_frame = QFrame()
        label_frame.setObjectName("LabelPreview")
        label_l = QVBoxLayout(label_frame)
        label_l.setContentsMargins(14, 12, 14, 12)
        label_l.setSpacing(4)

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
        left_l.addWidget(preview_card)

        hint = QLabel("Tip: Select an item on the right.\nThen press Print.")
        hint.setObjectName("Muted")
        left_l.addWidget(hint)

        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("Primary")
        self.btn_print.setEnabled(False)  # enable only when item selected
        self.btn_print.clicked.connect(self.on_print)
        left_l.addWidget(self.btn_print)

        left_l.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right pane
        self.right = QFrame()
        self.right.setObjectName("Card")
        right_l = QVBoxLayout(self.right)
        right_l.setContentsMargins(14, 14, 14, 14)
        right_l.setSpacing(10)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        filters.setContentsMargins(0, 0, 0, 0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search items…")
        self.search.textChanged.connect(self.refresh_tiles)

        self.category = QComboBox()
        self.category.currentIndexChanged.connect(self.refresh_tiles)

        filters.addWidget(self.search, 1)
        filters.addWidget(self.category, 0)
        right_l.addLayout(filters)

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

        # Load
        self.reload_categories()
        self.refresh_tiles()

    def _tick(self):
        now = QDateTime.currentDateTime()
        self.user_time.setText(f"Operator  {now.toString('HH:mm:ss')}")

    def refresh_printer_status(self):
        con = db.connect()
        printer_name = db.get_setting(con, "printer_name")
        con.close()

        state = get_printer_state(printer_name)
        self.status_dot.setProperty("ok", "true" if state.ok else "false")
        self.status_dot.setToolTip(
            f"Printer: {state.printer_name or '(none)'}\nStatus: {state.status_text}"
        )

        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)

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
        # Clear selection state
        self.selected = None
        self.btn_print.setEnabled(False)
        self.update_preview()

        # Clear group + buttons list
        for b in self._tile_btns:
            self._tile_group.removeButton(b)
            b.setParent(None)
        self._tile_btns.clear()

        # Clear grid widgets
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
            subtitle = f'{it.get("category_name") or "Uncategorized"} • {it["expire_days"]} day(s)'
            btn = TileButton(it["name"], it.get("icon_path"), subtitle)
            btn.setProperty("item_id", it["id"])

            # Add to exclusive group
            self._tile_group.addButton(btn)
            btn.clicked.connect(self._on_tile_clicked)

            self._tile_btns.append(btn)
            self.grid.addWidget(btn, r, c)

            c += 1
            if c >= cols:
                c = 0
                r += 1

        spacer = QWidget()
        spacer.setFixedHeight(10)
        self.grid.addWidget(spacer, r + 1, 0)

    def _on_tile_clicked(self):
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        item_id = btn.property("item_id")
        if item_id is None:
            return
        self.on_select(int(item_id))

    def on_select(self, item_id: int):
        # Ensure exclusivity visually: check only the selected tile.
        for b in self._tile_btns:
            b.setChecked(int(b.property("item_id")) == item_id)

        con = db.connect()
        it = db.get_item(con, item_id)
        con.close()
        if not it:
            return

        self.selected = SelectedItem(
            id=it["id"],
            name=it["name"],
            expire_days=int(it["expire_days"])
        )

        self.btn_print.setEnabled(True)
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

        state = get_printer_state(printer_name)
        if not state.ok:
            QMessageBox.warning(
                self,
                "No printer connected",
                "No printer connected.\n\nPlease navigate to Settings and select/connect to a printer."
            )
            return

        prepped = date.today()
        expires = prepped + timedelta(days=self.selected.expire_days)
        result = print_label_direct(
            printer_name=printer_name,
            item_name=self.selected.name,
            prepped=prepped,
            expires=expires,
            copies=self.copies.value(),
        )

        if not result.ok:
            QMessageBox.warning(self, "Print failed", result.message)
            return

        QMessageBox.information(self, "Printed", result.message)