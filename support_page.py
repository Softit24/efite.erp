import sqlite3
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, render_template_string

support_page = Blueprint("support_page", __name__)
DB_PATH = Path(__file__).resolve().parent / "efite.db"


def init_support_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


@support_page.route("/module/support", methods=["GET", "POST"])
def support():
    init_support_db()

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        category = request.form.get("category", "Other").strip()
        priority = request.form.get("priority", "Normal").strip()
        description = request.form.get("description", "").strip()

        if subject and description:
            with sqlite3.connect(DB_PATH) as db:
                db.execute("""
                    INSERT INTO support_tickets
                    (subject, category, priority, description)
                    VALUES (?, ?, ?, ?)
                """, (subject, category, priority, description))

        return redirect(url_for("support_page.support"))

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        tickets = db.execute(
            "SELECT * FROM support_tickets ORDER BY id DESC"
        ).fetchall()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>EFITE ERP Support</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 900px;
          margin: 20px auto; padding: 16px; background: #f4f6f9; color: #222; }
        h1, h2 { color: #17365d; }
        .panel { background: white; padding: 18px; margin: 16px 0;
          border-radius: 10px; box-shadow: 0 2px 8px #0001; }
        input, select, textarea, button { box-sizing: border-box; width: 100%;
          padding: 11px; margin: 7px 0 14px; border: 1px solid #ccd2da;
          border-radius: 6px; font-size: 16px; }
        button { background: #1769aa; color: white; border: 0; font-weight: bold; }
        a { color: #1769aa; }
        .ticket { border-top: 1px solid #ddd; padding: 12px 0; overflow-wrap: anywhere; }
        .meta { color: #555; font-size: 14px; }
      </style>
    </head>
    <body>
      <h1>EFITE Business ERP — Support</h1>
      <p><a href="/">← Back to ERP Dashboard</a></p>

      <div class="panel">
        <h2>Submit a Support Ticket</h2>
        <form method="post">
          <label>Subject *</label>
          <input name="subject" maxlength="200" required>

          <label>Category</label>
          <select name="category">
            <option>Technical Issue</option>
            <option>Account Access</option>
            <option>Sales or Inventory</option>
            <option>CRM</option>
            <option>Other</option>
          </select>

          <label>Priority</label>
          <select name="priority">
            <option>Low</option>
            <option selected>Normal</option>
            <option>High</option>
            <option>Urgent</option>
          </select>

          <label>Describe the issue *</label>
          <textarea name="description" rows="5" maxlength="5000" required></textarea>
          <button type="submit">Submit Ticket</button>
        </form>
      </div>

      <div class="panel">
        <h2>Support Tickets ({{ tickets|length }})</h2>
        {% for t in tickets %}
          <div class="ticket">
            <strong>#{{ t['id'] }} — {{ t['subject'] }}</strong>
            <p>{{ t['description'] }}</p>
            <div class="meta">
              Category: {{ t['category'] }} |
              Priority: {{ t['priority'] }} |
              Status: {{ t['status'] }} |
              Created: {{ t['created_at'] }}
            </div>
          </div>
        {% else %}
          <p>No support tickets yet. Submit your first ticket above.</p>
        {% endfor %}
      </div>
    </body>
    </html>
    """, tickets=tickets)


init_support_db()
