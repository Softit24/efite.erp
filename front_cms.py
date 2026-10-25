import sqlite3
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, render_template_string
from markupsafe import escape

front_cms = Blueprint("front_cms", __name__)
DB = Path(__file__).resolve().parent / "efite.db"


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS front_cms_content (
                id INTEGER PRIMARY KEY,
                business_name TEXT NOT NULL,
                headline TEXT NOT NULL,
                about TEXT NOT NULL,
                services TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)
        con.execute("""
            INSERT OR IGNORE INTO front_cms_content
            VALUES (1, 'EFITE IT', 'Smart ERP Solutions for Every Business',
                    'EFITE IT provides ERP solutions for schools, colleges, madrasas, shopping malls, hotels, and other businesses.',
                    'ERP Software\nWebsite Development\nApplication Development',
                    '01757254740', 'efite.com.bd@gmail.com')
        """)


def read_content():
    init_db()
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        return dict(con.execute(
            "SELECT * FROM front_cms_content WHERE id=1"
        ).fetchone())


@front_cms.route("/module/front-cms", methods=["GET", "POST"])
def admin():
    content = read_content()

    if request.method == "POST":
        values = tuple(request.form.get(k, "").strip() for k in (
            "business_name", "headline", "about",
            "services", "phone", "email"
        ))
        if all(values[:3]):
            with sqlite3.connect(DB) as con:
                con.execute("""
                    UPDATE front_cms_content
                    SET business_name=?, headline=?, about=?,
                        services=?, phone=?, email=?
                    WHERE id=1
                """, values)
        return redirect(url_for("front_cms.admin"))

    return render_template_string("""
    <!doctype html>
    <html lang="en"><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Front CMS | EFITE IT</title>
    <style>
    *{box-sizing:border-box}
    body{margin:0;background:#f1f5f4;color:#18332b;font-family:Arial,sans-serif}
    nav{background:#173c35;color:white;padding:16px 5%;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
    nav a{color:white;text-decoration:none}
    main{max-width:850px;margin:28px auto;padding:0 16px}
    .panel{background:white;padding:24px;border-radius:16px;box-shadow:0 8px 28px #163c3512}
    h1{margin-top:0}
    label{display:block;font-weight:bold;margin-top:17px}
    input,textarea{width:100%;padding:13px;margin-top:7px;border:1px solid #ccd8d3;border-radius:8px;font:inherit}
    textarea{resize:vertical}
    button{width:100%;margin-top:22px;padding:14px;border:0;border-radius:8px;background:#176b50;color:white;font-size:16px;font-weight:bold}
    .hint{color:#5b7067;font-size:14px}
    </style></head><body>
    <nav><strong>EFITE IT · Website CMS</strong><a href="/">ERP Dashboard</a></nav>
    <main><div class="panel">
    <h1>Manage your website</h1>
    <p class="hint">Edit your public business information, then save to update the website.</p>
    <form method="post">
    <label>Business Name *</label>
    <input name="business_name" maxlength="150" required value="{{content.business_name}}">
    <label>Homepage Headline *</label>
    <input name="headline" maxlength="200" required value="{{content.headline}}">
    <label>About Your Business *</label>
    <textarea name="about" maxlength="5000" rows="5" required>{{content.about}}</textarea>
    <label>Products and Services</label>
    <textarea name="services" maxlength="5000" rows="5">{{content.services}}</textarea>
    <label>Public Phone</label>
    <input name="phone" maxlength="50" value="{{content.phone}}">
    <label>Public Email</label>
    <input type="email" name="email" maxlength="254" value="{{content.email}}">
    <button type="submit">Save Website Content</button>
    </form>
    <p><a href="/website" target="_blank">Preview public website →</a></p>
    </div></main></body></html>
    """, content=content)


@front_cms.route("/website")
def public_website():
    content = read_content()
    services = [
        item.strip() for item in content["services"].replace(",", "\n").splitlines()
        if item.strip()
    ]
    phone_numbers = [
        "".join(ch for ch in number if ch.isdigit())
        for number in content["phone"].replace(";", ",").split(",")
        if "".join(ch for ch in number if ch.isdigit())
    ]

    service_items = []
    for item in services:
        cleaned = item.strip()
        if cleaned.lower().rstrip(":") in ("our product", "our products", "products", "services"):
            continue
        cleaned = cleaned.lstrip("0123456789.):- ").strip()
        if cleaned:
            service_items.append(cleaned)
    services = service_items

    service_cards = "".join(
        '<article class="service"><span class="service-icon">✦</span><h3>'
        + str(escape(item)) + '</h3><p>Solutions from EFITE IT, tailored to your needs.</p></article>'
        for item in services
    )

    phone_button = "".join(
        '<a class="button" href="tel:' + number + '">Call ' + number + '</a>'
        for number in phone_numbers
    )

    email_button = (
        '<a class="button secondary" href="mailto:' +
        str(escape(content["email"])) + '">Email Us</a>'
        if content["email"] else ""
    )

    whatsapp_button = (
        '<a class="button whatsapp" target="_blank" rel="noopener" href="https://wa.me/'
        + phone_numbers[0] + '">WhatsApp</a>'
        if phone_numbers else ""
    )

    page = """
    <!doctype html>
    <html lang="en"><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="description" content="{{ content.about[:155] }}">
    <title>{{content.business_name}} | Business Technology Solutions</title>
    <style>
    *{box-sizing:border-box}
    html{scroll-behavior:smooth}
    body{margin:0;font-family:Arial,sans-serif;color:#20352e;background:#fff;line-height:1.65}
    a{text-decoration:none}
    .nav{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px max(5%,calc((100% - 1100px)/2));background:#fff}
    .brand{font-size:22px;font-weight:800;color:#173c35}
    .navlinks{display:flex;gap:20px;flex-wrap:wrap}
    .navlinks a{color:#35584a;font-weight:600}
    .hero{background:linear-gradient(135deg,#173c35,#176b50);color:#fff;padding:76px 20px 84px}
    .hero-inner{max-width:1050px;margin:auto}
    .eyebrow{color:#b8ead0;font-weight:bold;letter-spacing:2px;text-transform:uppercase;font-size:13px}
    h1{font-size:clamp(36px,7vw,62px);line-height:1.1;max-width:800px;margin:18px 0}
    .hero p{font-size:18px;max-width:680px;color:#e1f1e8}
    .actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}
    .button{display:inline-block;background:#d9f99d;color:#173c35;padding:12px 20px;border-radius:9px;font-weight:bold}
    .secondary{background:#fff;color:#173c35}
    .whatsapp{background:#dcfce7}
    .wrap{max-width:1050px;margin:auto;padding:55px 20px}
    .section-title{text-align:center;margin-bottom:32px}
    .section-title h2{font-size:clamp(27px,4vw,38px);margin:0 0 8px;color:#173c35}
    .section-title p{color:#60756b;margin:0}
    .about{max-width:800px;margin:auto;font-size:18px;white-space:pre-line;text-align:center}
    .services{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}
    .service{padding:25px;border:1px solid #e1ebe5;border-radius:15px;background:#fff;box-shadow:0 8px 25px #173c350a}
    .service-icon{display:inline-grid;place-items:center;width:42px;height:42px;border-radius:12px;background:#e4f5eb;color:#176b50;font-size:24px}
    .service h3{margin:15px 0 6px;color:#173c35}
    .service p{margin:0;color:#62756b}
    .contact{background:#f0f7f2}
    .contact-box{text-align:center}
    .contact-box p{white-space:pre-line}
    .contact-links{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:20px}
    footer{background:#102f29;color:#dcece3;padding:26px 20px;text-align:center}
    footer p{margin:4px}
    @media(max-width:520px){.hero{padding:55px 20px}.nav{align-items:flex-start}.navlinks{gap:12px;font-size:14px}.wrap{padding:42px 18px}}
    </style></head><body>
    <nav class="nav"><a class="brand" href="/website">{{content.business_name}}</a>
    <div class="navlinks"><a href="/website">Home</a><a href="#about">About</a><a href="#services">Services</a><a href="#services">Products</a><a href="#contact">Contact</a></div></nav>
    <header class="hero"><div class="hero-inner">
    <div class="eyebrow">Technology · Innovation · Growth</div>
    <h1>{{content.headline}}</h1>
    <p>{{content.about}}</p>
    <div class="actions">""" + phone_button + email_button + whatsapp_button + """</div>
    </div></header>
    <main>
    <section class="wrap" id="about"><div class="section-title"><h2>About {{content.business_name}}</h2><p>Your technology partner for smarter operations</p></div>
    <div class="about">{{content.about}}</div></section>
    <section class="wrap" id="services"><div class="section-title"><h2>Our Products &amp; Services</h2><p>Digital solutions to help your organization grow</p></div>
    <div class="services">""" + service_cards + """</div></section>
    <section class="contact" id="contact"><div class="wrap contact-box">
    <div class="section-title"><h2>Let's Talk</h2><p>Contact us to discuss your business needs.</p></div>
    {% if content.phone %}<p><strong>Phone:</strong> {{content.phone}}</p>{% endif %}
    {% if content.email %}<p><strong>Email:</strong> {{content.email}}</p>{% endif %}
    <div class="contact-links">""" + phone_button + email_button + whatsapp_button + """</div>
    </div></section></main>
    <footer><p><strong>{{content.business_name}}</strong></p><p>ERP Solutions · Websites · Applications</p><p>© {{content.business_name}}. All rights reserved.</p></footer>
    </body></html>
    """
    return render_template_string(page, content=content)


init_db()
