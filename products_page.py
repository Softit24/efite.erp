from flask import Blueprint, request, redirect, render_template_string
from products_db import (
    get_products,
    add_product,
    update_product,
    delete_product,
)

products_page = Blueprint("products", __name__)


@products_page.route("/module/products", methods=["GET", "POST"])
def products():
    message = ""
    editing = None

    if request.method == "POST":
        action = request.form.get("action", "add")
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        price = request.form.get("price", "0")
        quantity = request.form.get("quantity", "0")
        url = request.form.get("url", "").strip()
        fees = request.form.get("installation_fees", "0")
        monthly_fees = request.form.get("monthly_service_fees", "0")

        try:
            if action == "edit":
                product_id = int(request.form.get("product_id", "0"))
                ok, message = update_product(
                    product_id, name, sku, price, quantity,
                    url, fees, monthly_fees
                )
            else:
                ok, message = add_product(
                    name, sku, price, quantity, url,
                    fees, monthly_fees
                )

            if ok:
                status = "updated" if action == "edit" else "added"
                return redirect(f"/module/products?message={status}")

        except (ValueError, TypeError):
            message = "Please enter valid product details."

    status_messages = {
        "added": "Product added successfully.",
        "updated": "Product updated successfully.",
        "deleted": "Product deleted successfully.",
    }
    message = status_messages.get(request.args.get("message"), message)

    all_products = get_products()
    edit_id = request.args.get("edit")

    if edit_id:
        try:
            editing = next(
                (p for p in all_products if int(p["id"]) == int(edit_id)),
                None,
            )
        except (ValueError, TypeError):
            editing = None

    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Products</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #222;
                    background: #f5f7fa;
                }
                h1, h2 { color: #17365d; }
                .panel {
                    background: white;
                    padding: 18px;
                    margin-bottom: 20px;
                    border-radius: 10px;
                }
                .product-form {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                    gap: 12px;
                }
                label { display: block; font-weight: bold; }
                input {
                    box-sizing: border-box;
                    width: 100%;
                    padding: 10px;
                    margin-top: 5px;
                }
                button, .button {
                    display: inline-block;
                    padding: 10px 14px;
                    border: 0;
                    border-radius: 5px;
                    background: #17365d;
                    color: white;
                    text-decoration: none;
                    cursor: pointer;
                }
                .message { color: #176b35; font-weight: bold; }
                .table-wrap { overflow-x: auto; }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }
                th, td {
                    text-align: left;
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                    white-space: nowrap;
                }
                th { background: #e8eef6; }
                .actions { display: flex; gap: 8px; align-items: center; }
                .delete-button { background: #a32626; }
                .cancel { color: #17365d; }
            </style>
        </head>
        <body>
            <h1>Products</h1>

            {% if message %}
                <p class="message">{{ message }}</p>
            {% endif %}

            <section class="panel">
                <h2>{{ "Edit Product" if editing else "Add Product" }}</h2>
                <form class="product-form" method="post" action="/module/products">
                    <input type="hidden" name="action"
                           value="{{ 'edit' if editing else 'add' }}">

                    {% if editing %}
                        <input type="hidden" name="product_id" value="{{ editing['id'] }}">
                    {% endif %}

                    <label>Product Name
                        <input name="name" required
                               value="{{ editing['name'] if editing else '' }}">
                    </label>

                    <label>SKU
                        <input name="sku" required
                               value="{{ editing['sku'] if editing else '' }}">
                    </label>

                    <label>Price
                        <input name="price" type="number" min="0" step="0.01" required
                               value="{{ editing['price'] if editing else 0 }}">
                    </label>

                    <label>Quantity
                        <input name="quantity" type="number" min="0" step="1" required
                               value="{{ editing['quantity'] if editing else 0 }}">
                    </label>

                    <label>URL / IP
                        <input name="url"
                               value="{{ editing['url'] if editing else '' }}">
                    </label>

                    <label>Installation Fees
                        <input name="installation_fees" type="number" min="0"
                               step="0.01" required
                               value="{{ editing['installation_fees'] if editing else 0 }}">
                    </label>

                    <label>Monthly Service Fees
                        <input name="monthly_service_fees" type="number" min="0"
                               step="0.01" required
                               value="{{ editing['monthly_service_fees'] if editing else 0 }}">
                    </label>

                    <div>
                        <button type="submit">
                            {{ "Update Product" if editing else "Add Product" }}
                        </button>
                        {% if editing %}
                            <a class="cancel" href="/module/products">Cancel</a>
                        {% endif %}
                    </div>
                </form>
            </section>

            <section class="panel">
                <h2>Product List</h2>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>SKU</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>URL / IP</th>
                                <th>Installation Fees</th>
                                <th>Monthly Fees</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for p in products %}
                            <tr>
                                <td>{{ p['id'] }}</td>
                                <td>{{ p['name'] }}</td>
                                <td>{{ p['sku'] }}</td>
                                <td>{{ "%.2f"|format(p['price']) }}</td>
                                <td>{{ p['quantity'] }}</td>
                                <td>{{ p['url'] }}</td>
                                <td>{{ "%.2f"|format(p['installation_fees']) }}</td>
                                <td>{{ "%.2f"|format(p['monthly_service_fees']) }}</td>
                                <td>
                                    <div class="actions">
                                        <a class="button"
                                           href="/module/products?edit={{ p['id'] }}">Edit</a>
                                        <form method="post"
                                              action="/module/products/delete/{{ p['id'] }}"
                                              onsubmit="return confirm('Delete this product?');">
                                            <button class="delete-button" type="submit">
                                                Delete
                                            </button>
                                        </form>
                                    </div>
                                </td>
                            </tr>
                        {% else %}
                            <tr>
                                <td colspan="9">No products found.</td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>
        </body>
        </html>
        """,
        products=all_products,
        editing=editing,
        message=message,
    )


@products_page.route("/module/products/delete/<int:product_id>", methods=["POST"])
def remove_product(product_id):
    delete_product(product_id)
    return redirect("/module/products?message=deleted")
