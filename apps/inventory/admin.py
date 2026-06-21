from django.contrib import admin

from apps.inventory import models as m


@admin.register(m.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "is_drug", "sale_price", "quantity_on_hand", "retired")
    list_filter = ("is_drug", "is_controlled", "category", "retired")
    search_fields = ("sku", "name", "barcode")


@admin.register(m.StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "batch_number", "expiry_date", "quantity_on_hand")
    list_filter = ("location",)
    search_fields = ("product__sku", "batch_number")


@admin.register(m.StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "transaction_type", "quantity", "location")
    list_filter = ("transaction_type", "location")
    date_hierarchy = "created_at"


class PurchaseOrderItemInline(admin.TabularInline):
    model = m.PurchaseOrderItem
    extra = 1


@admin.register(m.PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "status", "expected_date")
    list_filter = ("status",)
    inlines = [PurchaseOrderItemInline]


for model in (m.ProductCategory, m.UnitOfMeasure, m.TaxRate, m.Supplier):
    admin.site.register(model)


class PurchaseBillItemInline(admin.TabularInline):
    model = m.PurchaseBillItem
    extra = 0


@admin.register(m.PurchaseBill)
class PurchaseBillAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "supplier", "bill_date", "grand_total",
                    "amount_paid", "status")
    list_filter = ("status",)
    search_fields = ("bill_number", "supplier_invoice_no")
    inlines = [PurchaseBillItemInline]
    date_hierarchy = "bill_date"
