"""
inventory.py — SQLite-based inventory management
"""
import sqlite3
from datetime import datetime

DB_PATH = "grocery.db"

# Category auto-detect by keyword
KEYWORD_CAT = {
    "milk":"🥛 Dairy","curd":"🥛 Dairy","paneer":"🥛 Dairy","butter":"🥛 Dairy","cheese":"🥛 Dairy","yogurt":"🥛 Dairy",
    "rice":"🌾 Grains","wheat":"🌾 Grains","atta":"🌾 Grains","dal":"🌾 Grains","flour":"🌾 Grains","oats":"🌾 Grains","bread":"🌾 Grains","poha":"🌾 Grains","semolina":"🌾 Grains","suji":"🌾 Grains",
    "egg":"🥚 Eggs","eggs":"🥚 Eggs",
    "onion":"🥦 Vegetables","potato":"🥦 Vegetables","tomato":"🥦 Vegetables","carrot":"🥦 Vegetables","spinach":"🥦 Vegetables","cabbage":"🥦 Vegetables","brinjal":"🥦 Vegetables","cauliflower":"🥦 Vegetables","peas":"🥦 Vegetables","beans":"🥦 Vegetables","cucumber":"🥦 Vegetables","garlic":"🥦 Vegetables","ginger":"🥦 Vegetables","capsicum":"🥦 Vegetables",
    "apple":"🍎 Fruits","banana":"🍎 Fruits","mango":"🍎 Fruits","orange":"🍎 Fruits","grapes":"🍎 Fruits","watermelon":"🍎 Fruits","papaya":"🍎 Fruits","guava":"🍎 Fruits","pomegranate":"🍎 Fruits","lemon":"🍎 Fruits","pear":"🍎 Fruits","pineapple":"🍎 Fruits",
    "oil":"🛢️ Oils","ghee":"🛢️ Oils","mustard oil":"🛢️ Oils","coconut oil":"🛢️ Oils",
    "salt":"🧂 Spices","sugar":"🧂 Spices","turmeric":"🧂 Spices","chilli":"🧂 Spices","cumin":"🧂 Spices","coriander":"🧂 Spices","pepper":"🧂 Spices","masala":"🧂 Spices","jeera":"🧂 Spices","haldi":"🧂 Spices",
    "tea":"🥤 Beverages","coffee":"🥤 Beverages","juice":"🥤 Beverages","water":"🥤 Beverages","cold drink":"🥤 Beverages","soda":"🥤 Beverages",
    "biscuit":"🍫 Snacks","chips":"🍫 Snacks","chocolate":"🍫 Snacks","namkeen":"🍫 Snacks","snack":"🍫 Snacks","cookie":"🍫 Snacks","cake":"🍫 Snacks",
    "soap":"🧹 Household","shampoo":"🧹 Household","detergent":"🧹 Household","toothpaste":"🧹 Household","brush":"🧹 Household","tissue":"🧹 Household","cloth":"🧹 Household","mop":"🧹 Household",
}

CAT_ICONS = {
    "🥛 Dairy": "🥛",
    "🌾 Grains": "🌾",
    "🥚 Eggs": "🥚",
    "🥦 Vegetables": "🥦",
    "🍎 Fruits": "🍎",
    "🛢️ Oils": "🛢️",
    "🧂 Spices": "🧂",
    "🥤 Beverages": "🥤",
    "🍫 Snacks": "🍫",
    "🧹 Household": "🧹",
}


def get_conn():
    return sqlite3.connect(DB_PATH)


def guess_category(name: str) -> str:
    """Auto-detect category from item name keywords."""
    lower = name.lower()
    for keyword, cat in KEYWORD_CAT.items():
        if keyword in lower:
            return cat
    return "🍎 Fruits"  # default


def init_db():
    """Create tables and seed sample data if empty."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                qty     REAL DEFAULT 0,
                unit    TEXT DEFAULT 'units',
                status  TEXT DEFAULT 'ok',
                icon    TEXT DEFAULT '📦',
                cat     TEXT DEFAULT 'Other',
                added   TEXT,
                last_notified TEXT
            )
        """)
        # Track how often each item is added (for Frequent Items feature)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frequent_items (
                name    TEXT PRIMARY KEY,
                count   INTEGER DEFAULT 1,
                unit    TEXT DEFAULT 'units',
                cat     TEXT DEFAULT 'Other',
                icon    TEXT DEFAULT '📦',
                last_added TEXT
            )
        """)
        # Persistent Cart (allows WhatsApp bot to add items)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                price   REAL,
                platform TEXT,
                qty     INTEGER DEFAULT 1,
                added_at TEXT
            )
        """)
        conn.commit()

        # Seed sample data if table is empty
        count = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        if count == 0:
            samples = [
                ("Toned Milk",    2,   "L",  "low",  "🥛", "🥛 Dairy"),
                ("Basmati Rice",  3,   "kg", "ok",   "🌾", "🌾 Grains"),
                ("Toor Dal",      0.5, "kg", "low",  "🌾", "🌾 Grains"),
                ("Sunflower Oil", 1,   "L",  "med",  "🛢️", "🛢️ Oils"),
                ("Onions",        2,   "kg", "ok",   "🥦", "🥦 Vegetables"),
                ("Eggs",          6,   "units","med", "🥚", "🥚 Eggs"),
            ]
            today = datetime.now().strftime("%Y-%m-%d")
            conn.executemany(
                "INSERT INTO inventory (name,qty,unit,status,icon,cat,added) VALUES (?,?,?,?,?,?,?)",
                [(*s, today) for s in samples]
            )
            conn.commit()


def add_item(name: str, qty: float, unit: str, cat: str, status: str, icon: str):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO inventory (name,qty,unit,status,icon,cat,added) VALUES (?,?,?,?,?,?,?)",
            (name, qty, unit, status, icon, cat, today)
        )
        # Track frequency
        conn.execute("""
            INSERT INTO frequent_items (name, count, unit, cat, icon, last_added)
            VALUES (?, 1, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                count = count + 1,
                last_added = excluded.last_added
        """, (name.title(), unit, cat, icon, today))
        conn.commit()


def get_all_items():
    """Returns list of tuples: (id, name, qty, unit, status, icon, cat, added, last_notified)"""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,qty,unit,status,icon,cat,added,last_notified FROM inventory ORDER BY added DESC"
        ).fetchall()


def get_item_by_name(name: str):
    """Find an existing inventory item by name (case-insensitive)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,qty,unit,status,icon,cat,added,last_notified FROM inventory WHERE LOWER(name)=LOWER(?) LIMIT 1",
            (name,)
        ).fetchone()


def get_low_items():
    """Returns items with status='low'."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,qty,unit,status,icon,cat,added,last_notified FROM inventory WHERE status='low'"
        ).fetchall()


def get_frequent_items(limit: int = 8):
    """Returns most frequently added items."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT name,count,unit,cat,icon FROM frequent_items ORDER BY count DESC LIMIT ?",
            (limit,)
        ).fetchall()


def delete_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        conn.commit()


def update_item_status(item_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE inventory SET status=? WHERE id=?", (status, item_id))
        conn.commit()


def update_item_qty(item_id: int, qty: float):
    with get_conn() as conn:
        conn.execute("UPDATE inventory SET qty=? WHERE id=?", (qty, item_id))
        conn.commit()


def update_last_notified(item_id: int):
    """Update last_notified to current date."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        conn.execute("UPDATE inventory SET last_notified=? WHERE id=?", (today, item_id))
        conn.commit()


def increment_item_qty(item_id: int, delta: float):
    """Add delta to existing item's qty."""
    with get_conn() as conn:
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE id=?", (delta, item_id))
        conn.commit()


def get_db_cart():
    """Returns all items in the persistent cart."""
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, price, platform, qty FROM cart").fetchall()
        return [{"id":r[0], "name":r[1], "price":r[2], "platform":r[3], "qty":r[4]} for r in rows]


def add_to_db_cart(name: str, price: float, platform: str, qty: int = 1):
    """Adds an item to the persistent cart."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cart (name,price,platform,qty,added_at) VALUES (?,?,?,?,?)",
            (name, price, platform, qty, today)
        )
        conn.commit()


def delete_from_db_cart(cart_id: int):
    """Delete item from persistent cart."""
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        conn.commit()


def clear_db_cart():
    """Clears the persistent cart."""
    with get_conn() as conn:
        conn.execute("DELETE FROM cart")
        conn.commit()


def ai_add_to_inventory(name: str, qty: float, unit: str = "units") -> dict:
    """
    Smart add: if item already exists, increment qty.
    If new, auto-detect category and add.
    Returns dict with action taken.
    """
    existing = get_item_by_name(name)
    cat  = guess_category(name)
    icon = CAT_ICONS.get(cat, "📦")

    if existing:
        increment_item_qty(existing[0], qty)
        # also bump frequency
        today = datetime.now().strftime("%Y-%m-%d")
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO frequent_items (name, count, unit, cat, icon, last_added)
                VALUES (?, 1, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET count = count + 1, last_added = excluded.last_added
            """, (name.title(), unit, cat, icon, today))
            conn.commit()
        return {
            "action": "updated",
            "name":   existing[1],
            "qty":    existing[2] + qty,
            "unit":   existing[3],
            "cat":    existing[6],
            "icon":   existing[5],
        }
    else:
        status = "ok" if qty >= 3 else "med" if qty >= 1 else "low"
        add_item(name.title(), qty, unit, cat, status, icon)
        return {
            "action": "added",
            "name":   name.title(),
            "qty":    qty,
            "unit":   unit,
            "cat":    cat,
            "icon":   icon,
        }
