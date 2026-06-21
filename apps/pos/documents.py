"""PDF receipt / invoice generation for POS sales."""
from apps.core.pdf import PDFBuilder, org_header


def build_receipt_pdf(sale):
    """Render a sale as a printable A4 invoice/receipt and return PDF bytes."""
    builder = PDFBuilder(title=f"Invoice {sale.invoice_number}")
    org_header(builder, sale.organization, document_title="TAX INVOICE / RECEIPT")

    builder.text(f"Invoice: {sale.invoice_number}", size=10, bold=True, dy=13)
    builder.text(f"Date: {sale.created_at:%Y-%m-%d %H:%M}", size=9, dy=13)
    party = sale.patient or sale.customer
    if party is not None:
        builder.text(f"Billed to: {party}", size=9, dy=13)
    builder.text(f"Status: {sale.get_status_display()}", size=9, dy=15)

    # Line items table.
    widths = [0.46, 0.12, 0.16, 0.12, 0.14]
    builder.row(["Item", "Qty", "Unit", "Tax%", "Amount"], widths, bold=True)
    builder.line(6)
    for line in sale.lines.all():
        name = line.description or (line.product.name if line.product_id else line.get_line_type_display())
        builder.row(
            [name[:38], line.quantity, f"{line.unit_price:.2f}",
             f"{line.tax_percent:.1f}", f"{line.line_total:.2f}"],
            widths,
        )
    builder.line(6)

    # Totals.
    builder.right_text(f"Subtotal: {sale.subtotal:.2f} {sale.currency}")
    builder.spacer(13)
    builder.right_text(f"Discount: {sale.discount_total:.2f}")
    builder.spacer(13)
    builder.right_text(f"Tax: {sale.tax_total:.2f}")
    builder.spacer(13)
    builder.right_text(f"Grand total: {sale.grand_total:.2f} {sale.currency}")
    builder.spacer(13)
    builder.right_text(f"Paid: {sale.amount_paid:.2f}")
    builder.spacer(13)
    builder.right_text(f"Balance due: {sale.balance_due:.2f}")
    builder.spacer(20)

    if sale.payments.exists():
        builder.text("Payments", size=10, bold=True, dy=14)
        for payment in sale.payments.all():
            builder.text(
                f"  {payment.created_at:%Y-%m-%d %H:%M}  {payment.get_method_display()}  "
                f"{payment.amount:.2f}  {payment.reference}", size=8, dy=11
            )

    builder.spacer(16)
    builder.text("Thank you for your business.", size=9, dy=12)
    return builder.render()
