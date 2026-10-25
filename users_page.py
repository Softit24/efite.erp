from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from users_db import init_users_table, list_users, add_user, delete_user

users_page = Blueprint("users_page", __name__)
init_users_table()

STYLE = """
body { font-family: Arial, sans-serif; background: #f1f5f4; color: #18332b; margin: 0; }
header { background: #173c35; color: white; padding: 20px; }
main { max-width: 1000px; margin: 25px auto; padding: 0 16px; }
.panel { background: white; padding: 20px; margin: 18px 0; border-radius: 10px; }
input, select, button { padding: 10px; margin: 5px 0; max-width: 100%; }
input, select { width: 100%; border: 1px solid #ccd6d1; border-radius: 5px; }
button { background: #173c35; color: white; border: 0; border-radius: 5px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
.notice { padding: 10px; background: #e4eee8; margin: 10px 0; }
a { color: #17634e; }
"""

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Users - EFITE Business ERP</title>
<style>{{ style }}</style>
</head>
<body>
<header>
<h2>EFITE Business ERP</h2>
<p>User Management</p>
</header>
<main>
<a href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="notice">{{ message }}</div>
{% endfor %}
{% endwith %}

<section class="panel">
<h3>Add User</h3>
<form method="post" action="{{ url_for('users_page.create_user') }}">
<label>Full name</label>
<input name="full_name" required maxlength="120">

<label>Username</label>
<input name="username" required maxlength="80" autocomplete="off">

<label>Password</label>
<input type="password" name="password" required minlength="8" autocomplete="new-password">

<label>Role</label>
<select name="role" required>
<option value="Employee">Employee</option>
<option value="Admin">Admin</option>
<option value="Customer">Customer</option>
</select>

<label>Status</label>
<select name="status" required>
<option value="Active">Active</option>
<option value="Inactive">Inactive</option>
</select>
<button type="submit">Create User</button>
</form>
</section>

<section class="panel">
<h3>Existing Users ({{ users|length }})</h3>
{% if users %}
<div style="overflow-x:auto">
<table>
<thead><tr><th>ID</th><th>Name</th><th>Username</th><th>Role</th><th>Status</th><th>Action</th></tr></thead>
<tbody>
{% for user in users %}
<tr>
<td>{{ user.id }}</td>
<td>{{ user.full_name }}</td>
<td>{{ user.username }}</td>
<td>{{ user.role }}</td>
<td>{{ user.status }}</td>
<td>
<form method="post" action="{{ url_for('users_page.remove_user', user_id=user.id) }}" onsubmit="return confirm('Delete this user?')">
<button type="submit">Delete</button>
</form>
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<p>No users have been created yet.</p>
{% endif %}
</section>
</main>
</body>
</html>
"""


@users_page.get("/module/users")
def users():
    return render_template_string(TEMPLATE, users=list_users(), style=STYLE)


@users_page.post("/module/users/create")
def create_user():
    try:
        add_user(
            request.form.get("full_name", ""),
            request.form.get("username", ""),
            request.form.get("password", ""),
            request.form.get("role", ""),
            request.form.get("status", ""),
        )
        flash("User created successfully.")
    except ValueError as exc:
        flash(str(exc))

    return redirect(url_for("users_page.users"))


@users_page.post("/module/users/delete/<int:user_id>")
def remove_user(user_id):
    delete_user(user_id)
    flash("User deleted.")
    return redirect(url_for("users_page.users"))
