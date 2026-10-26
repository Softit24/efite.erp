import io
import sqlite3
from flask import Blueprint, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from products_db import init_db
from sales_db import init_sales_db

pdf_reports = Blueprint("pdf_reports", __name__)

@pdf_reports.route("/module/reports/download-pdf")
def download_report_pdf():
    init_db()
    init_sales_db()

    with sqlite3.connect("efite.db") as con:
        con.row_factory = sqlite3.Row
        products = con.execute(
            "SELECT name, sku, price, quantity FROM products ORDER BY name"
        ).fetchall()
        summary = con.execute("""
            SELECT COUNT(*) AS sales_count,
                   COALESCE(SUM(quantity), 0) AS units_sold,
                   COALESCE(SUM(total), 0) AS revenue
            FROM sales
        """).fetchone()
        sales = con.execute("""
            SELECT sale_date, product_name, quantity, total
            FROM sales ORDER BY id DESC LIMIT 10
        """).fetchall()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("EFITE Business ERP — Reports", styles["Title"]),
        Spacer(1, 6*mm),
        Paragraph(
            f"Sales: {summary['sales_count']} | "
            f"Units sold: {summary['units_sold']} | "
            f"Revenue: {float(summary['revenue']):.2f}",
            styles["Normal"]
        ),
        Spacer(1, 5*mm),
        Paragraph("Inventory Status", styles["Heading2"])
    ]

    inventory = [["Product", "SKU", "Stock", "Unit Price", "Status"]]
    for p in products:
        qty = int(p["quantity"] or 0)
        inventory.append([
            str(p["name"]), str(p["sku"] or ""), str(qty),
            f"{float(p['price'] or 0):.2f}",
            "Low stock" if qty <= 5 else "In stock"
        ])
    table = Table(inventory, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 6*mm),
                  Paragraph("Recent Sales", styles["Heading2"])])

    recent = [["Date", "Product", "Quantity", "Total"]]
    for s in sales:
        recent.append([
            str(s["sale_date"]), str(s["product_name"]),
            str(s["quantity"]), f"{float(s['total'] or 0):.2f}"
        ])
    table = Table(recent, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return send_file(
        buffer, mimetype="application/pdf", as_attachment=True,
        download_name="efite_business_report.pdf"
    )
