import sqlite3
from pathlib import Path
from datetime import date
from flask import Blueprint, render_template_string, request

profit_loss_page = Blueprint("profit_loss_page", __name__)
DB_PATH = Path(__file__).resolve().parent / "efite.db"

STYLE = """
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; background: #f1f5f4;
       color: #18332b; margin: 0; }
header { background: #173c35; color: white; padding: 22px 18px; }
main { max-width: 1100px; margin: 25px auto; padding: 0 16px; }
.panel { background: white; padding: 20px; margin: 18px 0;
         border-radius: 10px; box-shadow: 0 2px 8px #00000010; }
.cards { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 14px; }
.metric { padding: 18px; border-radius: 8px; background: #e8efeb; }
.metric h3 { font-size: 14px; margin-top: 0; }
.amount { font-size: 25px; font-weight: bold; overflow-wrap: anywhere; }
.profit { color: #17634e; }
.loss { color: #a33b32; }
input, button { padding: 11px; margin: 6px 4px 6px 0; }
input { max-width: 100%; border: 1px solid #ccd6d1; border-radius: 5px; }
button { background: #173c35; color: white; border: 0; border-radius: 5px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
a { color: #17634e; }
"""
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profit & Loss - EFITE Business ERP</title>
<style>{{ style }}</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Profit & Loss Report</p>
</header>
<main>
<a href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>

<section class="panel">
<h3>Select reporting period</h3>
<form method="get">
<label>From <input type="date" name="start" value="{{ start }}" required></label>
<label>To <input type="date" name="end" value="{{ end }}" required></label>
<button type="submit">Generate Report</button>
</form>
{% if error %}<p>{{ error }}</p>{% endif %}
</section>

{% if not error %}
<section class="panel">
<div class="cards">
<div class="metric">
<h3>Total Income</h3>
<div class="amount">{{ "%.2f"|format(total_income) }}</div>
</div>
<div class="metric">
<h3>Total Expenses</h3>
<div class="amount">{{ "%.2f"|format(total_expenses) }}</div>
</div>
<div class="metric">
<h3>Net {{ "Profit" if net >= 0 else "Loss" }}</h3>
<div class="amount {{ 'profit' if net >= 0 else 'loss' }}">
{{ "%.2f"|format(net|abs) }}
</div>
</div>
</div>
<p>Period: {{ start }} to {{ end }}</p>
</section>

<section class="panel">
<h3>Transaction Summary ({{ records|length }})</h3>
{% if records %}
<div style="overflow-x:auto">
<table>
<thead><tr><th>Date</th><th>Type</th><th>Description</th><th>Method</th><th>Amount</th></tr></thead>
<tbody>
{% for r in records %}
<tr>
<td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td>
<td>{{ r[3] }}</td><td>{{ "%.2f"|format(r[4]) }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<p>No income or expenses found for this period.</p>
{% endif %}
</section>
{% endif %}
</main>
</body>
</html>
"""

@profit_loss_page.get("/module/profit-loss")
def report():
    today = date.today()
    default_start = today.replace(day=1).isoformat()
    start = request.args.get("start", default_start)
    end = request.args.get("end", today.isoformat())
    error = ""

    try:
        date.fromisoformat(start)
        date.fromisoformat(end)
        if start > end:
            raise ValueError
    except ValueError:
        error = "Please choose valid dates. The start date must not be after the end date."

    total_income = 0
    total_expenses = 0
    records = []

    if not error:
        with sqlite3.connect(DB_PATH) as con:
            total_income = con.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM income WHERE income_date BETWEEN ? AND ?",
                (start, end)
            ).fetchone()[0]

            total_expenses = con.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date BETWEEN ? AND ?",
                (start, end)
            ).fetchone()[0]

            records = con.execute("""
                SELECT transaction_date, kind, description, payment_method, amount
                FROM (
                    SELECT income_date AS transaction_date, 'Income' AS kind,
                           description, payment_method, amount, id
                    FROM income WHERE income_date BETWEEN ? AND ?
                    UNION ALL
                    SELECT expense_date AS transaction_date, 'Expense' AS kind,
                           description, payment_method, amount, id
                    FROM expenses WHERE expense_date BETWEEN ? AND ?
                )
                ORDER BY transaction_date DESC, id DESC
            """, (start, end, start, end)).fetchall()

    net = total_income - total_expenses

    return render_template_string(
        TEMPLATE, style=STYLE, start=start, end=end, error=error,
        total_income=total_income, total_expenses=total_expenses,
        net=net, records=records
    )
