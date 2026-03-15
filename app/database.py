import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "minishop.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK(role IN ('merchant', 'buyer')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                category TEXT,
                image_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (merchant_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS product_colors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                color_name TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER NOT NULL,
                total_price REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (buyer_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                color_name TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )

    seed_demo_data()


def seed_demo_data() -> None:
    """Seed starter records once so the project is demo-ready."""
    with get_connection() as conn:
        existing_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if existing_users > 0:
            return

        created_at = now_iso()

        # CREATE EXAMPLE: create users in SQLite
        conn.executemany(
            "INSERT INTO users (username, role, created_at) VALUES (?, ?, ?)",
            [
                ("alice_store", "merchant", created_at),
                ("greenlane_shop", "merchant", created_at),
                ("brian_buyer", "buyer", created_at),
                ("nina_buyer", "buyer", created_at),
            ],
        )

        merchants = conn.execute(
            "SELECT id, username FROM users WHERE role = 'merchant' ORDER BY id"
        ).fetchall()
        merchant_map = {m["username"]: m["id"] for m in merchants}

        sample_products = [
            (
                merchant_map["alice_store"],
                "Linen Everyday Shirt",
                "Breathable shirt for daily wear.",
                39.99,
                18,
                "Clothing",
                "https://via.placeholder.com/400x260?text=Linen+Shirt",
            ),
            (
                merchant_map["alice_store"],
                "Cotton Lounge Pants",
                "Relaxed fit lounge pants.",
                32.50,
                24,
                "Clothing",
                "https://via.placeholder.com/400x260?text=Lounge+Pants",
            ),
            (
                merchant_map["alice_store"],
                "Minimal Tote Bag",
                "Lightweight tote for everyday errands.",
                22.00,
                14,
                "Accessories",
                "https://via.placeholder.com/400x260?text=Tote+Bag",
            ),
            (
                merchant_map["alice_store"],
                "Ceramic Mug Set",
                "Set of two hand-finished mugs.",
                26.40,
                11,
                "Home",
                "https://via.placeholder.com/400x260?text=Ceramic+Mugs",
            ),
            (
                merchant_map["greenlane_shop"],
                "Desk Lamp Pro",
                "Warm/cool dimmable desk lamp.",
                58.00,
                9,
                "Home",
                "https://via.placeholder.com/400x260?text=Desk+Lamp",
            ),
            (
                merchant_map["greenlane_shop"],
                "Wireless Earbuds Mini",
                "Compact earbuds with charging case.",
                74.90,
                21,
                "Tech",
                "https://via.placeholder.com/400x260?text=Earbuds",
            ),
            (
                merchant_map["greenlane_shop"],
                "Smart Bottle",
                "Tracks hydration and glows as reminder.",
                45.25,
                7,
                "Tech",
                "https://via.placeholder.com/400x260?text=Smart+Bottle",
            ),
            (
                merchant_map["greenlane_shop"],
                "Woven Key Holder",
                "Wall-mounted key holder with shelf.",
                19.80,
                16,
                "Accessories",
                "https://via.placeholder.com/400x260?text=Key+Holder",
            ),
        ]

        for p in sample_products:
            conn.execute(
                """
                INSERT INTO products (
                    merchant_id, name, description, price, stock_quantity, category,
                    image_url, is_active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (*p, created_at, created_at),
            )

        products = conn.execute("SELECT id, name FROM products ORDER BY id").fetchall()
        product_id_map = {row["name"]: row["id"] for row in products}

        color_rows = [
            (product_id_map["Linen Everyday Shirt"], "Sand"),
            (product_id_map["Linen Everyday Shirt"], "Forest"),
            (product_id_map["Cotton Lounge Pants"], "Olive"),
            (product_id_map["Cotton Lounge Pants"], "Stone"),
            (product_id_map["Minimal Tote Bag"], "Moss"),
            (product_id_map["Minimal Tote Bag"], "Slate"),
            (product_id_map["Ceramic Mug Set"], "Cream"),
            (product_id_map["Ceramic Mug Set"], "Seafoam"),
            (product_id_map["Desk Lamp Pro"], "Graphite"),
            (product_id_map["Desk Lamp Pro"], "Pearl"),
            (product_id_map["Wireless Earbuds Mini"], "Midnight"),
            (product_id_map["Wireless Earbuds Mini"], "Sage"),
            (product_id_map["Smart Bottle"], "Teal"),
            (product_id_map["Smart Bottle"], "Mist"),
            (product_id_map["Woven Key Holder"], "Walnut"),
            (product_id_map["Woven Key Holder"], "Drift"),
        ]
        conn.executemany(
            "INSERT INTO product_colors (product_id, color_name) VALUES (?, ?)",
            color_rows,
        )

        conn.commit()
