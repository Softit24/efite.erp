from settings_page import settings_bp
from customers_page import customers_page
import sqlite3
from flask import Flask, render_template_string, abort, url_for, redirect

app = Flask(__name__)
app.register_blueprint(settings_bp, url_prefix="/settings")

from front_cms import front_cms
app.register_blueprint(front_cms)

from support_page import support_page
app.register_blueprint(support_page)

from token_page import token_page
app.secret_key = __import__("secrets").token_hex(32)
app.register_blueprint(token_page)
from expense_page import expense_page
from profit_loss_page import profit_loss_page
from income_page import income_page
from users_page import users_page
app.register_blueprint(users_page)
app.register_blueprint(income_page)
app.register_blueprint(expense_page)
app.register_blueprint(profit_loss_page)

from products_page import products_page
app.register_blueprint(products_page)
from category_page import category_page
app.register_blueprint(category_page)
from inventory_page import inventory_page
app.register_blueprint(inventory_page)
from sales_page import sales_page
app.register_blueprint(sales_page)
from reports_page import reports_page
app.register_blueprint(reports_page)
app.register_blueprint(customers_page)
from crm_page import crm_page, init_crm_db
app.register_blueprint(crm_page)
init_crm_db()





MODULES = [
    ("front-cms", "Front CMS", "Manage your public website"),
    ("products", "Products", "Manage your products"),
    ("category", "Category", "Organize product categories"),
    ("inventory", "Inventory", "Manage stock"),
    ("sales", "Sales", "Orders and invoices"),
    ("reports", "Reports", "Business reports"),
    ("users", "Users", "Admin, EME and Customer"),
    ("token", "Token", "Customer requests"),
    ("support", "Support", "Support and solutions"),
    ("income", "Income", "Money received"),
    ("expense", "Expense", "Business expenses"),
    ("profit-loss", "Profit & Loss", "Income, expenses and net profit"),
    ("crm", "CRM", "Manage customer relationships"),
    ("settings", "Settings", "Business and system configuration"),
]

BASE_STYLE = """
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5f4;
    color: #18332b;
}
header {
    background: #173c35;
    color: white;
    padding: 24px 18px;
}
header h2 { margin: 0 0 8px; }
header p { margin-bottom: 0; }
main {
    padding: 16px;
    max-width: 900px;
    margin: auto;
}
.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.card {
    display: block;
    background: white;
    padding: 18px 12px;
    border-radius: 12px;
    box-shadow: 0 2px 8px #00000010;
    text-decoration: none;
    color: #18332b;
}
.card strong {
    display: block;
    margin-bottom: 8px;
}
.card span {
    font-size: 13px;
    color: #66766e;
}
.card:active { background: #e4eee9; }
.back {
    display: inline-block;
    margin: 8px 0 20px;
    color: #176b50;
    font-weight: bold;
    text-decoration: none;
}
.panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px #00000010;
}
footer {
    text-align: center;
    padding: 20px;
    color: #66766e;
    font-size: 13px;
}
@media (max-width: 360px) {
    .grid { grid-template-columns: 1fr; }
}
"""

@app.route("/")
def dashboard():
    conn = sqlite3.connect("efite.db")
    try:
        sales_income = conn.execute("SELECT COALESCE(SUM(total), 0) FROM sales").fetchone()[0]
        other_income = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM income").fetchone()[0]
        total_income = sales_income + other_income
        total_expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]
    finally:
        conn.close()
    net_profit = total_income - total_expenses

    conn = sqlite3.connect("efite.db")
    try:
        total_products = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        total_stock_units = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM products"
        ).fetchone()[0]
        total_sales = conn.execute(
            "SELECT COALESCE(SUM(total), 0) FROM sales"
        ).fetchone()[0]
    finally:
        conn.close()

    currency = "BDT"
    try:
        with sqlite3.connect("efite.db") as conn:
            row = conn.execute(
                "SELECT currency FROM system_preferences WHERE id=1"
            ).fetchone()
            if row and row[0]:
                currency = row[0]
    except sqlite3.OperationalError:
        pass

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>EFITE Business ERP - Dashboard</title>
        <style>{{ style }}</style>
    <style>
      .app-layout { display:flex; min-height:100vh; }
      .sidebar { width:220px; flex-shrink:0; background:#173c35; color:white; padding:20px 12px; }
      .sidebar h3 { margin:0 0 20px; padding:0 8px; }
      .sidebar nav { display:flex; flex-direction:column; gap:5px; }
      .sidebar a { color:white; text-decoration:none; padding:12px 10px; border-radius:8px; }
      .sidebar a:hover { background:#28584d; }
      .main-area { min-width:0; flex:1; }
      @media(max-width:650px) {
        .app-layout { flex-direction:column; }
        .sidebar { width:100%; padding:12px; }
        .sidebar h3 { margin-bottom:10px; }
        .sidebar nav { flex-direction:row; flex-wrap:wrap; }
        .sidebar a { padding:9px; }
      }
    </style>
    </head>
    <body>
    <div class="app-layout">
      <aside class="sidebar">
        <h3>EFITE ERP</h3>
        <nav>
          {% for slug, name, description in modules %}
          <a href="{{ url_for('module_page', slug=slug) }}">{{ name }}</a>
          {% endfor %}
        </nav>
      </aside>
      <div class="main-area">
        <header>
            <h2>EFITE Business ERP</h2>
            <p>Business Management System</p>
        </header>
        <main>
            <h3>Dashboard</h3>
            <div class="grid">
              <div class="card"><strong>Total Income</strong><span>{{ currency }} {{ "%.2f"|format(total_income) }}</span></div>
              <div class="card"><strong>Total Expenses</strong><span>{{ currency }} {{ "%.2f"|format(total_expenses) }}</span></div>
              <div class="card"><strong>Net Profit / Loss</strong><span>{{ currency }} {{ "%.2f"|format(net_profit) }}</span></div>
        <div class="card"><strong>Total Products</strong><span>{{ total_products }}</span></div>
        <div class="card"><strong>Total Stock Units</strong><span>{{ total_stock_units }}</span></div>
        <div class="card"><strong>Total Sales</strong><span>{{ currency }} {{ "%.2f"|format(total_sales) }}</span></div>
                {% for slug, name, description in modules %}
                <a class="card"
                   href="{{ url_for('module_page', slug=slug) }}">
                    <strong>{{ name }}</strong>
                    <span>{{ description }}</span>
                </a>
                {% endfor %}
            </div>
        
            <section style="text-align:center; margin:32px auto; padding:24px; background:#f4f8f6; border-radius:14px;">
                
                <div style="display:flex; align-items:center; justify-content:center; gap:14px; flex-wrap:wrap;">
                    <img src="{{ url_for('static', filename='images/efite-logo.png') }}"
         alt="EFITE IT Logo"
         style="display:block;width:100%;max-width:460px;max-height:240px;object-fit:contain;margin:0 auto;">
                    <div style="text-align:left;">
                        <div style="font-size:36px; font-weight:800; letter-spacing:2px; color:#173c35;">EFITE IT</div>
                        <div style="font-size:15px; letter-spacing:2px; color:#39834b;">Business Solutions</div>
                    </div>
                </div>

                
                <h3>CEO: Md. Mizanur Rahman</h3>
                <p>Email: <a href="mailto:ceomizan1971@gmail.com">ceomizan1971@gmail.com</a></p>
            </section>
</main>
        <footer style="text-align:center;">Powered by: Evergreen Freelance IT &amp; Electronics</footer>
      </div>
    </div>
    </body>
    </html>
    """, modules=MODULES, style=BASE_STYLE, total_income=total_income, total_expenses=total_expenses, net_profit=net_profit, total_products=total_products, total_stock_units=total_stock_units, total_sales=total_sales, currency=currency)


@app.route("/module/<slug>")
def module_page(slug):
    if slug == "settings":
        return redirect(url_for("settings.general"))
    if slug == "crm":
        return redirect(url_for("crm.crm_home"))

    selected = next(
        (m for m in MODULES if m[0] == slug), None
    )

    if selected is None:
        abort(404)

    slug, name, description = selected

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>{{ name }} - EFITE Business ERP</title>
        <style>{{ style }}</style>
    </head>
    <body>
        <header>
            <h2>EFITE Business ERP</h2>
            <p>Business Management System</p>
        </header>
        <main>
            <a class="back" href="{{ url_for('dashboard') }}">
                &larr; Back to Dashboard
            </a>
            <div class="panel">
                <h3>{{ name }}</h3>
                <p>{{ description }}</p>
                <p>This module page is ready for development.</p>
            </div>
        </main>
        <footer>EFITE Business ERP</footer>
    </body>
    </html>
    """, name=name, description=description, style=BASE_STYLE)


@app.errorhandler(404)
def page_not_found(error):
    return render_template_string("""
    <h2>Page not found</h2>
    <p>The requested page does not exist.</p>
    <a href="{{ url_for('dashboard') }}">Return to Dashboard</a>
    """), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
