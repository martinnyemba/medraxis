from django.contrib import admin

from apps.lis import models as m


@admin.register(m.LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("test_code", "name", "section", "is_panel", "price", "turnaround_hours")
    list_filter = ("section", "is_panel")
    search_fields = ("test_code", "name", "loinc_code")


@admin.register(m.Specimen)
class SpecimenAdmin(admin.ModelAdmin):
    list_display = ("accession_number", "patient", "specimen_type", "status", "collected_at")
    list_filter = ("status", "specimen_type")
    search_fields = ("accession_number",)


@admin.register(m.LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("test_order", "analyte", "value_numeric", "flag", "status")
    list_filter = ("status", "flag")


@admin.register(m.TestOrder)
class TestOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "patient", "lab_test", "fulfiller_status")
    search_fields = ("order_number",)


for model in (m.LabSection, m.SpecimenType, m.Analyzer, m.Worklist):
    admin.site.register(model)
