from django.contrib import admin

from apps.billing import models as m


@admin.register(m.BillableService)
class BillableServiceAdmin(admin.ModelAdmin):
    list_display = ("service_code", "name", "price", "tax_rate", "retired")
    search_fields = ("service_code", "name")


@admin.register(m.InsuranceScheme)
class InsuranceSchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "payer_name", "coverage_percent", "retired")


@admin.register(m.PatientInsurance)
class PatientInsuranceAdmin(admin.ModelAdmin):
    list_display = ("patient", "scheme", "policy_number", "is_active")
    list_filter = ("is_active", "scheme")
    search_fields = ("policy_number",)
