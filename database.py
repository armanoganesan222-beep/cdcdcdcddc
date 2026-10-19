
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_NAME = "bot.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _columns(conn, table):
    return {
        row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                stars INTEGER PRIMARY KEY,
                price REAL NOT NULL DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS premium_prices (
                months INTEGER PRIMARY KEY,
                price REAL NOT NULL DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                receiver TEXT DEFAULT '',
                stars INTEGER DEFAULT 0,
                price REAL DEFAULT 0,
                status TEXT DEFAULT 'waiting',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                product_type TEXT DEFAULT 'stars',
                premium_months INTEGER DEFAULT 0,
                receipt_file_id TEXT DEFAULT '',
                gram_amount REAL DEFAULT 0,
                gram_wallet TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS button_styles (
                button_name TEXT PRIMARY KEY,
                style TEXT NOT NULL DEFAULT 'primary'
            )
        """)

        # Migrations for an existing bot.db.
        order_columns = _columns(conn, "orders")
        migrations = {
            "username": "TEXT DEFAULT ''",
            "receiver": "TEXT DEFAULT ''",
            "stars": "INTEGER DEFAULT 0",
            "price": "REAL DEFAULT 0",
            "status": "TEXT DEFAULT 'waiting'",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
            "product_type": "TEXT DEFAULT 'stars'",
            "premium_months": "INTEGER DEFAULT 0",
            "receipt_file_id": "TEXT DEFAULT ''",
            "gram_amount": "REAL DEFAULT 0",
            "gram_wallet": "TEXT DEFAULT ''",
        }
        for column, definition in migrations.items():
            if column not in order_columns:
                conn.execute(
                    f"ALTER TABLE orders ADD COLUMN {column} {definition}"
                )

        user_columns = _columns(conn, "users")
        if "username" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN username TEXT DEFAULT ''")
        if "created_at" not in user_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            )
        if "last_active" not in user_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN last_active TEXT DEFAULT CURRENT_TIMESTAMP"
            )

        for stars, price in [
            (50, 66),
            (100, 132),
            (250, 330),
            (500, 660),
            (1000, 1320),
        ]:
            conn.execute(
                "INSERT OR IGNORE INTO prices (stars, price) VALUES (?, ?)",
                (stars, price),
            )

        for months, price in [(3, 599), (6, 1199), (12, 1999)]:
            conn.execute(
                "INSERT OR IGNORE INTO premium_prices (months, price) VALUES (?, ?)",
                (months, price),
            )

        defaults = {
            "stars_rate": "1.32",
            "gram_markup": "5",
            "gram_balance": "0",
            "gram_enabled": "0",
            "gram_payment_wallet": "",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )

        for button in ("stars", "premium", "gram", "profile", "promo"):
            conn.execute(
                "INSERT OR IGNORE INTO button_styles (button_name, style) VALUES (?, ?)",
                (button, "primary"),
            )


init_db()


# ---------------- USERS ----------------


def add_user(user_id, username="", *args):
    first_name = args[0] if len(args) > 0 else ""
    last_name = args[1] if len(args) > 1 else ""

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, created_at, last_active)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                last_active = CURRENT_TIMESTAMP
            """,
            (user_id, username or ""),
        )



def get_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT user_id, username, created_at, last_active FROM users ORDER BY user_id"
        ).fetchall()


def count_users():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def count_active_today():
    with get_connection() as conn:
        return conn.execute("""
            SELECT COUNT(*) FROM users
            WHERE date(last_active) = date('now', 'localtime')
        """).fetchone()[0]


def count_active_week():
    with get_connection() as conn:
        return conn.execute("""
            SELECT COUNT(*) FROM users
            WHERE datetime(last_active) >= datetime('now', '-7 days', 'localtime')
        """).fetchone()[0]


# ---------------- SETTINGS ----------------

def _get_setting(key, default=""):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else default


def _set_setting(key, value):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )


# ---------------- STARS ----------------

def get_stars_rate():
    saved = _get_setting("stars_rate", "")
    try:
        if saved != "":
            return float(saved)
    except (TypeError, ValueError):
        pass

    with get_connection() as conn:
        row = conn.execute(
            "SELECT price FROM prices WHERE stars = 100"
        ).fetchone()
    return float(row[0]) / 100 if row else 1.32


def set_stars_rate(rate):
    rate = float(rate)
    if rate <= 0:
        raise ValueError("Курс Stars должен быть больше нуля")

    with get_connection() as conn:
        conn.execute(
            "UPDATE prices SET price = ROUND(stars * ?, 2)",
            (rate,),
        )
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('stars_rate', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(rate),),
        )


def get_stars_price(stars):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT price FROM prices WHERE stars = ?", (int(stars),)
        ).fetchone()
    if row:
        return float(row[0])
    return round(int(stars) * get_stars_rate(), 2)


def get_price(stars):
    return get_stars_price(stars)


def set_price(stars, price):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prices (stars, price) VALUES (?, ?)
            ON CONFLICT(stars) DO UPDATE SET price = excluded.price
            """,
            (int(stars), float(price)),
        )


def get_all_prices():
    with get_connection() as conn:
        return conn.execute(
            "SELECT stars, price FROM prices ORDER BY stars"
        ).fetchall()


# ---------------- PREMIUM ----------------

def get_premium_price(months):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT price FROM premium_prices WHERE months = ?",
            (int(months),),
        ).fetchone()
    return float(row[0]) if row else 0


def set_premium_price(months, price):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO premium_prices (months, price) VALUES (?, ?)
            ON CONFLICT(months) DO UPDATE SET price = excluded.price
            """,
            (int(months), float(price)),
        )


def get_all_premium_prices():
    with get_connection() as conn:
        return conn.execute(
            "SELECT months, price FROM premium_prices ORDER BY months"
        ).fetchall()


# ---------------- GRAM SETTINGS / BALANCE ----------------

def get_gram_markup():
    try:
        return float(_get_setting("gram_markup", "5"))
    except (TypeError, ValueError):
        return 5.0


def set_gram_markup(value):
    value = float(value)
    if value < 0:
        raise ValueError("Наценка GRAM не может быть отрицательной")
    _set_setting("gram_markup", value)


def get_gram_balance():
    try:
        return float(_get_setting("gram_balance", "0"))
    except (TypeError, ValueError):
        return 0.0


def set_gram_balance(value):
    value = float(value)
    if value < 0:
        raise ValueError("Баланс GRAM не может быть отрицательным")
    _set_setting("gram_balance", value)


def get_gram_enabled():
    return _get_setting("gram_enabled", "0").lower() in (
        "1", "true", "yes", "on"
    )


def set_gram_enabled(enabled):
    _set_setting("gram_enabled", "1" if enabled else "0")


def get_gram_payment_wallet():
    return _get_setting("gram_payment_wallet", "")


def set_gram_payment_wallet(wallet):
    _set_setting("gram_payment_wallet", (wallet or "").strip())


# ---------------- BUTTON STYLES ----------------

def get_button_style(button_name):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT style FROM button_styles WHERE button_name = ?",
            (str(button_name),),
        ).fetchone()
    return row[0] if row else "primary"


def set_button_style(button_name, style):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO button_styles (button_name, style) VALUES (?, ?)
            ON CONFLICT(button_name) DO UPDATE SET style = excluded.style
            """,
            (str(button_name), str(style)),
        )


# ---------------- ADMINS ----------------

def is_admin(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", (int(user_id),)
        ).fetchone()
    return row is not None


def add_admin(user_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
            (int(user_id),),
        )


def remove_admin(user_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM admins WHERE user_id = ?", (int(user_id),)
        )


def get_admins():
    with get_connection() as conn:
        return [
            row[0] for row in conn.execute(
                "SELECT user_id FROM admins ORDER BY user_id"
            ).fetchall()
        ]


# ---------------- ORDERS ----------------

def create_order(
    user_id,
    username,
    receiver,
    stars,
    price,
    product_type="stars",
    premium_months=0,
    gram_amount=0,
    gram_wallet="",
):
    product_type = str(product_type or "stars").lower()
    gram_amount = float(gram_amount or 0)

    with get_connection() as conn:
        if product_type == "gram":
            enabled_row = conn.execute(
                "SELECT value FROM settings WHERE key = 'gram_enabled'"
            ).fetchone()
            enabled = enabled_row and enabled_row[0].lower() in (
                "1", "true", "yes", "on"
            )
            if not enabled:
                raise ValueError("Продажа GRAM сейчас отключена")

            balance_row = conn.execute(
                "SELECT value FROM settings WHERE key = 'gram_balance'"
            ).fetchone()
            balance = float(balance_row[0]) if balance_row else 0.0

            if gram_amount <= 0:
                raise ValueError("Количество GRAM должно быть больше нуля")
            if balance < gram_amount:
                raise ValueError("Недостаточно GRAM на балансе")

            # Reserve GRAM atomically when creating the order.
            new_balance = balance - gram_amount
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES ('gram_balance', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(new_balance),),
            )

        cursor = conn.execute(
            """
            INSERT INTO orders (
                user_id, username, receiver, stars, price, status,
                created_at, product_type, premium_months, receipt_file_id,
                gram_amount, gram_wallet
            )
            VALUES (?, ?, ?, ?, ?, 'waiting', CURRENT_TIMESTAMP, ?, ?, '', ?, ?)
            """,
            (
                int(user_id),
                username or "",
                receiver or "",
                int(stars or 0),
                float(price or 0),
                product_type,
                int(premium_months or 0),
                gram_amount,
                gram_wallet or "",
            ),
        )
        return cursor.lastrowid


def get_order(order_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                user_id, username, receiver, stars, price, status,
                created_at, product_type, premium_months, receipt_file_id,
                gram_amount, gram_wallet
            FROM orders WHERE id = ?
            """,
            (int(order_id),),
        ).fetchone()


def get_all_orders():
    # Layout for the admin list:
    # 0=id, 1=user_id, 2=username, 3=receiver, 4=stars, 5=price,
    # 6=status, 7=product_type, 8=premium_months, 9=created_at,
    # 10=receipt_file_id, 11=gram_amount, 12=gram_wallet.
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                id, user_id, username, receiver, stars, price, status,
                product_type, premium_months, created_at, receipt_file_id,
                gram_amount, gram_wallet
            FROM orders ORDER BY id DESC
            """
        ).fetchall()


def set_receipt(order_id, receipt_file_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE orders SET receipt_file_id = ? WHERE id = ?",
            (receipt_file_id or "", int(order_id)),
        )


def complete_order(order_id):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE orders SET status = 'completed'
            WHERE id = ? AND status = 'waiting'
            """,
            (int(order_id),),
        )


def cancel_order(order_id):
    with get_connection() as conn:
        order = conn.execute(
            """
            SELECT status, product_type, gram_amount
            FROM orders WHERE id = ?
            """,
            (int(order_id),),
        ).fetchone()

        if not order or order[0] != "waiting":
            return False

        status, product_type, gram_amount = order

        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ?",
            (int(order_id),),
        )

        # Return reserved GRAM only once, and only for an uncompleted order.
        if product_type == "gram" and float(gram_amount or 0) > 0:
            balance_row = conn.execute(
                "SELECT value FROM settings WHERE key = 'gram_balance'"
            ).fetchone()
            balance = float(balance_row[0]) if balance_row else 0.0
            new_balance = balance + float(gram_amount)

            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES ('gram_balance', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(new_balance),),
            )

        return True


def count_orders():
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]


def count_completed_orders():
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'completed'"
        ).fetchone()[0]


def touch_user(user_id, username=""):
    add_user(user_id, username)
