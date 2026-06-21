from rest_framework import serializers

from apps.finance import models as m


class FinancialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.FinancialAccount
        fields = ["id", "uuid", "name", "account_type", "account_number", "bank_name",
                  "opening_balance", "current_balance", "is_default", "retired"]
        read_only_fields = ["uuid", "current_balance", "retired"]


class AccountTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AccountTransaction
        fields = ["id", "account", "direction", "amount", "balance_after",
                  "reference_type", "reference_id", "note", "occurred_at"]
        read_only_fields = fields


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ExpenseCategory
        fields = ["id", "uuid", "name", "description", "retired"]
        read_only_fields = ["uuid", "retired"]


class ExpenseSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model = m.Expense
        fields = ["id", "number", "category", "account", "supplier", "amount",
                  "tax_amount", "total", "expense_date", "payment_method", "note"]
        read_only_fields = ["number", "total"]


class SupplierPaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.SupplierPaymentAllocation
        fields = ["id", "purchase_bill", "amount"]


class SupplierPaymentSerializer(serializers.ModelSerializer):
    allocations = SupplierPaymentAllocationSerializer(many=True, required=False)

    class Meta:
        model = m.SupplierPayment
        fields = ["id", "number", "supplier", "account", "amount", "paid_on",
                  "method", "reference", "note", "allocations"]
        read_only_fields = ["number"]


class PartyLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PartyLedgerEntry
        fields = ["id", "entry_type", "entry_date", "debit", "credit", "balance",
                  "reference_type", "reference_id", "narration"]
        read_only_fields = fields


class TaxComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.TaxComponent
        fields = ["id", "tax_rate", "component_type", "rate_percent"]
