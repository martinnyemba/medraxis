from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import (
    Privilege,
    Provider,
    ProviderAttributeType,
    Role,
    User,
)


@admin.register(Privilege)
class PrivilegeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    filter_horizontal = ("privileges", "inherited_roles")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "is_staff", "is_active", "is_system_account")
    list_filter = ("is_staff", "is_active", "is_system_account", "roles")
    filter_horizontal = ("groups", "user_permissions", "roles")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Medraxis", {"fields": ("roles", "phone", "is_system_account", "force_password_change")}),
    )


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier", "provider_role", "user", "retired")
    list_filter = ("provider_role", "retired")
    search_fields = ("name", "identifier")


@admin.register(ProviderAttributeType)
class ProviderAttributeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "datatype", "min_occurs", "max_occurs", "retired")
    search_fields = ("name",)
