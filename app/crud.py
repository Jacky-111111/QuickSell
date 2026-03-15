import sqlite3
from datetime import datetime
from typing import Any, Optional, Tuple

from app.database import get_connection


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def parse_colors(color_text: str) -> list[str]:
    return [c.strip() for c in color_text.split(",") if c.strip()]


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def create_user(username: str, role: str) -> sqlite3.Row:
    # CREATE EXAMPLE: creating a user row in SQLite
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, role, created_at) VALUES (?, ?, ?)",
            (username, role, now_iso()),
        )
        conn.commit()
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_merchant_products(merchant_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        # READ EXAMPLE: read merchant-owned products
        return conn.execute(
            """
            SELECT p.*,
                   GROUP_CONCAT(pc.color_name, ', ') AS colors,
                   COALESCE(SUM(oi.quantity), 0) AS sold_units,
                   COALESCE(SUM(oi.subtotal), 0) AS sales_revenue
            FROM products p
            LEFT JOIN product_colors pc ON pc.product_id = p.id
            LEFT JOIN order_items oi ON oi.product_id = p.id
            WHERE p.merchant_id = ?
            GROUP BY p.id
            ORDER BY p.updated_at DESC
            """,
            (merchant_id,),
        ).fetchall()


def get_product_for_merchant(product_id: int, merchant_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id = ? AND merchant_id = ?",
            (product_id, merchant_id),
        ).fetchone()


def get_product_colors(product_id: int) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT color_name FROM product_colors WHERE product_id = ? ORDER BY id",
            (product_id,),
        ).fetchall()
        return [r["color_name"] for r in rows]


def create_product(merchant_id: int, form: dict[str, Any], color_csv: str) -> int:
    # CREATE EXAMPLE: merchant creates product
    with get_connection() as conn:
        ts = now_iso()
        cursor = conn.execute(
            """
            INSERT INTO products (
                merchant_id, name, description, price, stock_quantity, category,
                image_url, is_active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                merchant_id,
                form["name"],
                form.get("description") or "",
                float(form["price"]),
                int(form["stock_quantity"]),
                form.get("category") or "",
                form.get("image_url") or "",
                1 if form.get("is_active") else 0,
                ts,
                ts,
            ),
        )
        product_id = cursor.lastrowid
        for color in parse_colors(color_csv):
            conn.execute(
                "INSERT INTO product_colors (product_id, color_name) VALUES (?, ?)",
                (product_id, color),
            )
        conn.commit()
        return int(product_id)


def update_product(product_id: int, merchant_id: int, form: dict[str, Any], color_csv: str) -> bool:
    # UPDATE EXAMPLE: merchant updates product and colors
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ? AND merchant_id = ?",
            (product_id, merchant_id),
        ).fetchone()
        if not existing:
            return False

        conn.execute(
            """
            UPDATE products
            SET name = ?,
                description = ?,
                price = ?,
                stock_quantity = ?,
                category = ?,
                image_url = ?,
                is_active = ?,
                updated_at = ?
            WHERE id = ? AND merchant_id = ?
            """,
            (
                form["name"],
                form.get("description") or "",
                float(form["price"]),
                int(form["stock_quantity"]),
                form.get("category") or "",
                form.get("image_url") or "",
                1 if form.get("is_active") else 0,
                now_iso(),
                product_id,
                merchant_id,
            ),
        )
        conn.execute("DELETE FROM product_colors WHERE product_id = ?", (product_id,))
        for color in parse_colors(color_csv):
            conn.execute(
                "INSERT INTO product_colors (product_id, color_name) VALUES (?, ?)",
                (product_id, color),
            )
        conn.commit()
        return True


def delete_product(product_id: int, merchant_id: int) -> bool:
    # DELETE EXAMPLE: merchant deletes a product
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM products WHERE id = ? AND merchant_id = ?",
            (product_id, merchant_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def toggle_product_active(product_id: int, merchant_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT is_active FROM products WHERE id = ? AND merchant_id = ?",
            (product_id, merchant_id),
        ).fetchone()
        if not row:
            return False
        new_value = 0 if row["is_active"] else 1
        conn.execute(
            "UPDATE products SET is_active = ?, updated_at = ? WHERE id = ? AND merchant_id = ?",
            (new_value, now_iso(), product_id, merchant_id),
        )
        conn.commit()
        return True


def get_merchant_sales_history(merchant_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT oi.id,
                   o.id AS order_id,
                   o.created_at,
                   o.shipping_address,
                   o.buyer_note,
                   p.id AS product_id,
                   p.name AS product_name,
                   oi.color_name,
                   oi.quantity,
                   oi.unit_price,
                   oi.subtotal,
                   b.username AS buyer_username
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            JOIN users b ON b.id = o.buyer_id
            WHERE p.merchant_id = ?
            ORDER BY o.created_at DESC
            """,
            (merchant_id,),
        ).fetchall()


def list_products(
    q: str = "",
    category: str = "",
    color: str = "",
    sort: str = "newest",
    only_active: bool = True,
) -> list[sqlite3.Row]:
    where = []
    params: list[Any] = []

    if only_active:
        where.append("p.is_active = 1")
    if q:
        where.append("p.name LIKE ?")
        params.append(f"%{q}%")
    if category:
        where.append("p.category = ?")
        params.append(category)
    if color:
        where.append("EXISTS (SELECT 1 FROM product_colors c2 WHERE c2.product_id = p.id AND c2.color_name = ?)")
        params.append(color)

    order_clause = {
        "price_asc": "p.price ASC",
        "price_desc": "p.price DESC",
        "newest": "p.created_at DESC",
    }.get(sort, "p.created_at DESC")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with get_connection() as conn:
        # READ + FILTER/SORT EXAMPLE: user-controlled SQL filtering and sorting
        return conn.execute(
            f"""
            SELECT p.*,
                   u.username AS merchant_username,
                   GROUP_CONCAT(pc.color_name, ', ') AS colors
            FROM products p
            JOIN users u ON u.id = p.merchant_id
            LEFT JOIN product_colors pc ON pc.product_id = p.id
            {where_sql}
            GROUP BY p.id
            ORDER BY {order_clause}
            """,
            params,
        ).fetchall()


def get_distinct_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]


def get_distinct_colors() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT color_name FROM product_colors ORDER BY color_name"
        ).fetchall()
        return [r["color_name"] for r in rows]


def get_product_detail(product_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, u.username AS merchant_username
            FROM products p
            JOIN users u ON u.id = p.merchant_id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()
        if not row:
            return None
        colors = get_product_colors(product_id)
        detail = dict(row)
        detail["colors"] = colors
        return detail  # type: ignore[return-value]


def create_order_for_product(
    buyer_id: int,
    product_id: int,
    color_name: str,
    quantity: int,
    shipping_address: str,
    buyer_note: str,
) -> Tuple[bool, str, Optional[int], Optional[int]]:
    with get_connection() as conn:
        try:
            conn.execute("BEGIN")
            product = conn.execute(
                "SELECT * FROM products WHERE id = ? AND is_active = 1",
                (product_id,),
            ).fetchone()
            if not product:
                conn.rollback()
                return False, "Product not found or inactive.", None, None

            if quantity <= 0:
                conn.rollback()
                return False, "Quantity must be at least 1.", None, None

            if quantity > product["stock_quantity"]:
                conn.rollback()
                return False, "Not enough stock available.", None, None

            valid_colors = conn.execute(
                "SELECT color_name FROM product_colors WHERE product_id = ?",
                (product_id,),
            ).fetchall()
            valid_color_list = [c["color_name"] for c in valid_colors]
            if valid_color_list and color_name not in valid_color_list:
                conn.rollback()
                return False, "Please select a valid color.", None, None

            unit_price = float(product["price"])
            subtotal = unit_price * quantity

            # CREATE EXAMPLE: create order + order item records
            order_cursor = conn.execute(
                """
                INSERT INTO orders (buyer_id, total_price, shipping_address, buyer_note, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (buyer_id, subtotal, shipping_address.strip(), buyer_note.strip(), now_iso()),
            )
            order_id = int(order_cursor.lastrowid)

            conn.execute(
                """
                INSERT INTO order_items (
                    order_id, product_id, color_name, quantity, unit_price, subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, product_id, color_name or None, quantity, unit_price, subtotal),
            )

            new_stock = int(product["stock_quantity"]) - quantity
            # UPDATE EXAMPLE: inventory update after purchase
            conn.execute(
                "UPDATE products SET stock_quantity = ?, updated_at = ? WHERE id = ?",
                (new_stock, now_iso(), product_id),
            )
            conn.commit()
            return True, "Purchase successful.", order_id, new_stock
        except sqlite3.Error:
            conn.rollback()
            return False, "Database error during purchase.", None, None


def get_buyer_orders(buyer_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT oi.id,
                   o.id AS order_id,
                   o.created_at,
                   o.shipping_address,
                   o.buyer_note,
                   oi.product_id,
                   p.name AS product_name,
                   oi.color_name,
                   oi.quantity,
                   oi.unit_price,
                   oi.subtotal
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.buyer_id = ?
            ORDER BY o.created_at DESC
            """,
            (buyer_id,),
        ).fetchall()


def get_order_summary_for_buyer(order_id: int, buyer_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT o.id, o.total_price, o.created_at, u.username AS buyer_username
            FROM orders o
            JOIN users u ON u.id = o.buyer_id
            WHERE o.id = ? AND o.buyer_id = ?
            """,
            (order_id, buyer_id),
        ).fetchone()
