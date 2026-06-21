"""PDF generation for the lab: specimen labels and patient result reports."""
from reportlab.lib.units import mm

from apps.core.pdf import PDFBuilder, org_header


def build_specimen_label_pdf(specimen):
    """Render a compact specimen label (accession, patient, type, date).

    Uses a small label-sized page suitable for a thermal label printer.
    """
    label_size = (62 * mm, 40 * mm)
    builder = PDFBuilder(pagesize=label_size, margin=4 * mm,
                         title=f"Label {specimen.accession_number}")
    builder.text(specimen.accession_number, size=12, bold=True, dy=14)
    patient = specimen.patient
    name = patient.person.preferred_name if patient and patient.person_id else ""
    builder.text(str(name)[:28], size=9, dy=11)
    builder.text(f"Type: {specimen.specimen_type.name}", size=8, dy=10)
    builder.text(f"Status: {specimen.get_status_display()}", size=8, dy=10)
    if specimen.collected_at:
        builder.text(f"Collected: {specimen.collected_at:%Y-%m-%d %H:%M}", size=7, dy=10)
    return builder.render()


def build_lab_report_pdf(test_order):
    """Render a patient-facing lab report for a test order's released results."""
    builder = PDFBuilder(title=f"Lab Report {test_order.order_number}")
    org_header(builder, getattr(test_order, "organization", None),
               document_title="LABORATORY REPORT")

    patient = test_order.patient
    name = patient.person.preferred_name if patient and patient.person_id else ""
    builder.text(f"Patient: {name}", size=10, bold=True, dy=13)
    identifier = patient.preferred_identifier if patient else None
    if identifier is not None:
        builder.text(f"ID: {identifier.identifier}", size=9, dy=13)
    builder.text(f"Order: {test_order.order_number}", size=9, dy=13)
    builder.text(f"Test: {test_order.lab_test.name}", size=9, dy=15)

    widths = [0.36, 0.18, 0.14, 0.22, 0.10]
    builder.row(["Analyte", "Result", "Units", "Reference", "Flag"], widths, bold=True)
    builder.line(6)
    for result in test_order.results.select_related("analyte").all():
        value = result.value_numeric if result.value_numeric is not None else result.value_text
        builder.row(
            [result.analyte.name[:30], value, result.units,
             result.reference_range[:18], result.get_flag_display() if result.flag else ""],
            widths,
        )
    builder.line(8)
    builder.text("This report was generated electronically by Medraxis.", size=8, dy=12)
    return builder.render()
