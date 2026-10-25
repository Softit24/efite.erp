from flask import Blueprint, request, redirect, render_template_string, url_for
import sqlite3
from products_db import get_products, init_db

inventory_page = Blueprint("inventory_page", __name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inventory - EFITE Business ERP</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f3f5f9;color:#222}
header{background:#17365d;color:white;padding:20px}
main{max-width:950px;margin:20px auto;padding:16px}
.panel{background:white;padding:18px;margin:16px 0;border-radius:10px;overflow-x:auto}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px;border-bottom:1px solid #ddd}
input,button{padding:10px;box-sizing:border-box}
input{width:100%;min-width:75px}
button{background:#176b45;color:white;border:0;border-radius:5px}
.message{color:#176b45}
.low{color:#a52a2a;font-weight:bold}
.back{color:white}
</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Inventory Management</p>
<a class="back" href="{{ url_for('dashboard') }}">← Back to Dashboard</a>
</header>
<main>
<h2>Stock Inventory</h2>
{% if message %}<p class="message">{{ message }}</p>{% endif %}
<div class="panel">
<p><strong>Total products:</strong> {{ products|length }}</p>
<table>
<thead><tr><th>Product</th><th>SKU</th><th>Stock</th><th>Update stock</th></tr></thead>
<tbody>
{% for p in products %}
<tr>
<td>{{ p['name'] }}</td>
<td>{{ p['sku'] }}</td>
<td>{% if p['quantity']|int <= 5 %}<span class="low">{{ p['quantity'] }} (Low stock)</span>{% else %}{{ p['quantity'] }}{% endif %}</td>
<td>
<form method="post" action="{{ url_for('inventory_page.update_stock', product_id=p['id']) }}">
<input type="number" name="quantity" min="0" step="1" value="{{ p['quantity'] }}" required>
<button type="submit">Save</button>
</form>
</td>
</tr>
{% else %}
<tr><td colspan="4">No products found. Add products in the Products module first.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</main>
</body>
</html>
"""

@inventory_page.route("/module/inventory")
def inventory():
    init_db()
    return render_template_string(
        TEMPLATE,
        products=get_products(),
        message=request.args.get("message", "")
    )

@inventory_page.route("/module/inventory/update/<int:product_id>", methods=["POST"])
def update_stock(product_id):
    raw_quantity = request.form.get("quantity", "")
    try:
        quantity = int(raw_quantity)
        if quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        return redirect(url_for("inventory_page.inventory", message="Enter a valid stock quantity."))

    init_db()
    with sqlite3.connect("efite.db") as con:
        cur = con.execute(
            "UPDATE products SET quantity=? WHERE id=?",
            (quantity, product_id)
        )
        if cur.rowcount == 0:
            return redirect(url_for("inventory_page.inventory", message="Product not found."))

    return redirect(url_for("inventory_page.inventory", message="Stock updated successfully."))
