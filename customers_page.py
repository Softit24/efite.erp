import sqlite3
from flask import Blueprint, request, redirect, url_for, render_template_string, flash

customers_page = Blueprint("customers_page", __name__)
DB_NAME = "efite.db"


def init_customers_db():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Customer Management - EFITE ERP</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f3f5f9;color:#222}
header{background:#17365d;color:white;padding:18px}
main{max-width:1000px;margin:20px auto;padding:16px}
.panel{background:white;padding:18px;border-radius:10px;margin-bottom:18px}
form .fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
input,textarea{box-sizing:border-box;width:100%;padding:11px;border:1px solid #ccc;border-radius:6px;margin:5px 0 12px}
button,.btn{display:inline-block;background:#176b45;color:white;padding:10px 14px;border:0;border-radius:6px;text-decoration:none;cursor:pointer}
.delete{background:#a52a2a}
.back{color:#176b45}
table{width:100%;border-collapse:collapse;min-width:650px}
th,td{text-align:left;padding:10px;border-bottom:1px solid #ddd}
.table-wrap{overflow-x:auto}
.notice{padding:10px;background:#e5f5e9;border-radius:6px;margin:12px 0}
.actions{display:flex;gap:8px;align-items:center}
.actions form{margin:0}
</style>
</head>
<body>
<header><h2>EFITE Business ERP</h2><p>Customer Management</p></header>
<main>
<a class="back" href="/">← Back to Dashboard</a>
{% with messages = get_flashed_messages() %}
{% for message in messages %}<div class="notice">{{ message }}</div>{% endfor %}
{% endwith %}
<div class="panel">
<h3>{{ 'Edit Customer' if customer else 'Add New Customer' }}</h3>
<form method="post" action="{{ url_for('customers_page.save_customer') }}">
<input type="hidden" name="id" value="{{ customer.id if customer else '' }}">
<div class="fields">
<div><label>Customer Name *</label><input name="name" required maxlength="150" value="{{ customer.name if customer else '' }}"></div>
<div><label>Phone Number</label><input name="phone" maxlength="50" value="{{ customer.phone if customer else '' }}"></div>
<div><label>Email Address</label><input name="email" type="email" maxlength="150" value="{{ customer.email if customer else '' }}"></div>
</div>
<label>Address</label><textarea name="address" rows="2" maxlength="500">{{ customer.address if customer else '' }}</textarea>
<button type="submit">{{ 'Update Customer' if customer else 'Save Customer' }}</button>
{% if customer %}<a class="btn" href="{{ url_for('customers_page.customers') }}">Cancel</a>{% endif %}
</form>
</div>
<div class="panel">
<h3>Customer List ({{ customers|length }})</h3>
<div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Name</th><th>Phone</th><th>Email</th><th>Address</th><th>Actions</th></tr></thead>
<tbody>
{% for c in customers %}
<tr>
<td>{{ c.id }}</td><td>{{ c.name }}</td><td>{{ c.phone }}</td><td>{{ c.email }}</td><td>{{ c.address }}</td>
<td><div class="actions">
<a class="btn" href="{{ url_for('customers_page.customers', edit=c.id) }}">Edit</a>
<form method="post" action="{{ url_for('customers_page.delete_customer', customer_id=c.id) }}" onsubmit="return confirm('Delete this customer?')"><button class="delete" type="submit">Delete</button></form>
</div></td>
</tr>
{% else %}
<tr><td colspan="6">No customers added yet.</td></tr>
{% endfor %}
</tbody></table></div>
</div>
</main>
</body></html>
"""


@customers_page.route("/module/customers", methods=["GET"])
def customers():
    init_customers_db()
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        customers_list = [dict(row) for row in rows]
        customer_id = request.args.get("edit", type=int)
        customer = None
        if customer_id:
            row = con.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
            customer = dict(row) if row else None
    return render_template_string(PAGE, customers=customers_list, customer=customer)


@customers_page.route("/customers/save", methods=["POST"])
def save_customer():
    init_customers_db()
    customer_id = request.form.get("id", "").strip()
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        flash("Customer name is required.")
        return redirect(url_for("customers_page.customers"))

    with sqlite3.connect(DB_NAME) as con:
        if customer_id:
            con.execute(
                "UPDATE customers SET name=?, phone=?, email=?, address=? WHERE id=?",
                (name, phone, email, address, customer_id)
            )
            flash("Customer updated.")
        else:
            con.execute(
                "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
                (name, phone, email, address)
            )
            flash("Customer saved.")
    return redirect(url_for("customers_page.customers"))


@customers_page.route("/customers/delete/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):
    init_customers_db()
    with sqlite3.connect(DB_NAME) as con:
        con.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    flash("Customer deleted.")
    return redirect(url_for("customers_page.customers"))


init_customers_db()
