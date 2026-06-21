from django.contrib import admin

from apps.pos import models as m


class SaleLineInline(admin.TabularInline):
    model = m.SaleLine
    extra = 0


class PaymentInline(admin.TabularInline):
    model = m.Payment
    extra = 0


@admin.register(m.Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "status", "patient", "customer", "client",
                    "grand_total", "amount_paid", "created_at")
    list_filter = ("status", "location")
    search_fields = ("invoice_number",)
    inlines = [SaleLineInline, PaymentInline]
    date_hierarchy = "created_at"


@admin.register(m.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "patient")
    search_fields = ("name", "phone", "email")


@admin.register(m.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "sale", "method", "amount", "status")
    list_filter = ("method", "status")


class QuotationLineInline(admin.TabularInline):
    model = m.QuotationLine
    extra = 0


@admin.register(m.Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("quotation_number", "status", "customer", "client", "grand_total",
                    "converted_sale")
    list_filter = ("status",)
    inlines = [QuotationLineInline]


class SalesReturnLineInline(admin.TabularInline):
    model = m.SalesReturnLine
    extra = 0


@admin.register(m.SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = ("return_number", "sale", "return_date", "total", "status", "restock")
    list_filter = ("status", "restock")
    inlines = [SalesReturnLineInline]
