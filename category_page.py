from flask import Blueprint, request, redirect, render_template_string, url_for
from category_db import get_categories, add_category, delete_category

category_page = Blueprint("category_page", __name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Categories - EFITE Business ERP</title>
<style>
body { margin:0; font-family:Arial,sans-serif; background:#f3f5f9; color:#222; }
header { background:#17365d; color:white; padding:20px; }
main { max-width:850px; margin:20px auto; padding:16px; }
.panel { background:white; padding:20px; margin-top:18px; border-radius:10px; }
input, textarea, button { box-sizing:border-box; width:100%; padding:12px; margin:7px 0; }
button { background:#176b45; color:white; border:0; border-radius:5px; }
.delete { background:#a52a2a; width:auto; }
.item { border-bottom:1px solid #ddd; padding:12px 0; }
.back { color:white; }
.message { color:#176b45; }
</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>Category Management</p>
<a class="back" href="{{ url_for('dashboard') }}">← Back to Dashboard</a>
</header>
<main>
<h2>Product Categories</h2>
{% if message %}<p class="message">{{ message }}</p>{% endif %}
<section class="panel">
<h3>Add Category</h3>
<form method="post">
<label>Category name</label>
<input name="name" required maxlength="100" placeholder="e.g. Networking Equipment">
<label>Description</label>
<textarea name="description" rows="3" placeholder="Optional description"></textarea>
<button type="submit">Add Category</button>
</form>
</section>
<section class="panel">
<h3>Existing Categories ({{ categories|length }})</h3>
{% for category in categories %}
<div class="item">
<strong>{{ category['name'] }}</strong>
{% if category['description'] %}<p>{{ category['description'] }}</p>{% endif %}
<form method="post" action="{{ url_for('category_page.remove_category', category_id=category['id']) }}" onsubmit="return confirm('Delete this category?')">
<button class="delete" type="submit">Delete</button>
</form>
</div>
{% else %}
<p>No categories yet. Add your first category above.</p>
{% endfor %}
</section>
</main>
</body>
</html>
"""

@category_page.route("/module/category", methods=["GET", "POST"])
def categories():
    message = request.args.get("message", "")
    if request.method == "POST":
        ok, result = add_category(
            request.form.get("name", ""),
            request.form.get("description", "")
        )
        return redirect(url_for(
            "category_page.categories",
            message=result
        ))
    return render_template_string(
        TEMPLATE,
        categories=get_categories(),
        message=message
    )

@category_page.route("/module/category/delete/<int:category_id>", methods=["POST"])
def remove_category(category_id):
    delete_category(category_id)
    return redirect(url_for(
        "category_page.categories",
        message="Category deleted."
    ))
