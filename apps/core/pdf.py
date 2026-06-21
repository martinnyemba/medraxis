"""Shared PDF building helpers (reportlab).

Thin wrappers that keep the layout primitives in one place so document builders
across apps (receipts, specimen labels, lab reports) stay consistent and small.
Each public builder returns raw PDF ``bytes`` suitable for an HTTP response.
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class PDFBuilder:
    """A tiny stateful helper around a reportlab canvas with a text cursor."""

    def __init__(self, pagesize=A4, margin=18 * mm, title="Document"):
        self.buffer = io.BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=pagesize)
        self.canvas.setTitle(title)
        self.width, self.height = pagesize
        self.margin = margin
        self.y = self.height - margin

    def text(self, text, *, size=10, bold=False, dy=14, x=None):
        self.canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.canvas.drawString(x if x is not None else self.margin, self.y, str(text))
        self.y -= dy
        return self

    def right_text(self, text, *, size=10, bold=False):
        self.canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.canvas.drawRightString(self.width - self.margin, self.y, str(text))
        return self

    def line(self, dy=8):
        self.canvas.line(self.margin, self.y, self.width - self.margin, self.y)
        self.y -= dy
        return self

    def spacer(self, dy=8):
        self.y -= dy
        return self

    def row(self, columns, widths, *, size=9, bold=False):
        """Draw a tabular row. ``columns`` and ``widths`` (fractions) align left."""
        self.canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        x = self.margin
        usable = self.width - 2 * self.margin
        for value, frac in zip(columns, widths):
            self.canvas.drawString(x, self.y, str(value))
            x += usable * frac
        self.y -= 13
        return self

    def render(self):
        self.canvas.showPage()
        self.canvas.save()
        return self.buffer.getvalue()


def org_header(builder, organization, *, document_title=""):
    """Render a branded header from an Organization (falls back gracefully)."""
    name = getattr(organization, "name", "Medraxis")
    builder.text(name, size=15, bold=True, dy=16)
    legal = getattr(organization, "legal_name", "")
    if legal:
        builder.text(legal, size=9, dy=12)
    contact = " | ".join(
        p for p in [getattr(organization, "phone", ""),
                    getattr(organization, "email", ""),
                    getattr(organization, "tax_identifier", "")] if p
    )
    if contact:
        builder.text(contact, size=8, dy=12)
    if document_title:
        builder.spacer(4)
        builder.text(document_title, size=12, bold=True, dy=16)
    builder.line()
    return builder
