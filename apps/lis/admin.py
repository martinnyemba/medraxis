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


@admin.register(m.AnalyzerMessage)
class AnalyzerMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "protocol", "analyzer", "status",
                    "results_matched", "results_unmatched")
    list_filter = ("protocol", "status")
    date_hierarchy = "created_at"
    readonly_fields = ("raw_payload", "log", "results_matched", "results_unmatched")


class SensitivityResultInline(admin.TabularInline):
    model = m.SensitivityResult
    extra = 1


@admin.register(m.MicrobiologyResult)
class MicrobiologyResultAdmin(admin.ModelAdmin):
    list_display = ("test_order", "growth", "organism", "status")
    list_filter = ("growth", "status")
    inlines = [SensitivityResultInline]


@admin.register(m.ReferenceRange)
class ReferenceRangeAdmin(admin.ModelAdmin):
    list_display = ("lab_test", "analyte", "sex", "age_min_days", "age_max_days",
                    "low_normal", "hi_normal")
    list_filter = ("sex",)


@admin.register(m.QCResult)
class QCResultAdmin(admin.ModelAdmin):
    list_display = ("run_at", "qc_material", "measured_value", "z_score",
                    "westgard_rule", "accepted")
    list_filter = ("accepted", "westgard_rule")
    date_hierarchy = "run_at"


@admin.register(m.ReportDelivery)
class ReportDeliveryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "test_order", "channel", "recipient_type", "status")
    list_filter = ("channel", "status", "recipient_type")


@admin.register(m.CollectionAppointment)
class CollectionAppointmentAdmin(admin.ModelAdmin):
    list_display = ("scheduled_for", "patient", "collection_center",
                    "is_home_collection", "status")
    list_filter = ("status", "is_home_collection")
    date_hierarchy = "scheduled_for"


for model in (
    m.LabSection, m.SpecimenType, m.Analyzer, m.Worklist,
    m.TestMethod, m.TestProfile, m.ReportTemplate,
    m.ReferringDoctor, m.Client, m.PriceList, m.CollectionCenter, m.ReferenceLab,
    m.Organism, m.Antibiotic, m.QCMaterial, m.AutoVerificationRule,
):
    admin.site.register(model)
