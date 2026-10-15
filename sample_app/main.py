import os
import uuid
import datetime
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="DevStore Controlled Sample E-Commerce App", version="1.0.0")

# Mount static and templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def render_template(request: Request, name: str, context: Optional[Dict[str, Any]] = None) -> HTMLResponse:
    ctx = context or {}
    ctx["request"] = request
    return templates.TemplateResponse(request, name, ctx)

# Initial Synthetic Data
INITIAL_PRODUCTS = [
    {
        "id": "PRD-01",
        "name": "DevPulse Mechanical Keyboard",
        "category": "Hardware",
        "price": 129.99,
        "description": "Custom hot-swappable tactile switches, RGB underglow, aircraft-grade aluminum casing.",
    },
    {
        "id": "PRD-02",
        "name": "UltraWide 4K Coding Monitor",
        "category": "Hardware",
        "price": 449.00,
        "description": "34-inch curved IPS panel, USB-C 90W power delivery, 99% sRGB color accuracy.",
    },
    {
        "id": "PRD-03",
        "name": "Ergonomic Mesh Task Chair",
        "category": "Furniture",
        "price": 289.50,
        "description": "Breathable mesh backing, dynamic lumbar support, 4D adjustable armrests.",
    },
    {
        "id": "PRD-04",
        "name": "Studio ANC Headphones",
        "category": "Audio",
        "price": 199.00,
        "description": "Active noise cancellation tuned for engineering focus, 40-hour battery life.",
    },
    {
        "id": "PRD-05",
        "name": "Thunderbolt 4 Pro Dock",
        "category": "Accessories",
        "price": 149.00,
        "description": "12-in-1 connectivity hub supporting dual 4K 60Hz displays and 10Gbps transfers.",
    },
]

INITIAL_USERS = {
    "tester@apexqa.io": {
        "name": "Alex QA Lead",
        "email": "tester@apexqa.io",
        "password": "Password123!",
        "created_at": "2026-01-15T10:00:00Z"
    }
}

# Runtime In-Memory State
db_products: List[Dict[str, Any]] = [dict(p) for p in INITIAL_PRODUCTS]
db_users: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in INITIAL_USERS.items()}
db_carts: Dict[str, List[Dict[str, Any]]] = {}
db_orders: List[Dict[str, Any]] = []

def get_session_id(request: Request) -> str:
    session_id = request.cookies.get("devstore_session")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    user_email = request.cookies.get("devstore_user")
    if user_email and user_email in db_users:
        return db_users[user_email]
    return None

def get_cart_for_session(session_id: str) -> List[Dict[str, Any]]:
    if session_id not in db_carts:
        db_carts[session_id] = []
    return db_carts[session_id]

def get_cart_count(session_id: str) -> int:
    cart = get_cart_for_session(session_id)
    return sum(item["quantity"] for item in cart)

# ----------------- Seeded Defect Endpoints & Pages -----------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    response = render_template(request, "index.html", {
        "products": db_products,
        "cart_count": get_cart_count(session_id),
        "user": user
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/products", response_class=HTMLResponse)
async def products(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    response = render_template(request, "products.html", {
        "products": db_products,
        "cart_count": get_cart_count(session_id),
        "user": user
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(product_id: str, request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    product = next((p for p in db_products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    response = render_template(request, "product_detail.html", {
        "product": product,
        "cart_count": get_cart_count(session_id),
        "user": user
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    cart = get_cart_for_session(session_id)
    
    # Calculate cart totals
    cart_items = []
    raw_subtotal = 0.0
    for item in cart:
        prod = next((p for p in db_products if p["id"] == item["product_id"]), None)
        if prod:
            line_total = prod["price"] * item["quantity"]
            raw_subtotal += line_total
            cart_items.append({
                "product": prod,
                "quantity": item["quantity"],
                "line_total": line_total
            })

    shipping = 15.00 if cart_items else 0.0
    tax = round(raw_subtotal * 0.08, 2)
    total = raw_subtotal + shipping + tax

    response = render_template(request, "cart.html", {
        "items": cart_items,
        "subtotal": raw_subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "cart_count": sum(i["quantity"] for i in cart_items),
        "user": user
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.post("/cart/add")
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1)
):
    session_id = get_session_id(request)
    cart = get_cart_for_session(session_id)
    
    existing = next((item for item in cart if item["product_id"] == product_id), None)
    if existing:
        existing["quantity"] += quantity
    else:
        cart.append({"product_id": product_id, "quantity": quantity})
        
    response = RedirectResponse(url="/cart", status_code=303)
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.post("/cart/update")
async def update_cart_item(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(...)
):
    session_id = get_session_id(request)
    cart = get_cart_for_session(session_id)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] = max(1, quantity)
            break
    return JSONResponse({"status": "ok", "product_id": product_id, "quantity": quantity})

@app.post("/cart/remove")
async def remove_cart_item(
    request: Request,
    product_id: str = Form(...)
):
    session_id = get_session_id(request)
    cart = get_cart_for_session(session_id)
    db_carts[session_id] = [item for item in cart if item["product_id"] != product_id]
    response = RedirectResponse(url="/cart", status_code=303)
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    cart = get_cart_for_session(session_id)
    
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)

    response = render_template(request, "checkout.html", {
        "default_name": user["name"] if user else "",
        "default_email": user["email"] if user else "",
        "cart_count": get_cart_count(session_id),
        "user": user,
        "error": None
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.post("/checkout")
async def process_checkout(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    postal_code: Optional[str] = Form(None), # SEEDED BUG BUG-03: Not validated as required
    country: str = Form("US"),
    payment_method: str = Form("card")
):
    session_id = get_session_id(request)
    user = get_current_user(request)
    cart = get_cart_for_session(session_id)

    if not cart:
        return RedirectResponse(url="/cart", status_code=303)

    # Note: BUG-03: Required validation for postal_code is intentionally missing!
    subtotal = 0.0
    for item in cart:
        prod = next((p for p in db_products if p["id"] == item["product_id"]), None)
        if prod:
            subtotal += prod["price"] * item["quantity"]
            
    total = subtotal + 15.00 + round(subtotal * 0.08, 2)

    # SEEDED BUG BUG-04: Non-idempotent order placement without duplicate check
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    new_order = {
        "id": order_id,
        "session_id": session_id,
        "fullname": fullname,
        "email": email,
        "address": address,
        "city": city,
        "postal_code": postal_code or "",
        "country": country,
        "payment_method": payment_method,
        "total": total,
        "items": [dict(i) for i in cart],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    db_orders.append(new_order)

    # Empty cart
    db_carts[session_id] = []

    response = RedirectResponse(url=f"/order-confirmation/{order_id}", status_code=303)
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/order-confirmation/{order_id}", response_class=HTMLResponse)
async def order_confirmation(order_id: str, request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    order = next((o for o in db_orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    response = render_template(request, "order_confirmation.html", {
        "order": order,
        "cart_count": get_cart_count(session_id),
        "user": user
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    response = render_template(request, "register.html", {
        "cart_count": get_cart_count(session_id),
        "user": user,
        "error": None,
        "success": None
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.post("/register")
async def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    session_id = get_session_id(request)
    
    if password != confirm_password:
        return render_template(request, "register.html", {
            "cart_count": get_cart_count(session_id),
            "user": None,
            "error": "Passwords do not match.",
            "success": None
        })

    # SEEDED BUG BUG-01: Faulty email validation
    if len(email) < 3:
        return render_template(request, "register.html", {
            "cart_count": get_cart_count(session_id),
            "user": None,
            "error": "Please provide a valid email address.",
            "success": None
        })

    db_users[email] = {
        "name": name,
        "email": email,
        "password": password,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    response = render_template(request, "register.html", {
        "cart_count": get_cart_count(session_id),
        "user": None,
        "error": None,
        "success": f"Account created for {email}! You can now sign in."
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    response = render_template(request, "login.html", {
        "cart_count": get_cart_count(session_id),
        "user": user,
        "error": None
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

@app.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    session_id = get_session_id(request)
    user = db_users.get(email)
    if not user or user["password"] != password:
        return render_template(request, "login.html", {
            "cart_count": get_cart_count(session_id),
            "user": None,
            "error": "Invalid email or password."
        })

    response = RedirectResponse(url="/account", status_code=303)
    response.set_cookie(key="devstore_session", value=session_id)
    response.set_cookie(key="devstore_user", value=email)
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="devstore_user")
    return response

# SEEDED BUG BUG-05: Broken Access Control on /account
@app.get("/account", response_class=HTMLResponse)
async def customer_account(request: Request):
    session_id = get_session_id(request)
    user = get_current_user(request)
    response = render_template(request, "account.html", {
        "user": user,
        "orders": db_orders,
        "cart_count": get_cart_count(session_id)
    })
    response.set_cookie(key="devstore_session", value=session_id)
    return response

# ----------------- Control & Reset Endpoints -----------------

@app.post("/api/reset")
async def reset_demo_state():
    """Resets the demo state back to default synthetic data."""
    global db_products, db_users, db_carts, db_orders
    db_products = [dict(p) for p in INITIAL_PRODUCTS]
    db_users = {k: dict(v) for k, v in INITIAL_USERS.items()}
    db_carts = {}
    db_orders = []
    return {"status": "success", "message": "Demo state reset to synthetic defaults."}

@app.get("/api/state")
async def get_demo_state():
    """Returns state metrics for test oracles and assertions."""
    return {
        "products_count": len(db_products),
        "users_count": len(db_users),
        "orders_count": len(db_orders),
        "carts_active": len(db_carts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5001, reload=True)
