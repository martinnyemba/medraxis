from django.contrib import admin

from apps.payments import models as m


@admin.register(m.PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "is_active", "is_test", "currency",
                    "settlement_account")
    list_filter = ("provider", "is_active", "is_test")


@admin.register(m.PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("reference", "gateway", "amount", "currency", "channel",
                    "status", "sale", "created_at")
    list_filter = ("status", "channel", "gateway")
    search_fields = ("reference", "provider_reference", "customer_email")
    date_hierarchy = "created_at"


@admin.register(m.WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "provider", "event_type", "signature_valid",
                    "processed", "intent")
    list_filter = ("provider", "signature_valid", "processed")
    readonly_fields = ("payload",)
