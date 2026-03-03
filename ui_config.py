import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTextEdit,
    QMessageBox, QFileDialog
)

import db

class ConfigTab(QWidget):
    def __init__(self, on_data_changed_callback, parent=None):
        super().__init__(parent)
        self.on_data_changed = on_data_changed_callback

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        card = QFrame()
        card.setObjectName("Card")
        root.addWidget(card, 1)

        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 14, 14, 14)
        card_l.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Config (JSON Backup)")
        title.setStyleSheet("font-weight: 600; font-size: 12pt;")

        btn_export = QPushButton("Export JSON")
        btn_import = QPushButton("Import JSON (replace)")
        btn_export.clicked.connect(self.export_json)
        btn_import.clicked.connect(self.import_json)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(btn_export)
        header.addWidget(btn_import)

        card_l.addLayout(header)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Export will place JSON here, or paste JSON to import.")
        card_l.addWidget(self.editor, 1)

    def export_json(self):
        con = db.connect()
        cats = db.list_categories(con)
        items = db.list_items(con)
        con.close()

        payload = {"categories": cats, "items": items}
        self.editor.setPlainText(json.dumps(payload, indent=2))
        QMessageBox.information(self, "Exported", "JSON exported to the editor.")

    def import_json(self):
        txt = self.editor.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Empty", "Paste JSON first.")
            return

        try:
            payload = json.loads(txt)
            cats = payload.get("categories", [])
            items = payload.get("items", [])
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", str(e))
            return

        if QMessageBox.question(self, "Replace", "This will replace ALL categories and items. Continue?") != QMessageBox.Yes:
            return

        con = db.connect()
        cur = con.cursor()
        cur.execute("DELETE FROM items")
        cur.execute("DELETE FROM categories")

        # reinsert categories
        id_map = {}
        for c in cats:
            name = c.get("name", "").strip()
            if not name:
                continue
            cur.execute("INSERT INTO categories(name) VALUES(?)", (name,))
            id_map[c.get("id")] = cur.lastrowid

        # reinsert items
        for it in items:
            name = it.get("name", "").strip()
            if not name:
                continue
            expire_days = int(it.get("expire_days", 0))
            old_cat = it.get("category_id")
            new_cat = id_map.get(old_cat) if old_cat is not None else None
            icon_path = it.get("icon_path")
            cur.execute(
                "INSERT INTO items(name, expire_days, category_id, icon_path) VALUES(?,?,?,?)",
                (name, expire_days, new_cat, icon_path)
            )

        con.commit()
        con.close()

        self.on_data_changed()
        QMessageBox.information(self, "Imported", "JSON imported and database replaced.")