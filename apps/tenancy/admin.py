from django.contrib import admin

from apps.tenancy.models import Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    autocomplete_fields = ("user",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "org_type", "is_active", "currency")
    list_filter = ("org_type", "is_active")
    search_fields = ("name", "slug", "legal_name", "tax_identifier")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "is_default", "is_admin")
    list_filter = ("is_default", "is_admin", "organization")
    search_fields = ("user__username", "organization__name")
