from django.contrib import admin

from apps.finance import models as m


@admin.register(m.FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_type", "current_balance", "is_default", "retired")
    list_filter = ("account_type", "is_default")
    search_fields = ("name", "account_number", "bank_name")


@admin.register(m.AccountTransaction)
class AccountTransactionAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "account", "direction", "amount", "balance_after",
                    "reference_type")
    list_filter = ("direction", "account")
    date_hierarchy = "occurred_at"


@admin.register(m.Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "amount", "tax_amount", "expense_date", "account")
    list_filter = ("category",)
    date_hierarchy = "expense_date"
    search_fields = ("number", "note")


class SupplierPaymentAllocationInline(admin.TabularInline):
    model = m.SupplierPaymentAllocation
    extra = 0


@admin.register(m.SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ("number", "supplier", "amount", "paid_on", "method", "account")
    date_hierarchy = "paid_on"
    inlines = [SupplierPaymentAllocationInline]
    search_fields = ("number",)


@admin.register(m.PartyLedgerEntry)
class PartyLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_date", "party_content_type", "party_object_id",
                    "entry_type", "debit", "credit", "balance")
    list_filter = ("entry_type", "party_content_type")
    date_hierarchy = "entry_date"


class TaxComponentInline(admin.TabularInline):
    model = m.TaxComponent
    extra = 1


@admin.register(m.ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "retired")
    search_fields = ("name",)
