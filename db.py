import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from security import hash_password

APP_NAME = "PrepStickerApp"
DB_FILE = "prep_stickers.db"

def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

def db_path() -> Path:
    return app_data_dir() / DB_FILE

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      expire_days INTEGER NOT NULL,
      category_id INTEGER NULL,
      icon_path TEXT NULL,
      FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    )
    """)

    # Seed admin password if not set
    if get_setting(con, "admin_password_hash") is None:
        set_setting(con, "admin_password_hash", hash_password("admin"))

    # Seed some categories/items if empty (optional, harmless)
    cur.execute("SELECT COUNT(*) AS c FROM items")
    if cur.fetchone()["c"] == 0:
        ensure_category(con, "All Prep")
        cat_id = get_category_by_name(con, "All Prep")["id"]
        add_item(con, "Chicken Salad", 3, cat_id, None)
        add_item(con, "Cooked Rice", 2, cat_id, None)
        add_item(con, "Chopped Lettuce", 2, cat_id, None)

    con.commit()
    con.close()

# ---- settings ----
def get_setting(con: sqlite3.Connection, key: str) -> Optional[str]:
    cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None

def set_setting(con: sqlite3.Connection, key: str, value: str):
    cur = con.cursor()
    cur.execute("""
      INSERT INTO settings(key,value) VALUES(?,?)
      ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    con.commit()

# ---- categories ----
def list_categories(con: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name COLLATE NOCASE")
    return [dict(r) for r in cur.fetchall()]

def get_category(con: sqlite3.Connection, cat_id: int) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("SELECT id,name FROM categories WHERE id=?", (cat_id,))
    r = cur.fetchone()
    return dict(r) if r else None

def get_category_by_name(con: sqlite3.Connection, name: str) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("SELECT id,name FROM categories WHERE name=?", (name,))
    r = cur.fetchone()
    return dict(r) if r else None

def ensure_category(con: sqlite3.Connection, name: str):
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (name,))
    con.commit()

def add_category(con: sqlite3.Connection, name: str):
    cur = con.cursor()
    cur.execute("INSERT INTO categories(name) VALUES(?)", (name,))
    con.commit()

def update_category(con: sqlite3.Connection, cat_id: int, name: str):
    cur = con.cursor()
    cur.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))
    con.commit()

def delete_category(con: sqlite3.Connection, cat_id: int):
    cur = con.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    con.commit()

# ---- items ----
def list_items(con: sqlite3.Connection, search: str = "", category_id: Optional[int] = None) -> List[Dict[str, Any]]:
    q = """
    SELECT i.id, i.name, i.expire_days, i.category_id, i.icon_path, c.name as category_name
    FROM items i
    LEFT JOIN categories c ON c.id = i.category_id
    WHERE 1=1
    """
    params = []
    if search.strip():
        q += " AND i.name LIKE ? "
        params.append(f"%{search.strip()}%")
    if category_id is not None:
        q += " AND i.category_id = ? "
        params.append(category_id)

    q += " ORDER BY i.name COLLATE NOCASE"

    cur = con.cursor()
    cur.execute(q, params)
    return [dict(r) for r in cur.fetchall()]

def get_item(con: sqlite3.Connection, item_id: int) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("""
    SELECT i.id, i.name, i.expire_days, i.category_id, i.icon_path, c.name as category_name
    FROM items i
    LEFT JOIN categories c ON c.id = i.category_id
    WHERE i.id=?
    """, (item_id,))
    r = cur.fetchone()
    return dict(r) if r else None

def add_item(con: sqlite3.Connection, name: str, expire_days: int, category_id: Optional[int], icon_path: Optional[str]):
    cur = con.cursor()
    cur.execute(
        "INSERT INTO items(name, expire_days, category_id, icon_path) VALUES(?,?,?,?)",
        (name, expire_days, category_id, icon_path)
    )
    con.commit()

def update_item(con: sqlite3.Connection, item_id: int, name: str, expire_days: int, category_id: Optional[int], icon_path: Optional[str]):
    cur = con.cursor()
    cur.execute(
        "UPDATE items SET name=?, expire_days=?, category_id=?, icon_path=? WHERE id=?",
        (name, expire_days, category_id, icon_path, item_id)
    )
    con.commit()

def delete_item(con: sqlite3.Connection, item_id: int):
    cur = con.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    con.commit()