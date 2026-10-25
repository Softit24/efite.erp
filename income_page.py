import sqlite3
from pathlib import Path
from flask import Blueprint, render_template_string, request, redirect, url_for, flash

income_page = Blueprint("income_page", __name__)
DB_PATH = Path(__file__).resolve().parent / "efite.db"


def init_income_table():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                income_date TEXT NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'Cash',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_income_table()

STYLE = """
body { font-family: Arial, sans-serif; background: #f1f5f4;
       color: #18332b; margin: 0; }
header { background: #173c35; color: white; padding: 20px; }
main { max-width: 1000px; margin: 25px auto; padding: 0 16px; }
.panel { background: white; padding: 20px; margin: 18px 0;
         border-radius: 10px; }
input, select, button { box-sizing: border-box; padding: 10px;
                         margin: 6px 0; max-width: 100%; }
input, select { width: 100%; border: 1px solid #ccd6d1;
                 border-radius: 5px; }
button { background: #173c35; color: white; border: 0;
         border-radius: 5px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
.notice { padding: 10px; background: #e4eee8; margin: 10px 0; }
.total { font-size: 24px; font-weight: bold; color: #17634e; }
a { color: #17634e; }
"""

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Income - EFITE Business ERP</title>
<style>{{ style }}</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Income Management</p>
</header>
<main>
<a href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="notice">{{ message }}</div>
{% endfor %}
{% endwith %}

<section class="panel">
<h3>Total Recorded Income</h3>
<div class="total">{{ "%.2f"|format(total) }}</div>
</section>

<section class="panel">
<h3>Record Income</h3>
<form method="post" action="{{ url_for('income_page.add_income') }}">
<label>Description</label>
<input name="description" maxlength="200" required
       placeholder="e.g. Product sale or service payment">

<label>Amount</label>
<input type="number" name="amount" min="0.01" step="0.01"
       required placeholder="0.00">

<label>Income date</label>
<input type="date" name="income_date" required
       value="{{ today }}">

<label>Payment method</label>
<select name="payment_method" required>
<option>Cash</option>
<option>Bank Transfer</option>
<option>Mobile Banking</option>
<option>Card</option>
<option>Other</option>
</select>

<button type="submit">Save Income</button>
</form>
</section>

<section class="panel">
<h3>Income History ({{ records|length }})</h3>
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
<p>No income recorded yet.</p>
{% endif %}
</section>
</main>
</body>
</html>
"""


@income_page.get("/module/income")
def income():
    from datetime import date

    with sqlite3.connect(DB_PATH) as con:
        records = con.execute("""
            SELECT id, description, amount, income_date, payment_method
            FROM income
            ORDER BY income_date DESC, id DESC
        """).fetchall()
        total = con.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM income"
        ).fetchone()[0]

    return render_template_string(
        TEMPLATE, style=STYLE, records=records,
        total=total, today=date.today().isoformat()
    )


@income_page.post("/module/income/add")
def add_income():
    description = request.form.get("description", "").strip()
    amount_text = request.form.get("amount", "").strip()
    income_date = request.form.get("income_date", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    try:
        amount = float(amount_text)
        if not description or len(description) > 200:
            raise ValueError
        if amount <= 0:
            raise ValueError
        from datetime import date
        date.fromisoformat(income_date)
        if payment_method not in (
            "Cash", "Bank Transfer", "Mobile Banking", "Card", "Other"
        ):
            raise ValueError
    except (ValueError, TypeError):
        flash("Please enter valid income details and a positive amount.")
        return redirect(url_for("income_page.income"))

    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO income
                (description, amount, income_date, payment_method)
            VALUES (?, ?, ?, ?)
        """, (description, amount, income_date, payment_method))

    flash("Income recorded successfully.")
    return redirect(url_for("income_page.income"))
