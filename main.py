from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import crud
from app.database import init_db


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="QuickSell")
app.add_middleware(SessionMiddleware, secret_key="minishop-course-demo-secret")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def startup() -> None:
    init_db()


def flash(request: Request, level: str, text: str) -> None:
    request.session["flash"] = {"level": level, "text": text}


def pop_flash(request: Request):
    return request.session.pop("flash", None)


def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return crud.get_user_by_id(int(user_id))


def render(request: Request, template_name: str, context: dict):
    base_context = {
        "request": request,
        "current_user": current_user(request),
        "flash_message": pop_flash(request),
    }
    base_context.update(context)
    return templates.TemplateResponse(template_name, base_context)


def redirect(url: str, status_code: int = 303):
    return RedirectResponse(url=url, status_code=status_code)


def require_role(request: Request, role: str):
    user = current_user(request)
    if not user or user["role"] != role:
        return None
    return user


@app.get("/")
def home(request: Request):
    return render(request, "home.html", {})


@app.get("/login")
def login_page(request: Request):
    return render(request, "login.html", {})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    role: str = Form(...),
):
    username = username.strip()
    if not username:
        flash(request, "error", "Username is required.")
        return redirect("/login")

    if role not in {"merchant", "buyer"}:
        flash(request, "error", "Invalid role selection.")
        return redirect("/login")

    existing = crud.get_user_by_username(username)
    if existing and existing["role"] != role:
        flash(request, "error", "Username exists with a different role. Try another name.")
        return redirect("/login")

    user = existing or crud.create_user(username, role)
    request.session["user_id"] = user["id"]
    flash(request, "success", f"Welcome, {user['username']}!")

    if role == "merchant":
        return redirect("/merchant/dashboard")
    return redirect("/buyer/products")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect("/")


@app.get("/merchant/dashboard")
def merchant_dashboard(request: Request):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    products = crud.get_merchant_products(user["id"])
    sales = crud.get_merchant_sales_history(user["id"])
    total_units = sum(item["quantity"] for item in sales)
    total_revenue = sum(item["subtotal"] for item in sales)
    low_stock_count = sum(1 for p in products if p["stock_quantity"] <= 5)

    return render(
        request,
        "merchant_dashboard.html",
        {
            "products": products,
            "sales": sales[:8],
            "total_units": total_units,
            "total_revenue": total_revenue,
            "low_stock_count": low_stock_count,
        },
    )


@app.get("/merchant/products/new")
def new_product_page(request: Request):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")
    return render(
        request,
        "product_form.html",
        {"page_title": "Add Product", "product": None, "color_csv": ""},
    )


@app.post("/merchant/products/new")
def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock_quantity: int = Form(...),
    category: str = Form(""),
    image_url: str = Form(""),
    is_active: Optional[str] = Form(None),
    colors: str = Form(""),
):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    form_data = {
        "name": name.strip(),
        "description": description.strip(),
        "price": price,
        "stock_quantity": stock_quantity,
        "category": category.strip(),
        "image_url": image_url.strip(),
        "is_active": is_active,
    }
    if not form_data["name"]:
        flash(request, "error", "Product name is required.")
        return redirect("/merchant/products/new")

    crud.create_product(user["id"], form_data, colors)
    flash(request, "success", "Product created.")
    return redirect("/merchant/dashboard")


@app.get("/merchant/products/{product_id}/edit")
def edit_product_page(request: Request, product_id: int):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    product = crud.get_product_for_merchant(product_id, user["id"])
    if not product:
        flash(request, "error", "Product not found.")
        return redirect("/merchant/dashboard")
    colors = crud.get_product_colors(product_id)
    return render(
        request,
        "product_form.html",
        {"page_title": "Edit Product", "product": product, "color_csv": ", ".join(colors)},
    )


@app.post("/merchant/products/{product_id}/edit")
def edit_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock_quantity: int = Form(...),
    category: str = Form(""),
    image_url: str = Form(""),
    is_active: Optional[str] = Form(None),
    colors: str = Form(""),
):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    ok = crud.update_product(
        product_id,
        user["id"],
        {
            "name": name.strip(),
            "description": description.strip(),
            "price": price,
            "stock_quantity": stock_quantity,
            "category": category.strip(),
            "image_url": image_url.strip(),
            "is_active": is_active,
        },
        colors,
    )
    if not ok:
        flash(request, "error", "Could not update product.")
    else:
        flash(request, "success", "Product updated.")
    return redirect("/merchant/dashboard")


@app.post("/merchant/products/{product_id}/delete")
def remove_product(request: Request, product_id: int):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    deleted = crud.delete_product(product_id, user["id"])
    if deleted:
        flash(request, "success", "Product deleted.")
    else:
        flash(request, "error", "Product not found or not allowed.")
    return redirect("/merchant/dashboard")


@app.post("/merchant/products/{product_id}/toggle-active")
def toggle_active(request: Request, product_id: int):
    user = require_role(request, "merchant")
    if not user:
        flash(request, "error", "Please sign in as a merchant.")
        return redirect("/login")

    ok = crud.toggle_product_active(product_id, user["id"])
    if ok:
        flash(request, "success", "Product active status updated.")
    else:
        flash(request, "error", "Could not update active status.")
    return redirect("/merchant/dashboard")


@app.get("/buyer/products")
def buyer_products(
    request: Request,
    q: str = "",
    category: str = "",
    color: str = "",
    sort: str = "newest",
):
    user = require_role(request, "buyer")
    if not user:
        flash(request, "error", "Please sign in as a buyer.")
        return redirect("/login")

    products = crud.list_products(q=q.strip(), category=category, color=color, sort=sort)
    categories = crud.get_distinct_categories()
    colors = crud.get_distinct_colors()
    return render(
        request,
        "buyer_products.html",
        {
            "products": products,
            "categories": categories,
            "colors": colors,
            "q": q,
            "selected_category": category,
            "selected_color": color,
            "selected_sort": sort,
        },
    )


@app.get("/buyer/products/{product_id}")
def product_detail(request: Request, product_id: int):
    user = require_role(request, "buyer")
    if not user:
        flash(request, "error", "Please sign in as a buyer.")
        return redirect("/login")

    product = crud.get_product_detail(product_id)
    if not product or not product["is_active"]:
        flash(request, "error", "Product is not available.")
        return redirect("/buyer/products")

    return render(request, "product_detail.html", {"product": product})


@app.post("/buyer/products/{product_id}/purchase")
def purchase_product(
    request: Request,
    product_id: int,
    color_name: str = Form(""),
    quantity: int = Form(...),
):
    user = require_role(request, "buyer")
    if not user:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse({"ok": False, "message": "Please log in as buyer."}, status_code=401)
        flash(request, "error", "Please sign in as a buyer.")
        return redirect("/login")

    ok, message, order_id, new_stock = crud.create_order_for_product(
        user["id"], product_id, color_name.strip(), quantity
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        status = 200 if ok else 400
        return JSONResponse(
            {"ok": ok, "message": message, "order_id": order_id, "new_stock": new_stock},
            status_code=status,
        )

    if not ok:
        flash(request, "error", message)
        return redirect(f"/buyer/products/{product_id}")

    flash(request, "success", "Purchase completed.")
    return redirect(f"/buyer/orders/{order_id}/confirmation")


@app.get("/buyer/orders")
def buyer_orders(request: Request):
    user = require_role(request, "buyer")
    if not user:
        flash(request, "error", "Please sign in as a buyer.")
        return redirect("/login")
    orders = crud.get_buyer_orders(user["id"])
    return render(request, "buyer_orders.html", {"orders": orders})


@app.get("/buyer/orders/{order_id}/confirmation")
def order_confirmation(request: Request, order_id: int):
    user = require_role(request, "buyer")
    if not user:
        flash(request, "error", "Please sign in as a buyer.")
        return redirect("/login")
    summary = crud.get_order_summary_for_buyer(order_id, user["id"])
    if not summary:
        flash(request, "error", "Order not found.")
        return redirect("/buyer/orders")
    return render(request, "order_confirmation.html", {"order": summary})
