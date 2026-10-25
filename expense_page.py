import sqlite3
from pathlib import Path
from datetime import date
from flask import Blueprint, render_template_string, request, redirect, url_for, flash

expense_page = Blueprint("expense_page", __name__)
DB_PATH = Path(__file__).resolve().parent / "efite.db"


def init_expense_table():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                expense_date TEXT NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'Cash',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_expense_table()

STYLE = """
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; background: #f1f5f4;
       color: #18332b; margin: 0; }
header { background: #173c35; color: white; padding: 22px 18px; }
main { max-width: 1000px; margin: 25px auto; padding: 0 16px; }
.panel { background: white; padding: 20px; margin: 18px 0;
         border-radius: 10px; box-shadow: 0 2px 8px #00000010; }
input, select, button { box-sizing: border-box; padding: 11px;
                         margin: 6px 0; max-width: 100%; }
input, select { width: 100%; border: 1px solid #ccd6d1;
                 border-radius: 5px; }
button { background: #173c35; color: white; border: 0;
         border-radius: 5px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
.notice { padding: 10px; background: #e4eee8; margin: 10px 0; }
.total { font-size: 25px; font-weight: bold; color: #a33b32; }
a { color: #17634e; }
"""

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Expenses - EFITE Business ERP</title>
<style>{{ style }}</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Expense Management</p>
</header>
<main>
<a href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="notice">{{ message }}</div>
{% endfor %}
{% endwith %}

<section class="panel">
<h3>Total Recorded Expenses</h3>
<div class="total">{{ "%.2f"|format(total) }}</div>
</section>

<section class="panel">
<h3>Record Expense</h3>
<form method="post" action="{{ url_for('expense_page.add_expense') }}">
<label>Description</label>
<input name="description" maxlength="200" required
       placeholder="e.g. Rent, transport, supplies">

<label>Amount</label>
<input type="number" name="amount" min="0.01" step="0.01"
       required placeholder="0.00">

<label>Expense date</label>
<input type="date" name="expense_date" required
       value="{{ today }}">

<label>Payment method</label>
<select name="payment_method" required>
<option>Cash</option>
<option>Bank Transfer</option>
<option>Mobile Banking</option>
<option>Card</option>
<option>Other</option>
</select>

<button type="submit">Save Expense</button>
</form>
</section>

<section class="panel">
<h3>Expense History ({{ records|length }})</h3>
{% if records %}
<div style="overflow-x:auto">
<table>
<thead>
<tr><th>Date</th><th>Description</th><th>Method</th><th>Amount</th></tr>
</thead>
<tbody>
{% for record in records %}
<tr>
<td>{{ record[3] }}</td>
<td>{{ record[1] }}</td>
<td>{{ record[4] }}</td>
<td>{{ "%.2f"|format(record[2]) }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<p>No expenses recorded yet.</p>
{% endif %}
</section>
</main>
</body>
</html>
"""


@expense_page.get("/module/expense")
def expenses():
    with sqlite3.connect(DB_PATH) as con:
        records = con.execute("""
            SELECT id, description, amount, expense_date, payment_method
            FROM expenses
            ORDER BY expense_date DESC, id DESC
        """).fetchall()
        total = con.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        ).fetchone()[0]

    return render_template_string(
        TEMPLATE, style=STYLE, records=records,
        total=total, today=date.today().isoformat()
    )


@expense_page.post("/module/expense/add")
def add_expense():
    description = request.form.get("description", "").strip()
    amount_text = request.form.get("amount", "").strip()
    expense_date = request.form.get("expense_date", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    try:
        amount = float(amount_text)
        if not description or len(description) > 200 or amount <= 0:
            raise ValueError
        date.fromisoformat(expense_date)
        if payment_method not in (
            "Cash", "Bank Transfer", "Mobile Banking", "Card", "Other"
        ):
            raise ValueError
    except (ValueError, TypeError):
        flash("Enter a valid description, date, payment method and positive amount.")
        return redirect(url_for("expense_page.expenses"))

    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO expenses
                (description, amount, expense_date, payment_method)
            VALUES (?, ?, ?, ?)
        """, (description, amount, expense_date, payment_method))

    flash("Expense recorded successfully.")
    return redirect(url_for("expense_page.expenses"))
