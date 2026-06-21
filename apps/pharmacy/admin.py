from django.contrib import admin

from apps.pharmacy import models as m


@admin.register(m.DrugOrder)
class DrugOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "patient", "drug", "quantity", "fulfiller_status")
    search_fields = ("order_number",)
    list_filter = ("fulfiller_status",)


@admin.register(m.Dispense)
class DispenseAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "patient", "quantity", "unit_price", "status")
    list_filter = ("status", "location")
    date_hierarchy = "created_at"
