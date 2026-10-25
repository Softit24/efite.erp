import sqlite3
from flask import Blueprint, request, redirect, url_for, render_template_string, flash

settings_bp = Blueprint("settings", __name__)
DB_PATH = "efite.db"


def init_settings_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS business_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                business_name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO business_settings
            (id, business_name, phone, email, address)
            VALUES (1, '', '', '', '')
        """)


@settings_bp.route("/", methods=["GET", "POST"])
def general():
    init_settings_db()

    if request.method == "POST":
        values = (
            request.form.get("business_name", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("address", "").strip(),
        )
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE business_settings
                SET business_name=?, phone=?, email=?, address=?
                WHERE id=1
            """, values)
        return redirect(url_for("settings.general", saved="1"))

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        settings = conn.execute(
            "SELECT * FROM business_settings WHERE id=1"
        ).fetchone()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>General Settings - EFITE ERP</title>
      <style>
        body{font-family:Arial,sans-serif;background:#f1f5f4;color:#18332b;margin:0}
        header{background:#173c35;color:white;padding:20px}
        main{max-width:650px;margin:25px auto;padding:18px}
        .panel{background:white;padding:22px;border-radius:12px}
        label{display:block;font-weight:bold;margin-top:15px}
        input,textarea{box-sizing:border-box;width:100%;padding:12px;margin-top:6px;border:1px solid #cbd5d1;border-radius:7px;font-size:16px}
        button{margin-top:20px;padding:12px 20px;background:#176b50;color:white;border:0;border-radius:7px;font-size:16px}
        .back{color:#176b50}
        .success{background:#e1f5e8;padding:12px;border-radius:7px}
      </style>
    </head>
    <body>
      <header><h2>EFITE Business ERP</h2><p>Backend Settings</p></header>
      <main>
        <p><a class="back" href="/">← Back to Dashboard</a></p>
        <div class="panel">
          <h2>General Settings</h2>
          <p>
            <a href="/settings/">General Settings</a> |
            <a href="/settings/regional">Regional Settings</a> |
            <a href="/settings/system">System Preferences</a> |
            <a href="/settings/website">Website Settings</a>
          </p>
          {% if request.args.get('saved') %}<p class="success">Settings saved successfully.</p>{% endif %}
          <form method="post">
            <label>Business Name</label>
            <input name="business_name" value="{{ settings['business_name'] }}" placeholder="Your business name">
            <label>Phone</label>
            <input name="phone" value="{{ settings['phone'] }}" placeholder="Phone number">
            <label>Email</label>
            <input type="email" name="email" value="{{ settings['email'] }}" placeholder="Business email">
            <label>Business Address</label>
            <textarea name="address" rows="3" placeholder="Business address">{{ settings['address'] }}</textarea>
            <button type="submit">Save Settings</button>
          </form>
        </div>
      </main>
    </body>
    </html>
    """, settings=settings)


init_settings_db()


@settings_bp.route("/website")
def website_settings():
    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Website Settings - EFITE ERP</title>
      <style>
        body{font-family:Arial,sans-serif;background:#f1f5f4;color:#18332b;margin:0}
        header{background:#173c35;color:white;padding:20px}
        main{max-width:650px;margin:25px auto;padding:18px}
        .panel{background:white;padding:22px;border-radius:12px}
        a,button{display:inline-block;padding:12px;margin:6px 4px 6px 0;border-radius:7px;text-decoration:none}
        a{color:#176b50;background:#e5f1eb}
        button{background:#176b50;color:white}
      </style>
    </head>
    <body>
      <header><h2>EFITE Business ERP</h2><p>Website Settings</p></header>
      <main>
        <div class="panel">
          <h2>Manage Public Website</h2>
          <p>Your existing website content is managed through Front CMS.</p>
          <p>Open Front CMS to edit your website name, headline, about section, services, phone, and email.</p>
          <a href="/module/front-cms">Open Front CMS Editor</a>
          <a href="/website" target="_blank">Preview Public Website</a>
          <p><a href="/settings/">Back to General Settings</a></p>
          <p><a href="/">Back to Dashboard</a></p>
        </div>
      </main>
    </body>
    </html>
    """)



@settings_bp.route("/regional", methods=["GET", "POST"])
def regional_settings():
    init_settings_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_preferences (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                currency TEXT NOT NULL DEFAULT 'BDT',
                timezone TEXT NOT NULL DEFAULT 'Asia/Dhaka',
                date_format TEXT NOT NULL DEFAULT 'DD-MM-YYYY',
                language TEXT NOT NULL DEFAULT 'English'
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO system_preferences (id)
            VALUES (1)
        """)

        if request.method == "POST":
            conn.execute("""
                UPDATE system_preferences
                SET currency=?, timezone=?, date_format=?, language=?
                WHERE id=1
            """, (
                request.form.get("currency", "BDT"),
                request.form.get("timezone", "Asia/Dhaka"),
                request.form.get("date_format", "DD-MM-YYYY"),
                request.form.get("language", "English"),
            ))
            return redirect(url_for("settings.regional_settings", saved="1"))

        conn.row_factory = sqlite3.Row
        prefs = conn.execute(
            "SELECT * FROM system_preferences WHERE id=1"
        ).fetchone()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Regional and System Settings - EFITE ERP</title>
      <style>
        body{font-family:Arial,sans-serif;background:#f1f5f4;color:#18332b;margin:0}
        header{background:#173c35;color:white;padding:20px}
        main{max-width:650px;margin:25px auto;padding:18px}
        .panel{background:white;padding:22px;border-radius:12px}
        label{display:block;font-weight:bold;margin-top:15px}
        input,select{box-sizing:border-box;width:100%;padding:12px;margin-top:6px;border:1px solid #cbd5d1;border-radius:7px;font-size:16px;background:white}
        button,a{display:inline-block;margin-top:20px;padding:12px 18px;border-radius:7px;text-decoration:none}
        button{background:#176b50;color:white;border:0;font-size:16px}
        a{color:#176b50;background:#e5f1eb}
        .success{background:#e1f5e8;padding:12px;border-radius:7px}
      </style>
    </head>
    <body>
      <header><h2>EFITE Business ERP</h2><p>Regional and System Settings</p></header>
      <main>
        <p><a href="/settings/">Back to General Settings</a></p>
        <div class="panel">
          <h2>Regional Settings</h2>
          {% if request.args.get('saved') %}
          <p class="success">Settings saved successfully.</p>
          {% endif %}
          <form method="post">
            <label>Currency</label>
            <select name="currency">
              {% for code, name in [('BDT','Bangladeshi Taka (BDT)'),('USD','US Dollar (USD)'),('INR','Indian Rupee (INR)'),('EUR','Euro (EUR)'),('GBP','British Pound (GBP)')] %}
              <option value="{{ code }}" {% if prefs['currency']==code %}selected{% endif %}>{{ name }}</option>
              {% endfor %}
            </select>

            <label>Time Zone</label>
            <select name="timezone">
              {% for zone, name in [('Asia/Dhaka','Bangladesh (Dhaka)'),('UTC','UTC'),('Asia/Kolkata','India (Kolkata)'),('Asia/Dubai','UAE (Dubai)'),('Europe/London','United Kingdom (London)'),('America/New_York','USA (New York)')] %}
              <option value="{{ zone }}" {% if prefs['timezone']==zone %}selected{% endif %}>{{ name }}</option>
              {% endfor %}
            </select>

            <label>Date Format</label>
            <select name="date_format">
              {% for fmt in ['DD-MM-YYYY','MM-DD-YYYY','YYYY-MM-DD'] %}
              <option value="{{ fmt }}" {% if prefs['date_format']==fmt %}selected{% endif %}>{{ fmt }}</option>
              {% endfor %}
            </select>

            <label>Default Language</label>
            <select name="language">
              {% for lang in ['English','বাংলা'] %}
              <option value="{{ lang }}" {% if prefs['language']==lang %}selected{% endif %}>{{ lang }}</option>
              {% endfor %}
            </select>

            <button type="submit">Save Preferences</button>
          </form>
        </div>
      </main>
    </body>
    </html>
    """, prefs=prefs)


@settings_bp.route("/system")
def system_settings():
    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>System Preferences - EFITE ERP</title>
      <style>
        body{font-family:Arial,sans-serif;background:#f1f5f4;color:#18332b;margin:0}
        header{background:#173c35;color:white;padding:20px}
        main{max-width:650px;margin:25px auto;padding:18px}
        .panel{background:white;padding:22px;border-radius:12px}
        a{display:inline-block;margin:8px 4px;padding:12px;border-radius:7px;text-decoration:none;color:#176b50;background:#e5f1eb}
      </style>
    </head>
    <body>
      <header><h2>EFITE Business ERP</h2><p>System Preferences</p></header>
      <main><div class="panel">
        <h2>System Preferences</h2>
        <p>Manage regional settings and access existing website settings.</p>
        <a href="/settings/regional">Currency, Time Zone, Language and Date Format</a>
        <a href="/settings/website">Website Settings</a>
        <a href="/">Back to Dashboard</a>
      </div></main>
    </body>
    </html>
    """)
