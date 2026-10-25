
import sqlite3
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, render_template_string, flash, current_app

token_page = Blueprint("token_page", __name__)

def get_db():
    # Use the existing ERP database.
    import os
    db_path = os.path.join(os.path.dirname(__file__), "efite.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_token_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_number TEXT UNIQUE,
            customer_name TEXT NOT NULL,
            phone TEXT,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'Waiting',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@token_page.route("/module/token", methods=["GET", "POST"])
def tokens():
    init_token_db()
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        reason = request.form.get("reason", "").strip()

        if not name:
            conn.close()
            return "Customer name is required.", 400

        now = datetime.now()
        token_number = "TK-" + now.strftime("%Y%m%d-%H%M%S-%f")

        conn.execute("""
            INSERT INTO customer_tokens
            (token_number, customer_name, phone, reason, status, created_at)
            VALUES (?, ?, ?, ?, 'Waiting', ?)
        """, (token_number, name, phone, reason, now.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return redirect(url_for("token_page.tokens"))

    search = request.args.get("q", "").strip()
    if search:
        rows = conn.execute("""
            SELECT * FROM customer_tokens
            WHERE token_number LIKE ? OR customer_name LIKE ? OR phone LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM customer_tokens ORDER BY id DESC LIMIT 200
        """).fetchall()

    conn.close()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Token Management - EFITE ERP</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #f3f5f9; color: #172033; }
        header { background: #182848; color: white; padding: 18px 24px; }
        main { max-width: 1100px; margin: 24px auto; padding: 0 16px; }
        .panel { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px #0001; }
        input, textarea, select, button { box-sizing: border-box; padding: 10px; margin: 5px 0; max-width: 100%; }
        input, textarea { width: 100%; }
        button { background: #2463eb; color: white; border: 0; border-radius: 5px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e4e8ef; }
        th { background: #eef2f8; }
        .table-wrap { overflow-x: auto; }
        .back { color: white; }
        @media (max-width: 650px) { th, td { padding: 7px; font-size: 13px; } }
        @media print { header, .form-panel, .search-panel, .back, .actions { display: none; } body { background: white; } .panel { box-shadow: none; } }
      </style>
    </head>
    <body>
      <header>
        <h2>EFITE Business ERP — Token Management</h2>
        <a class="back" href="{{ url_for('dashboard') }}">← Back to Dashboard</a>
      </header>
      <main>
        <section class="panel form-panel">
          <h3>Register Customer</h3>
          <form method="post">
            <label>Customer name *</label>
            <input name="customer_name" required maxlength="150">
            <label>Phone number</label>
            <input name="phone" maxlength="50">
            <label>Reason for visit / request</label>
            <textarea name="reason" rows="2" maxlength="500"></textarea>
            <button type="submit">Generate Token</button>
          </form>
        </section>

        <section class="panel search-panel">
          <h3>Search Tokens</h3>
          <form method="get">
            <input name="q" value="{{ search }}" placeholder="Token number, customer name, or phone">
            <button type="submit">Search</button>
            <a href="{{ url_for('token_page.tokens') }}">Clear</a>
          </form>
        </section>

        <section class="panel">
          <h3>Customer Queue</h3>
          <p>Showing {{ rows|length }} record(s).</p>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Token</th><th>Customer</th><th>Phone</th><th>Reason</th><th>Time</th><th>Status</th><th class="actions">Action</th></tr></thead>
              <tbody>
              {% for r in rows %}
                <tr>
                  <td>{{ r.token_number }}</td>
                  <td>{{ r.customer_name }}</td>
                  <td>{{ r.phone or '' }}</td>
                  <td>{{ r.reason or '' }}</td>
                  <td>{{ r.created_at }}</td>
                  <td>{{ r.status }}</td>
                  <td class="actions">
                    <form method="post" action="{{ url_for('token_page.update_status', token_id=r.id) }}">
                      <select name="status">
                        {% for s in ['Waiting', 'In Progress', 'Completed', 'Cancelled'] %}
                          <option value="{{ s }}" {% if r.status == s %}selected{% endif %}>{{ s }}</option>
                        {% endfor %}
                      </select>
                      <button type="submit">Update</button>
                    </form>
                    <button type="button" onclick="window.print()">Print</button>
                  </td>
                </tr>
              {% else %}
                <tr><td colspan="7">No tokens found.</td></tr>
              {% endfor %}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </body>
    </html>
    """, rows=rows, search=search)

@token_page.route("/module/token/status/<int:token_id>", methods=["POST"])
def update_status(token_id):
    status = request.form.get("status", "")
    allowed = {"Waiting", "In Progress", "Completed", "Cancelled"}
    if status not in allowed:
        return "Invalid status.", 400

    init_token_db()
    conn = get_db()
    conn.execute(
        "UPDATE customer_tokens SET status = ? WHERE id = ?",
        (status, token_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("token_page.tokens"))
