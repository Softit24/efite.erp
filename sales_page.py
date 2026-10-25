from flask import Blueprint, request, redirect, render_template_string, url_for
from products_db import get_products, init_db
from sales_db import get_sales, record_sale

sales_page = Blueprint("sales_page", __name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sales - EFITE Business ERP</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f3f5f9;color:#222}
header{background:#17365d;color:white;padding:20px}
main{max-width:950px;margin:20px auto;padding:16px}
.panel{background:white;padding:18px;margin:16px 0;border-radius:10px;overflow-x:auto}
input,select,button{padding:11px;margin:5px 0;box-sizing:border-box}
input,select{width:100%}
button{background:#176b45;color:white;border:0;border-radius:5px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px;border-bottom:1px solid #ddd}
.message{color:#176b45;font-weight:bold}
.back{color:white}
</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Sales Management</p>
<a class="back" href="{{ url_for('dashboard') }}">← Back to Dashboard</a>
</header>
<main>
<h2>Record a Sale</h2>
{% if message %}<p class="message">{{ message }}</p>{% endif %}
<div class="panel">
<form method="post">
<label>Product</label>
<select name="product_id" required>
{% for p in products %}
<option value="{{ p['id'] }}">{{ p['name'] }} — Stock: {{ p['quantity'] }} — Price: {{ "%.2f"|format(p['price']|float) }}</option>
{% endfor %}
</select>
<label>Quantity sold</label>
<input type="number" name="quantity" min="1" step="1" value="1" required>
<button type="submit" {% if not products %}disabled{% endif %}>Record Sale</button>
{% if not products %}<p>Add a product before recording sales.</p>{% endif %}
</form>
</div>
<h2>Sales History</h2>
<div class="panel">
<p><strong>Total sales revenue:</strong> {{ "%.2f"|format(total_revenue) }}</p>
<table>
<thead><tr><th>Date</th><th>Product</th><th>Quantity</th><th>Unit price</th><th>Total</th></tr></thead>
<tbody>
{% for s in sales %}
<tr>
<td>{{ s['sale_date'] }}</td>
<td>{{ s['product_name'] }}</td>
<td>{{ s['quantity'] }}</td>
<td>{{ "%.2f"|format(s['unit_price']) }}</td>
<td>{{ "%.2f"|format(s['total']) }}</td>
</tr>
{% else %}
<tr><td colspan="5">No sales recorded yet.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</main>
</body>
</html>
"""

@sales_page.route("/module/sales", methods=["GET", "POST"])
def sales():
    init_db()
    message = request.args.get("message", "")
    if request.method == "POST":
        try:
            product_id = int(request.form.get("product_id", ""))
            quantity = int(request.form.get("quantity", ""))
        except (ValueError, TypeError):
            return redirect(url_for("sales_page.sales", message="Enter a valid product and quantity."))

        success, result = record_sale(product_id, quantity)
        return redirect(url_for("sales_page.sales", message=result))

    products = get_products()
    sales_list = get_sales()
    total_revenue = sum(float(s["total"]) for s in sales_list)
    return render_template_string(
        TEMPLATE,
        products=products,
        sales=sales_list,
        total_revenue=total_revenue,
        message=message
    )
