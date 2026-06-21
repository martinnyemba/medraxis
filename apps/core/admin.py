from django.contrib import admin

from apps.core.models import AuditLog, GlobalProperty


@admin.register(GlobalProperty)
class GlobalPropertyAdmin(admin.ModelAdmin):
    list_display = ("property", "property_value", "datatype", "updated_at")
    search_fields = ("property", "description")
    list_filter = ("datatype",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "model_name", "object_pk", "ip_address")
    list_filter = ("action", "model_name")
    search_fields = ("model_name", "object_pk", "description", "request_id")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
