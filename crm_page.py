import os
import sqlite3
from datetime import date
from pathlib import Path
from flask import (
    Blueprint, current_app, render_template_string, request,
    redirect, url_for, flash, send_from_directory, abort
)
from werkzeug.utils import secure_filename

crm_page = Blueprint("crm", __name__, url_prefix="/crm")

DB_PATH = Path(__file__).resolve().parent / "efite.db"
UPLOAD_DIR = Path(__file__).resolve().parent / "private_uploads" / "cv"
ALLOWED_CV_EXTENSIONS = {".pdf", ".doc", ".docx"}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_crm_db():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS crm_emes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eme_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            assigned_area TEXT NOT NULL DEFAULT '',
            designation TEXT NOT NULL DEFAULT 'EFITE Marketing Executive',
            joining_date TEXT NOT NULL DEFAULT '',
            cv_filename TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Active'
                CHECK(status IN ('Active', 'Inactive')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS crm_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            eme_id INTEGER,
            target_month TEXT NOT NULL,
            target_amount REAL NOT NULL DEFAULT 0 CHECK(target_amount >= 0),
            actual_amount REAL NOT NULL DEFAULT 0 CHECK(actual_amount >= 0),
            follow_up_date TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Lead'
                CHECK(status IN ('Lead', 'Contacted', 'Follow-up', 'Won', 'Lost')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY(eme_id) REFERENCES crm_emes(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS crm_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            recipient_name TEXT NOT NULL DEFAULT 'All',
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS crm_salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eme_id INTEGER,
            staff_name TEXT NOT NULL,
            salary_month TEXT NOT NULL,
            basic_salary REAL NOT NULL DEFAULT 0 CHECK(basic_salary >= 0),
            allowances REAL NOT NULL DEFAULT 0 CHECK(allowances >= 0),
            deductions REAL NOT NULL DEFAULT 0 CHECK(deductions >= 0),
            payment_date TEXT NOT NULL DEFAULT '',
            payment_status TEXT NOT NULL DEFAULT 'Pending'
                CHECK(payment_status IN ('Pending', 'Paid')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(eme_id) REFERENCES crm_emes(id) ON DELETE SET NULL,
            UNIQUE(staff_name, salary_month)
        );
        """)
        # Link existing customers where names/phones match, without changing them.
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_crm_targets_month
            ON crm_targets(target_month)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_crm_messages_created
            ON crm_messages(created_at)
        """)

BASE = """
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} - EFITE CRM</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f1f5f4;color:#18332b;font:15px Arial,sans-serif}
header{background:#173c35;color:white;padding:20px}header h2{margin:0 0 6px}
main{max-width:1100px;margin:auto;padding:18px}.nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.nav a,.btn{display:inline-block;background:#176b50;color:#fff;text-decoration:none;border:0;border-radius:7px;padding:10px 13px;cursor:pointer}
.panel{background:#fff;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 2px 8px #00000010}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
label{display:block;font-weight:bold;margin:10px 0 5px}input,select,textarea{width:100%;padding:10px;border:1px solid #cbd5d1;border-radius:6px;background:white}
textarea{min-height:80px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:9px;border-bottom:1px solid #e0e7e3;text-align:left;vertical-align:top}
.table-wrap{overflow-x:auto}.muted{color:#66766e}.flash{background:#fff2cc;padding:10px;border-radius:6px;margin:8px 0}
.stat{background:#edf4f0;border-radius:8px;padding:14px}.stat strong{display:block;font-size:23px;margin-top:6px}
@media(max-width:600px){main{padding:10px}.panel{padding:12px}th,td{padding:7px;font-size:13px}}
</style></head><body>
<header><h2>EFITE Business ERP — CRM</h2><div>Marketing Executive & Staff Management</div></header>
<main><div class="nav">
<a href="{{ url_for('dashboard') }}">ERP Dashboard</a>
<a href="{{ url_for('crm.crm_home') }}">CRM Home</a>
<a href="{{ url_for('crm.emes') }}">EME List / CV</a>
<a href="{{ url_for('crm.targets') }}">Customer Targets</a>
<a href="{{ url_for('crm.chat') }}">Chat</a>
<a href="{{ url_for('crm.salaries') }}">Salary Records</a>
</div>
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}
{{ body|safe }}
</main></body></html>
"""

def page(title, body, **context):
    return render_template_string(BASE, title=title, body=render_template_string(body, **context))

@crm_page.route("/")
def crm_home():
    with db() as conn:
        emes = conn.execute("SELECT COUNT(*) FROM crm_emes WHERE status='Active'").fetchone()[0]
        targets = conn.execute("SELECT COUNT(*) FROM crm_targets").fetchone()[0]
        unread = conn.execute("SELECT COUNT(*) FROM crm_messages WHERE is_read=0").fetchone()[0]
        payroll = conn.execute("""
            SELECT COALESCE(SUM(basic_salary + allowances - deductions),0)
            FROM crm_salary_records WHERE salary_month=?
        """, (date.today().strftime("%Y-%m"),)).fetchone()[0]
    body = """
    <h3>CRM Dashboard</h3><div class="grid">
    <div class="stat">Active EMEs<strong>{{ emes }}</strong></div>
    <div class="stat">Customer Targets<strong>{{ targets }}</strong></div>
    <div class="stat">Unread Messages<strong>{{ unread }}</strong></div>
    <div class="stat">Current Month Payroll<strong>{{ '%.2f'|format(payroll) }}</strong></div>
    </div><div class="panel"><h3>Quick links</h3>
    <p>Register EMEs, upload CVs, assign customer targets, communicate with staff, and maintain monthly salary records.</p></div>
    """
    return page("Dashboard", body, emes=emes, targets=targets, unread=unread, payroll=payroll)

@crm_page.route("/emes", methods=["GET", "POST"])
def emes():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        if not full_name:
            flash("Full name is required.")
            return redirect(url_for("crm.emes"))
        cv = request.files.get("cv")
        filename = ""
        if cv and cv.filename:
            original = secure_filename(cv.filename)
            suffix = Path(original).suffix.lower()
            if suffix not in ALLOWED_CV_EXTENSIONS:
                flash("CV must be a PDF, DOC, or DOCX file.")
                return redirect(url_for("crm.emes"))
            # Randomized storage name avoids collisions and exposes no original path.
            import uuid
            filename = uuid.uuid4().hex + suffix
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            cv.save(UPLOAD_DIR / filename)
        code = request.form.get("eme_code", "").strip()
        if not code:
            code = "EME-" + date.today().strftime("%y%m%d") + "-" + os.urandom(3).hex().upper()
        try:
            with db() as conn:
                conn.execute("""
                    INSERT INTO crm_emes
                    (eme_code, full_name, phone, email, address, assigned_area,
                     designation, joining_date, cv_filename, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (code, full_name, request.form.get("phone","").strip(),
                      request.form.get("email","").strip(), request.form.get("address","").strip(),
                      request.form.get("assigned_area","").strip(),
                      request.form.get("designation","EFITE Marketing Executive").strip(),
                      request.form.get("joining_date",""), filename,
                      request.form.get("status","Active"),
                      request.form.get("notes","").strip()))
            flash("EME record saved.")
            return redirect(url_for("crm.emes"))
        except sqlite3.IntegrityError:
            if filename:
                (UPLOAD_DIR / filename).unlink(missing_ok=True)
            flash("EME code already exists or the submitted status is invalid.")
            return redirect(url_for("crm.emes"))
    with db() as conn:
        rows = conn.execute("SELECT * FROM crm_emes ORDER BY id DESC").fetchall()
    body = """
    <div class="panel"><h3>EME Entry Form</h3>
    <form method="post" enctype="multipart/form-data"><div class="grid">
    <div><label>EME Code (optional)</label><input name="eme_code" placeholder="Auto-generated if blank"></div>
    <div><label>Full name *</label><input name="full_name" required></div>
    <div><label>Phone</label><input name="phone" maxlength="40"></div>
    <div><label>Email</label><input type="email" name="email" maxlength="254"></div>
    <div><label>Assigned area</label><input name="assigned_area"></div>
    <div><label>Designation</label><input name="designation" value="EFITE Marketing Executive" required></div>
    <div><label>Joining date</label><input type="date" name="joining_date"></div>
    <div><label>Status</label><select name="status"><option>Active</option><option>Inactive</option></select></div>
    <div><label>CV (PDF, DOC, DOCX; max size should be configured at deployment)</label><input type="file" name="cv" accept=".pdf,.doc,.docx"></div>
    </div><label>Address</label><textarea name="address"></textarea>
    <label>Notes</label><textarea name="notes"></textarea><p><button class="btn">Save EME</button></p></form></div>
    <div class="panel"><h3>EME Directory</h3><div class="table-wrap"><table><tr><th>Code</th><th>Name</th><th>Phone</th><th>Area</th><th>Status</th><th>CV</th></tr>
    {% for e in rows %}<tr><td>{{ e.eme_code }}</td><td>{{ e.full_name }}</td><td>{{ e.phone }}</td><td>{{ e.assigned_area }}</td><td>{{ e.status }}</td><td>{% if e.cv_filename %}<a href="{{ url_for('crm.cv_file', filename=e.cv_filename) }}">View CV</a>{% else %}—{% endif %}</td></tr>{% else %}<tr><td colspan="6">No EMEs registered yet.</td></tr>{% endfor %}
    </table></div></div>
    """
    return page("EME Management", body, rows=rows)

@crm_page.route("/cv/<path:filename>")
def cv_file(filename):
    # Private directory, but authorization must be added when login/session
    # handling is wired into the application.
    if not filename or Path(filename).name != filename:
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@crm_page.route("/targets", methods=["GET", "POST"])
def targets():
    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        month = request.form.get("target_month", "").strip()
        if not name or len(month) != 7 or month[4] != "-":
            flash("Customer name and target month are required.")
            return redirect(url_for("crm.targets"))
        try:
            target_amount = float(request.form.get("target_amount", "0"))
            actual_amount = float(request.form.get("actual_amount", "0"))
            if min(target_amount, actual_amount) < 0:
                raise ValueError
        except ValueError:
            flash("Target and actual amounts must be non-negative numbers.")
            return redirect(url_for("crm.targets"))
        eme_id = request.form.get("eme_id") or None
        try:
            with db() as conn:
                conn.execute("""
                    INSERT INTO crm_targets
                    (customer_name, phone, address, eme_id, target_month,
                     target_amount, actual_amount, follow_up_date, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, request.form.get("phone","").strip(),
                      request.form.get("address","").strip(), eme_id, month,
                      target_amount, actual_amount, request.form.get("follow_up_date",""),
                      request.form.get("status","Lead"), request.form.get("notes","").strip()))
            flash("Customer target saved.")
            return redirect(url_for("crm.targets"))
        except (sqlite3.IntegrityError, ValueError):
            flash("Could not save target. Check the selected EME and values.")
            return redirect(url_for("crm.targets"))
    with db() as conn:
        emes_list = conn.execute("SELECT id, eme_code, full_name FROM crm_emes WHERE status='Active' ORDER BY full_name").fetchall()
        rows = conn.execute("""
            SELECT t.*, e.eme_code, e.full_name AS eme_name
            FROM crm_targets t LEFT JOIN crm_emes e ON e.id=t.eme_id
            ORDER BY t.target_month DESC, t.id DESC
        """).fetchall()
    body = """
    <div class="panel"><h3>Customer Target Entry</h3><form method="post"><div class="grid">
    <div><label>Customer / prospect name *</label><input name="customer_name" required></div>
    <div><label>Phone</label><input name="phone"></div><div><label>Target month *</label><input type="month" name="target_month" value="{{ month }}" required></div>
    <div><label>Assigned EME</label><select name="eme_id"><option value="">Unassigned</option>{% for e in emes_list %}<option value="{{ e.id }}">{{ e.eme_code }} — {{ e.full_name }}</option>{% endfor %}</select></div>
    <div><label>Target amount</label><input type="number" min="0" step="0.01" name="target_amount" value="0"></div>
    <div><label>Actual sales amount</label><input type="number" min="0" step="0.01" name="actual_amount" value="0"></div>
    <div><label>Follow-up date</label><input type="date" name="follow_up_date"></div>
    <div><label>Status</label><select name="status">{% for x in ['Lead','Contacted','Follow-up','Won','Lost'] %}<option>{{ x }}</option>{% endfor %}</select></div>
    </div><label>Address</label><textarea name="address"></textarea><label>Notes</label><textarea name="notes"></textarea><p><button class="btn">Save Target</button></p></form></div>
    <div class="panel"><h3>Customer Targets</h3><div class="table-wrap"><table><tr><th>Month</th><th>Customer</th><th>EME</th><th>Target</th><th>Actual</th><th>Follow-up</th><th>Status</th></tr>
    {% for t in rows %}<tr><td>{{ t.target_month }}</td><td>{{ t.customer_name }}<br>{{ t.phone }}</td><td>{{ t.eme_name or 'Unassigned' }}</td><td>{{ '%.2f'|format(t.target_amount) }}</td><td>{{ '%.2f'|format(t.actual_amount) }}</td><td>{{ t.follow_up_date or '—' }}</td><td>{{ t.status }}</td></tr>{% else %}<tr><td colspan="7">No targets entered yet.</td></tr>{% endfor %}
    </table></div></div>
    """
    return page("Customer Targets", body, rows=rows, emes_list=emes_list, month=date.today().strftime("%Y-%m"))

@crm_page.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        sender = request.form.get("sender_name", "").strip()
        recipient = request.form.get("recipient_name", "All").strip() or "All"
        message = request.form.get("message", "").strip()
        if not sender or not message:
            flash("Sender name and message are required.")
        elif len(message) > 4000:
            flash("Message is too long (maximum 4000 characters).")
        else:
            with db() as conn:
                conn.execute("INSERT INTO crm_messages (sender_name, recipient_name, message) VALUES (?, ?, ?)",
                             (sender, recipient, message))
            flash("Message saved.")
        return redirect(url_for("crm.chat"))
    with db() as conn:
        rows = conn.execute("SELECT * FROM crm_messages ORDER BY id DESC LIMIT 200").fetchall()
    body = """
    <div class="panel"><h3>Internal Chat</h3><p class="muted">This first version stores messages and refreshes when the page is reloaded; it is not real-time and does not yet authenticate sender identities.</p>
    <form method="post"><div class="grid"><div><label>Your display name *</label><input name="sender_name" required maxlength="120"></div>
    <div><label>Recipient</label><input name="recipient_name" value="All" maxlength="120"></div></div>
    <label>Message *</label><textarea name="message" required maxlength="4000"></textarea><p><button class="btn">Send Message</button></p></form></div>
    <div class="panel"><h3>Recent Messages</h3>{% for m in rows %}<div style="border-bottom:1px solid #e0e7e3;padding:10px 0"><strong>{{ m.sender_name }}</strong> → {{ m.recipient_name }} <span class="muted">{{ m.created_at }}</span><p style="white-space:pre-wrap">{{ m.message }}</p></div>{% else %}<p>No messages yet.</p>{% endfor %}</div>
    """
    return page("Internal Chat", body, rows=rows)

@crm_page.route("/salaries", methods=["GET", "POST"])
def salaries():
    if request.method == "POST":
        staff_name = request.form.get("staff_name", "").strip()
        month = request.form.get("salary_month", "").strip()
        if not staff_name or len(month) != 7 or month[4] != "-":
            flash("Staff name and salary month are required.")
            return redirect(url_for("crm.salaries"))
        try:
            basic = float(request.form.get("basic_salary", "0"))
            allowances = float(request.form.get("allowances", "0"))
            deductions = float(request.form.get("deductions", "0"))
            if min(basic, allowances, deductions) < 0:
                raise ValueError
        except ValueError:
            flash("Salary amounts must be non-negative numbers.")
            return redirect(url_for("crm.salaries"))
        eme_id = request.form.get("eme_id") or None
        try:
            with db() as conn:
                conn.execute("""
                    INSERT INTO crm_salary_records
                    (eme_id, staff_name, salary_month, basic_salary, allowances,
                     deductions, payment_date, payment_status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(staff_name, salary_month) DO UPDATE SET
                    eme_id=excluded.eme_id, basic_salary=excluded.basic_salary,
                    allowances=excluded.allowances, deductions=excluded.deductions,
                    payment_date=excluded.payment_date, payment_status=excluded.payment_status,
                    notes=excluded.notes
                """, (eme_id, staff_name, month, basic, allowances, deductions,
                      request.form.get("payment_date",""),
                      request.form.get("payment_status","Pending"),
                      request.form.get("notes","").strip()))
            flash("Salary record saved.")
            return redirect(url_for("crm.salaries"))
        except (sqlite3.IntegrityError, ValueError):
            flash("Could not save salary record. Check the selected EME and values.")
            return redirect(url_for("crm.salaries"))
    with db() as conn:
        emes_list = conn.execute("SELECT id, full_name FROM crm_emes ORDER BY full_name").fetchall()
        rows = conn.execute("SELECT * FROM crm_salary_records ORDER BY salary_month DESC, staff_name").fetchall()
    body = """
    <div class="panel"><h3>Staff Salary Entry</h3><p class="muted">Salary records are sensitive. Add login/role authorization before using this page in a shared or internet-facing deployment.</p>
    <form method="post"><div class="grid"><div><label>Staff name *</label><input name="staff_name" required></div>
    <div><label>Linked EME (optional)</label><select name="eme_id"><option value="">Other staff / not linked</option>{% for e in emes_list %}<option value="{{ e.id }}">{{ e.full_name }}</option>{% endfor %}</select></div>
    <div><label>Salary month *</label><input type="month" name="salary_month" value="{{ month }}" required></div>
    <div><label>Basic salary</label><input type="number" min="0" step="0.01" name="basic_salary" value="0"></div>
    <div><label>Allowances</label><input type="number" min="0" step="0.01" name="allowances" value="0"></div>
    <div><label>Deductions</label><input type="number" min="0" step="0.01" name="deductions" value="0"></div>
    <div><label>Payment date</label><input type="date" name="payment_date"></div>
    <div><label>Payment status</label><select name="payment_status"><option>Pending</option><option>Paid</option></select></div></div>
    <label>Notes</label><textarea name="notes"></textarea><p><button class="btn">Save Salary Record</button></p></form></div>
    <div class="panel"><h3>Salary History</h3><div class="table-wrap"><table><tr><th>Month</th><th>Staff</th><th>Basic</th><th>Allowances</th><th>Deductions</th><th>Net salary</th><th>Payment</th></tr>
    {% for s in rows %}<tr><td>{{ s.salary_month }}</td><td>{{ s.staff_name }}</td><td>{{ '%.2f'|format(s.basic_salary) }}</td><td>{{ '%.2f'|format(s.allowances) }}</td><td>{{ '%.2f'|format(s.deductions) }}</td><td>{{ '%.2f'|format(s.basic_salary+s.allowances-s.deductions) }}</td><td>{{ s.payment_status }}{% if s.payment_date %}<br>{{ s.payment_date }}{% endif %}</td></tr>{% else %}<tr><td colspan="7">No salary records yet.</td></tr>{% endfor %}
    </table></div></div>
    """
    return page("Salary Records", body, rows=rows, emes_list=emes_list, month=date.today().strftime("%Y-%m"))
