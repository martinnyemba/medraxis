from django.contrib import admin

from apps.notifications.models import Notification, NotificationTemplate, ReportRun


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "default_channel", "description")
    search_fields = ("code", "description")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "channel", "recipient_address", "status", "subject")
    list_filter = ("channel", "status")
    search_fields = ("recipient_address", "subject", "dedupe_key")
    date_hierarchy = "created_at"


@admin.register(ReportRun)
class ReportRunAdmin(admin.ModelAdmin):
    list_display = ("created_at", "report_type", "status", "row_count", "requested_by")
    list_filter = ("report_type", "status")
    date_hierarchy = "created_at"
