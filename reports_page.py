from flask import Blueprint, render_template_string, url_for
import sqlite3
from products_db import init_db
from sales_db import init_sales_db

reports_page = Blueprint("reports_page", __name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reports & Dashboard - EFITE Business ERP</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f3f5f9;color:#222}
header{background:#17365d;color:white;padding:20px}
main{max-width:1000px;margin:20px auto;padding:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}
.card,.panel{background:white;padding:18px;border-radius:10px;margin-bottom:16px}
.value{font-size:26px;font-weight:bold;margin:10px 0}
small{color:#666}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px;border-bottom:1px solid #ddd}
.panel{overflow-x:auto}
a{color:#176b45}
header a{color:white}
.low{color:#a52a2a;font-weight:bold}
</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Reports & Business Dashboard</p>
<a href="{{ url_for('dashboard') }}">← Back to Main Dashboard</a>
</header>
<main>
<h2>Business Overview</h2>
<div class="grid">
<div class="card"><small>Total Sales Revenue</small><div class="value">{{ "%.2f"|format(revenue) }}</div></div>
<div class="card"><small>Sales Transactions</small><div class="value">{{ sales_count }}</div></div>
<div class="card"><small>Units Sold</small><div class="value">{{ units_sold }}</div></div>
<div class="card"><small>Products in Catalog</small><div class="value">{{ product_count }}</div></div>
<div class="card"><small>Units in Stock</small><div class="value">{{ stock_units }}</div></div>
<div class="card"><small>Low-stock Products</small><div class="value">{{ low_stock|length }}</div></div>
</div>

<div class="panel">
<h3>Inventory Status</h3>
<table>
<thead><tr><th>Product</th><th>SKU</th><th>Stock</th><th>Unit Price</th><th>Status</th></tr></thead>
<tbody>
{% for p in products %}
<tr>
<td>{{ p['name'] }}</td>
<td>{{ p['sku'] }}</td>
<td>{{ p['quantity'] }}</td>
<td>{{ "%.2f"|format(p['price']|float) }}</td>
<td>{% if p['quantity']|int <= 5 %}<span class="low">Low stock</span>{% else %}In stock{% endif %}</td>
</tr>
{% else %}
<tr><td colspan="5">No products found.</td></tr>
{% endfor %}
</tbody>
</table>
</div>

<div class="panel">
<h3>Recent Sales</h3>
<table>
<thead><tr><th>Date</th><th>Product</th><th>Quantity</th><th>Total</th></tr></thead>
<tbody>
{% for s in recent_sales %}
<tr><td>{{ s['sale_date'] }}</td><td>{{ s['product_name'] }}</td><td>{{ s['quantity'] }}</td><td>{{ "%.2f"|format(s['total']) }}</td></tr>
{% else %}
<tr><td colspan="4">No sales recorded yet.</td></tr>
{% endfor %}
</tbody>
</table>
</div>

<p>
<a href="{{ url_for('sales_page.sales') }}">Open Sales</a> |
<a href="{{ url_for('inventory_page.inventory') }}">Open Inventory</a> |
<a href="{{ url_for('products.products') }}">Open Products</a>
</p>
</main>
</body>
</html>
"""

@reports_page.route("/module/reports")
def reports():
    init_db()
    init_sales_db()

    with sqlite3.connect("efite.db") as con:
        con.row_factory = sqlite3.Row

        product_rows = con.execute(
            "SELECT id, name, sku, price, quantity FROM products ORDER BY name"
        ).fetchall()

        summary = con.execute("""
            SELECT COUNT(*) AS sales_count,
                   COALESCE(SUM(quantity), 0) AS units_sold,
                   COALESCE(SUM(total), 0) AS revenue
            FROM sales
        """).fetchone()

        recent_rows = con.execute("""
            SELECT sale_date, product_name, quantity, total
            FROM sales ORDER BY id DESC LIMIT 10
        """).fetchall()

    products = [dict(p) for p in product_rows]
    recent_sales = [dict(s) for s in recent_rows]
    low_stock = [p for p in products if int(p["quantity"]) <= 5]

    return render_template_string(
        TEMPLATE,
        products=products,
        recent_sales=recent_sales,
        low_stock=low_stock,
        product_count=len(products),
        stock_units=sum(int(p["quantity"]) for p in products),
        sales_count=summary["sales_count"],
        units_sold=summary["units_sold"],
        revenue=summary["revenue"]
    )
