# QuickSell - MiniShop

MiniShop is a full-stack FastAPI + SQLite assignment project that simulates a simple e-commerce app.
It is intentionally small and readable: merchants manage products, buyers browse and purchase.

## Project Purpose

This project demonstrates SQLite database fundamentals for course grading:
- Create records
- Read records
- Update records
- Delete records
- User-controlled filtering and sorting queries

## Tech Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite (`minishop.db`)
- **Frontend:** Jinja2 templates + HTML/CSS/vanilla JavaScript
- **No React/Vue used**

## Folder Structure

```text
QuickSell/
├── app/
│   ├── __init__.py
│   ├── database.py          # SQLite connection, schema creation, seed data
│   └── crud.py              # SQL operations (CRUD + filter/sort queries)
├── static/
│   ├── css/
│   │   └── styles.css       # UI design with required palette
│   └── js/
│       └── main.js          # color selection + purchase feedback/stock updates
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── merchant_dashboard.html
│   ├── product_form.html
│   ├── buyer_products.html
│   ├── product_detail.html
│   ├── buyer_orders.html
│   └── order_confirmation.html
├── main.py                  # FastAPI routes and page flows
├── requirements.txt
├── .gitignore
└── README.md
```

## Database Schema

The app uses these tables:
- `users` (`id`, `username`, `role`, `created_at`)
- `products` (`id`, `merchant_id`, `name`, `description`, `price`, `stock_quantity`, `category`, `image_url`, `is_active`, `created_at`, `updated_at`)
- `product_colors` (`id`, `product_id`, `color_name`)
- `orders` (`id`, `buyer_id`, `total_price`, `created_at`)
- `order_items` (`id`, `order_id`, `product_id`, `color_name`, `quantity`, `unit_price`, `subtotal`)

Schema is created automatically at app startup in `app/database.py`.

## Assignment Evidence (CRUD + Filter/Sort)

### Create
- User creation on login if username does not exist: `app/crud.py` -> `create_user()`
- Merchant adds product: `app/crud.py` -> `create_product()`
- Buyer purchase creates order + order_item: `app/crud.py` -> `create_order_for_product()`

### Read
- Buyer product listing: `app/crud.py` -> `list_products()`
- Merchant product list: `app/crud.py` -> `get_merchant_products()`
- Buyer order history: `app/crud.py` -> `get_buyer_orders()`
- Merchant sales history: `app/crud.py` -> `get_merchant_sales_history()`

### Update
- Merchant edits products + colors: `app/crud.py` -> `update_product()`
- Merchant toggles active/inactive: `app/crud.py` -> `toggle_product_active()`
- Purchase updates inventory immediately: `app/crud.py` -> `create_order_for_product()`

### Delete
- Merchant deletes products: `app/crud.py` -> `delete_product()`

### Filter/Sort Query
- User-controlled search/filter/sort query:
  - `q` (name search)
  - `category` filter
  - `color` filter
  - `sort` by newest / price asc / price desc
- Implemented in `app/crud.py` -> `list_products()`

## Features

### Authentication / Role Selection
- Simple login form with `username + role`
- Existing usernames preserve their role
- Session-based login

### Merchant
- Add, edit, delete products
- Update inventory quantity
- Manage color options
- Toggle product active/inactive
- View only own products
- View sales history and summary metrics
- Low-stock warning (`<= 5`)

### Buyer
- Browse active products
- Search, filter, and sort products
- View product detail
- Select color and quantity
- Purchase product
- Immediate stock update (SQLite write + frontend update)
- View purchase history
- Order confirmation page

## UI / Design Notes

The app uses the required palette consistently:
- `#ddd8c4`
- `#a3c9a8`
- `#84b59f`
- `#69a297`
- `#50808e`

Applied across backgrounds, cards, buttons, badges, hovers, and accents for a soft modern style.

## Demo Seed Data

Automatically seeded on first startup:
- 2 merchants: `alice_store`, `greenlane_shop`
- 2 buyers: `brian_buyer`, `nina_buyer`
- 8 products across categories:
  - Clothing
  - Accessories
  - Home
  - Tech
- Multiple color choices per product

## Setup and Run

### 1) Create virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Start the app

```bash
uvicorn main:app --reload
```

### 4) Open in browser

```text
http://127.0.0.1:8000
```

## Sample Workflows

### Merchant flow
1. Login with username `alice_store` and role `merchant`
2. Open dashboard
3. Add a product with colors
4. Edit stock and details
5. Toggle active/inactive
6. Delete a product
7. Check sales history after buyer purchases

### Buyer flow
1. Login with username `brian_buyer` and role `buyer`
2. Browse products
3. Search/filter/sort (category, color, price)
4. Open product detail and choose color + quantity
5. Purchase
6. See stock update immediately
7. Open purchase history / confirmation

## Notes for Grading

- SQLite is actively used for all app data.
- Multiple related tables demonstrate relational design.
- CRUD + filter/sort are explicit in code and in this README.
- Project runs locally with minimal setup and clear structure.