from __future__ import annotations

from pathlib import Path
from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QFormLayout, QComboBox, QMessageBox, QLineEdit, QGroupBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QFileDialog, QSpinBox, QDialog, QHeaderView
)

import db
from security import verify_password, hash_password
from printer_backend import list_printers, get_printer_state
from label_print import generate_1x1_label_pdf, print_label_pdf, make_temp_label_path


class PasswordDialog(QDialog):
    def __init__(self, parent=None, title: str = "Admin Unlock", prompt: str = "Enter admin password:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(360, 150)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        lbl = QLabel(prompt)

        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.cancel = QPushButton("Cancel")
        self.ok = QPushButton("OK")
        self.ok.setObjectName("Primary")
        self.cancel.clicked.connect(self.reject)
        self.ok.clicked.connect(self.accept)
        btn_row.addWidget(self.cancel)
        btn_row.addWidget(self.ok)

        root.addWidget(lbl)
        root.addWidget(self.pw)
        root.addLayout(btn_row)


class ItemDialog(QDialog):
    def __init__(self, categories: list[dict], item: dict | None = None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Add Item" if item is None else "Edit Item")
        self.resize(460, 280)
        self.icon_path: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.name = QLineEdit()

        self.expire_days = QSpinBox()
        self.expire_days.setRange(0, 3650)
        self.expire_days.setValue(3)
        self.expire_days.setButtonSymbols(QSpinBox.NoButtons)
        self.expire_days.setAlignment(Qt.AlignCenter)

        self.category = QComboBox()
        self.category.addItem("(None)", None)
        for c in categories:
            self.category.addItem(c["name"], c["id"])

        form.addRow("Name:", self.name)
        form.addRow("Expire Days:", self.expire_days)
        form.addRow("Category:", self.category)

        root.addLayout(form)

        # Icon picker row
        icon_label = QLabel("Icon (optional, UI only):")
        root.addWidget(icon_label)

        icon_row = QHBoxLayout()
        self.icon_value = QLabel("(none)")
        self.icon_value.setObjectName("Muted")
        self.btn_pick = QPushButton("Choose…")
        self.btn_clear = QPushButton("Clear")
        self.btn_pick.clicked.connect(self.pick_icon)
        self.btn_clear.clicked.connect(self.clear_icon)

        icon_row.addWidget(self.icon_value, 1)
        icon_row.addWidget(self.btn_pick)
        icon_row.addWidget(self.btn_clear)
        root.addLayout(icon_row)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok = QPushButton("Save")
        self.btn_ok.setObjectName("Primary")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        root.addLayout(btns)

        if item:
            self.name.setText(item["name"])
            self.expire_days.setValue(int(item["expire_days"]))
            self.icon_path = item.get("icon_path")
            self.icon_value.setText(self.icon_path if self.icon_path else "(none)")
            cat_id = item.get("category_id")
            idx = self.category.findData(cat_id)
            if idx >= 0:
                self.category.setCurrentIndex(idx)

    def pick_icon(self):
        p, _ = QFileDialog.getOpenFileName(self, "Choose icon", "", "Images (*.png *.jpg *.jpeg *.ico)")
        if p:
            self.icon_path = p
            self.icon_value.setText(p)

    def clear_icon(self):
        self.icon_path = None
        self.icon_value.setText("(none)")


class SettingsTab(QWidget):
    def __init__(self, on_data_changed_callback, parent=None):
        super().__init__(parent)
        self.on_data_changed = on_data_changed_callback
        self.admin_unlocked = False

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # =========================
        # Settings Card
        # =========================
        settings_card = QFrame()
        settings_card.setObjectName("Card")
        root.addWidget(settings_card)

        sc = QVBoxLayout(settings_card)
        sc.setContentsMargins(14, 14, 14, 14)
        sc.setSpacing(12)

        title = QLabel("Settings")
        title.setStyleSheet("font-weight: 700; font-size: 12pt;")
        sc.addWidget(title)

        # Row: printer picker + status pill
        row = QHBoxLayout()
        row.setSpacing(10)

        self.printer = QComboBox()
        self.printer.setMinimumWidth(360)

        self.printer_status_pill = QLabel("Offline")
        self.printer_status_pill.setObjectName("PillBad")
        self.printer_status_pill.setAlignment(Qt.AlignCenter)
        self.printer_status_pill.setFixedHeight(30)
        self.printer_status_pill.setMinimumWidth(120)

        row.addWidget(QLabel("Printer:"), 0)
        row.addWidget(self.printer, 1)
        row.addWidget(self.printer_status_pill, 0)
        sc.addLayout(row)

        # Buttons row (compact like demo)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_refresh = QPushButton("Refresh Printers")
        self.btn_check = QPushButton("Check Connection")
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_connect.setObjectName("Primary")

        self.btn_refresh.clicked.connect(self.refresh_printers_dropdown)
        self.btn_check.clicked.connect(self.check_connection)
        self.btn_connect.clicked.connect(self.connect_printer)
        self.btn_disconnect.clicked.connect(self.disconnect_printer)

        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_check)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_disconnect)
        btn_row.addWidget(self.btn_connect)
        sc.addLayout(btn_row)

        # Test print row
        test_row = QHBoxLayout()
        test_row.setSpacing(10)
        self.btn_test = QPushButton("Test Print 1x1")
        self.btn_test.clicked.connect(self.test_print)
        test_row.addStretch(1)
        test_row.addWidget(self.btn_test)
        sc.addLayout(test_row)

        # initial load printers + saved selection
        self.refresh_printers_dropdown()
        self._apply_saved_printer_selection()
        self._update_printer_pill()

        # =========================
        # Admin Section (group style like app, but polished)
        # =========================
        admin_box = QGroupBox("Admin")
        admin_l = QVBoxLayout(admin_box)
        admin_l.setContentsMargins(12, 16, 12, 12)
        admin_l.setSpacing(10)
        root.addWidget(admin_box, 1)

        admin_top = QHBoxLayout()
        admin_top.setSpacing(10)

        self.admin_state_pill = QLabel("Locked")
        self.admin_state_pill.setObjectName("PillBad")
        self.admin_state_pill.setAlignment(Qt.AlignCenter)
        self.admin_state_pill.setFixedHeight(30)
        self.admin_state_pill.setMinimumWidth(110)

        self.btn_unlock = QPushButton("Enter Admin Mode")
        self.btn_unlock.setObjectName("Primary")
        self.btn_unlock.clicked.connect(self.unlock_admin)

        self.btn_lock = QPushButton("Lock Admin Mode")
        self.btn_lock.clicked.connect(self.lock_admin)
        self.btn_lock.setEnabled(False)

        self.btn_change_pw = QPushButton("Change Admin Password")
        self.btn_change_pw.clicked.connect(self.change_password)
        self.btn_change_pw.setEnabled(False)

        admin_top.addWidget(self.admin_state_pill)
        admin_top.addWidget(self.btn_unlock)
        admin_top.addWidget(self.btn_lock)
        admin_top.addStretch(1)
        admin_top.addWidget(self.btn_change_pw)
        admin_l.addLayout(admin_top)

        # Admin tabs
        self.admin_tabs = QTabWidget()
        self.admin_tabs.setEnabled(False)
        admin_l.addWidget(self.admin_tabs, 1)

        self.items_tab = QWidget()
        self.cats_tab = QWidget()
        self.admin_tabs.addTab(self.items_tab, "Items")
        self.admin_tabs.addTab(self.cats_tab, "Categories")

        self._build_items_tab()
        self._build_categories_tab()
        self.refresh_admin_tables()

    # -------------------------
    # Printer UX
    # -------------------------
    def refresh_printers_dropdown(self):
        current = self.printer.currentData() or ""

        self.printer.blockSignals(True)
        self.printer.clear()
        self.printer.addItem("(Default / Not set)", "")

        for p in list_printers():
            self.printer.addItem(p, p)

        # restore selection (current)
        if current:
            idx = self.printer.findData(current)
            if idx >= 0:
                self.printer.setCurrentIndex(idx)

        self.printer.blockSignals(False)

    def _apply_saved_printer_selection(self):
        con = db.connect()
        saved = db.get_setting(con, "printer_name") or ""
        con.close()

        idx = self.printer.findData(saved)
        if idx >= 0:
            self.printer.setCurrentIndex(idx)

    def _update_printer_pill(self):
        name = self.printer.currentData() or ""
        con = db.connect()
        saved = db.get_setting(con, "printer_name") or ""
        con.close()

        # show status of saved printer, not just current dropdown
        state = get_printer_state(saved if saved else None)

        if state.ok:
            self.printer_status_pill.setText("Connected")
            self.printer_status_pill.setObjectName("PillOk")
        else:
            self.printer_status_pill.setText("Offline")
            self.printer_status_pill.setObjectName("PillBad")

        self.printer_status_pill.setToolTip(
            f"Printer: {state.printer_name or '(none)'}\nStatus: {state.status_text}"
        )

        # re-polish for objectName change
        self.printer_status_pill.style().unpolish(self.printer_status_pill)
        self.printer_status_pill.style().polish(self.printer_status_pill)

    def check_connection(self):
        name = self.printer.currentData() or ""
        state = get_printer_state(name if name else None)
        QMessageBox.information(
            self,
            "Printer Status",
            f"Printer: {state.printer_name or '(none)'}\nStatus: {state.status_text}"
        )

    def connect_printer(self):
        name = self.printer.currentData() or ""
        con = db.connect()
        db.set_setting(con, "printer_name", name)
        con.close()

        self.on_data_changed()
        self._update_printer_pill()

        state = get_printer_state(name if name else None)
        QMessageBox.information(
            self,
            "Connected",
            f"Saved printer selection.\n\nPrinter: {state.printer_name or '(none)'}\nStatus: {state.status_text}"
        )

    def disconnect_printer(self):
        con = db.connect()
        db.set_setting(con, "printer_name", "")
        con.close()

        self.on_data_changed()
        self._update_printer_pill()

        QMessageBox.information(self, "Disconnected", "Printer selection cleared.")

    def test_print(self):
        con = db.connect()
        printer_name = db.get_setting(con, "printer_name")
        con.close()

        state = get_printer_state(printer_name)
        if not state.ok:
            QMessageBox.warning(
                self,
                "No printer connected",
                "Please Connect to a printer first."
            )
            return

        prepped = date.today()
        expires = prepped + timedelta(days=3)
        pdf_path = make_temp_label_path()
        generate_1x1_label_pdf("TEST LABEL", prepped, expires, pdf_path)

        try:
            print_label_pdf(str(pdf_path), printer_name=printer_name)
        except Exception as e:
            QMessageBox.critical(self, "Test print failed", str(e))
            return

        QMessageBox.information(self, "Test sent", "A test label was sent to the printer.")

    # -------------------------
    # Admin UX
    # -------------------------
    def unlock_admin(self):
        dlg = PasswordDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        con = db.connect()
        stored = db.get_setting(con, "admin_password_hash") or ""
        con.close()

        if not verify_password(dlg.pw.text(), stored):
            QMessageBox.warning(self, "Denied", "Incorrect password.")
            return

        self.admin_unlocked = True
        self.admin_tabs.setEnabled(True)
        self.btn_change_pw.setEnabled(True)
        self.btn_lock.setEnabled(True)
        self.btn_unlock.setEnabled(False)

        self.admin_state_pill.setText("Unlocked")
        self.admin_state_pill.setObjectName("PillOk")
        self.admin_state_pill.style().unpolish(self.admin_state_pill)
        self.admin_state_pill.style().polish(self.admin_state_pill)

    def lock_admin(self):
        self.admin_unlocked = False
        self.admin_tabs.setEnabled(False)
        self.btn_change_pw.setEnabled(False)
        self.btn_lock.setEnabled(False)
        self.btn_unlock.setEnabled(True)

        self.admin_state_pill.setText("Locked")
        self.admin_state_pill.setObjectName("PillBad")
        self.admin_state_pill.style().unpolish(self.admin_state_pill)
        self.admin_state_pill.style().polish(self.admin_state_pill)

    def change_password(self):
        if not self.admin_unlocked:
            return

        dlg = PasswordDialog(self, title="Set New Admin Password", prompt="New admin password:")
        if dlg.exec() != QDialog.Accepted:
            return

        new_pw = dlg.pw.text().strip()
        if len(new_pw) < 4:
            QMessageBox.warning(self, "Too short", "Use at least 4 characters.")
            return

        con = db.connect()
        db.set_setting(con, "admin_password_hash", hash_password(new_pw))
        con.close()

        QMessageBox.information(self, "Updated", "Admin password updated.")

    # -------------------------
    # Admin: Items tab
    # -------------------------
    def _build_items_tab(self):
        layout = QVBoxLayout(self.items_tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.btn_add_item = QPushButton("Add Item")
        self.btn_edit_item = QPushButton("Edit Selected")
        self.btn_del_item = QPushButton("Delete Selected")
        self.btn_del_item.setObjectName("Danger")

        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_edit_item.clicked.connect(self.edit_item)
        self.btn_del_item.clicked.connect(self.delete_item)

        top.addWidget(self.btn_add_item)
        top.addWidget(self.btn_edit_item)
        top.addWidget(self.btn_del_item)
        top.addStretch(1)
        layout.addLayout(top)

        self.items_table = QTableWidget(0, 5)
        self.items_table.setObjectName("DataTable")
        self.items_table.setHorizontalHeaderLabels(["ID", "Name", "Expire Days", "Category", "Icon"])
        self.items_table.setColumnHidden(0, True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.items_table, 1)

    def _selected_item_id(self) -> int | None:
        row = self.items_table.currentRow()
        if row < 0:
            return None
        return int(self.items_table.item(row, 0).text())

    def add_item(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return

        con = db.connect()
        cats = db.list_categories(con)
        con.close()

        dlg = ItemDialog(cats, None, self)
        if dlg.exec() != QDialog.Accepted:
            return

        name = dlg.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing", "Name is required.")
            return

        con = db.connect()
        db.add_item(con, name, int(dlg.expire_days.value()), dlg.category.currentData(), dlg.icon_path)
        con.close()

        self.refresh_admin_tables()
        self.on_data_changed()

    def edit_item(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return
        item_id = self._selected_item_id()
        if item_id is None:
            return

        con = db.connect()
        cats = db.list_categories(con)
        it = db.get_item(con, item_id)
        con.close()
        if not it:
            return

        dlg = ItemDialog(cats, it, self)
        if dlg.exec() != QDialog.Accepted:
            return

        name = dlg.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing", "Name is required.")
            return

        con = db.connect()
        db.update_item(con, item_id, name, int(dlg.expire_days.value()), dlg.category.currentData(), dlg.icon_path)
        con.close()

        self.refresh_admin_tables()
        self.on_data_changed()

    def delete_item(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return
        item_id = self._selected_item_id()
        if item_id is None:
            return

        if QMessageBox.question(self, "Delete", "Delete this item?") != QMessageBox.Yes:
            return

        con = db.connect()
        db.delete_item(con, item_id)
        con.close()

        self.refresh_admin_tables()
        self.on_data_changed()

    # -------------------------
    # Admin: Categories tab
    # -------------------------
    def _build_categories_tab(self):
        layout = QVBoxLayout(self.cats_tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.cat_name = QLineEdit()
        self.cat_name.setPlaceholderText("New category name…")

        self.btn_add_cat = QPushButton("Add Category")
        self.btn_ren_cat = QPushButton("Rename Selected")
        self.btn_del_cat = QPushButton("Delete Selected")
        self.btn_del_cat.setObjectName("Danger")

        self.btn_add_cat.clicked.connect(self.add_category)
        self.btn_ren_cat.clicked.connect(self.rename_category)
        self.btn_del_cat.clicked.connect(self.delete_category)

        top.addWidget(self.cat_name, 1)
        top.addWidget(self.btn_add_cat)
        top.addWidget(self.btn_ren_cat)
        top.addWidget(self.btn_del_cat)
        layout.addLayout(top)

        self.cats_table = QTableWidget(0, 2)
        self.cats_table.setObjectName("DataTable")
        self.cats_table.setHorizontalHeaderLabels(["ID", "Name"])
        self.cats_table.setColumnHidden(0, True)
        self.cats_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cats_table.setAlternatingRowColors(True)
        self.cats_table.verticalHeader().setVisible(False)
        self.cats_table.horizontalHeader().setStretchLastSection(True)
        self.cats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.cats_table, 1)

    def _selected_cat_id(self) -> int | None:
        row = self.cats_table.currentRow()
        if row < 0:
            return None
        return int(self.cats_table.item(row, 0).text())

    def add_category(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return

        name = self.cat_name.text().strip()
        if not name:
            return

        con = db.connect()
        try:
            db.add_category(con, name)
        except Exception as e:
            con.close()
            QMessageBox.warning(self, "Failed", f"Could not add category.\n{e}")
            return
        con.close()

        self.cat_name.clear()
        self.refresh_admin_tables()
        self.on_data_changed()

    def rename_category(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return

        cat_id = self._selected_cat_id()
        if cat_id is None:
            return

        dlg = PasswordDialog(self, title="Rename Category", prompt="Type new name:")
        dlg.pw.setEchoMode(QLineEdit.Normal)
        dlg.pw.setPlaceholderText("New category name")
        if dlg.exec() != QDialog.Accepted:
            return

        new_name = dlg.pw.text().strip()
        if not new_name:
            return

        con = db.connect()
        try:
            db.update_category(con, cat_id, new_name)
        except Exception as e:
            con.close()
            QMessageBox.warning(self, "Failed", f"Could not rename category.\n{e}")
            return
        con.close()

        self.refresh_admin_tables()
        self.on_data_changed()

    def delete_category(self):
        if not self.admin_unlocked:
            QMessageBox.information(self, "Locked", "Unlock admin mode first.")
            return

        cat_id = self._selected_cat_id()
        if cat_id is None:
            return

        if QMessageBox.question(self, "Delete", "Delete this category? Items will become uncategorized.") != QMessageBox.Yes:
            return

        con = db.connect()
        db.delete_category(con, cat_id)
        con.close()

        self.refresh_admin_tables()
        self.on_data_changed()

    # -------------------------
    # Refresh tables
    # -------------------------
    def refresh_admin_tables(self):
        con = db.connect()
        items = db.list_items(con)
        cats = db.list_categories(con)
        con.close()

        self.items_table.setRowCount(0)
        for it in items:
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            self.items_table.setItem(r, 0, QTableWidgetItem(str(it["id"])))
            self.items_table.setItem(r, 1, QTableWidgetItem(it["name"]))
            self.items_table.setItem(r, 2, QTableWidgetItem(str(it["expire_days"])))
            self.items_table.setItem(r, 3, QTableWidgetItem(it.get("category_name") or ""))
            self.items_table.setItem(r, 4, QTableWidgetItem(it.get("icon_path") or ""))

        self.cats_table.setRowCount(0)
        for c in cats:
            r = self.cats_table.rowCount()
            self.cats_table.insertRow(r)
            self.cats_table.setItem(r, 0, QTableWidgetItem(str(c["id"])))
            self.cats_table.setItem(r, 1, QTableWidgetItem(c["name"]))