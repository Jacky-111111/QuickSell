# QuickSell

QuickSell is a course project for demonstrating SQLite CRUD operations in a full-stack web app.
It uses FastAPI + SQLite + Jinja templates (HTML/CSS/JS), with two roles:
- Merchant: manage products and view sales
- Buyer: browse, filter/sort, and purchase products

## Deployment Status

This project is **not deployed online**.
It runs **locally only** on your computer.

## Tech Stack

- Backend: Python + FastAPI
- Database: SQLite (`minishop.db`)
- Frontend: Jinja2 templates + HTML/CSS/vanilla JavaScript
- No React / Vue

## Local Run Guide (Step-by-Step)

> Run each command on its own line.  
> Do not paste all commands into one single line.

### 1) Open project folder

```bash
cd /path/to/QuickSell
```

### 2) Create virtual environment

```bash
python3 -m venv .venv
```

### 3) Activate virtual environment

```bash
source .venv/bin/activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

### 5) Start backend server

```bash
uvicorn main:app --reload
```

### 6) Open website in browser

```text
http://127.0.0.1:8000
```

## Quick Troubleshooting

- If `ModuleNotFoundError: No module named 'itsdangerous'` appears:
  ```bash
  pip install -r requirements.txt
  ```
- If page changes are not visible:
  - restart `uvicorn`
  - hard refresh browser (`Cmd + Shift + R`)

## Project Structure

```text
QuickSell/
├── app/
│   ├── database.py      # SQLite connection, schema creation, seed
│   └── crud.py          # SQL CRUD and filtering/sorting queries
├── templates/           # Server-rendered HTML pages
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── main.py              # FastAPI routes/controllers
├── requirements.txt
└── README.md
```

## SQLite: How It Is Controlled In This Project

SQLite operations are intentionally explicit and easy to inspect.

### 1) Database file and connection

- DB file: `minishop.db` (project root)
- Connection helper: `app/database.py` -> `get_connection()`
- `row_factory` is enabled, so query rows can be accessed by column names.

### 2) Schema creation (table setup)

- Runs at app startup:
  - `main.py` -> `startup()` calls `init_db()`
  - `app/database.py` -> `init_db()` uses `CREATE TABLE IF NOT EXISTS ...`
- Tables:
  - `users`
  - `products`
  - `product_colors`
  - `orders`
  - `order_items`

### 3) Seed/demo data

- `app/database.py` -> `seed_demo_data()`
- Seeds only when `users` table is empty.
- Includes:
  - 2 merchants + 2 buyers
  - 8 products
  - multi-category data (Clothing / Accessories / Home / Tech)
  - product colors

### 4) CRUD operations (where SQL happens)

All major SQL is in `app/crud.py`.

- **Create**
  - `create_user()`
  - `create_product()`
  - `create_order_for_product()` (creates `orders` + `order_items`)
- **Read**
  - `list_products()` (with search/filter/sort)
  - `get_merchant_products()`
  - `get_buyer_orders()`
  - `get_merchant_sales_history()`
- **Update**
  - `update_product()`
  - `toggle_product_active()`
  - `create_order_for_product()` decreases `stock_quantity` after purchase
- **Delete**
  - `delete_product()`

### 5) Filtering / sorting query (grading point)

- Implemented in `app/crud.py` -> `list_products()`
- Supports user-controlled parameters:
  - name search (`q`)
  - category filter
  - color filter
  - sort by newest / price asc / price desc

### 6) Transaction-like purchase flow

In `create_order_for_product()`:
- validate product exists and stock is enough
- insert `orders`
- insert `order_items`
- update `products.stock_quantity`
- commit if success, rollback on DB error

This makes inventory updates consistent with order creation.

## Database Schema (Summary)

- `users`: `id`, `username`, `role`, `created_at`
- `products`: `id`, `merchant_id`, `name`, `description`, `price`, `stock_quantity`, `category`, `image_url`, `is_active`, `created_at`, `updated_at`
- `product_colors`: `id`, `product_id`, `color_name`
- `orders`: `id`, `buyer_id`, `total_price`, `created_at`
- `order_items`: `id`, `order_id`, `product_id`, `color_name`, `quantity`, `unit_price`, `subtotal`

## Demo Accounts

- Merchants: `alice_store`, `greenlane_shop`
- Buyers: `brian_buyer`, `nina_buyer`

## Assignment Evidence Checklist

- SQLite database in active use: yes (`minishop.db`)
- Table with >=4 columns including `id`: yes (`products`, `users`, etc.)
- Full CRUD: yes (`app/crud.py`)
- Read query with user-controlled filter/sort: yes (`list_products()`)
- Interactive local web UI: yes (FastAPI templates + JS)
- Clear local run instructions: yes (this README)