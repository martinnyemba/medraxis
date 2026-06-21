"""Reusable building blocks for tenant scoping.

* :class:`TenantScopedModel` -- abstract model adding the ``organization`` FK and
  auto-assigning it from the active tenant on first save.
* :func:`scope_to_current_organization` -- filter any queryset to the active
  tenant (no-op when no tenant is set, e.g. superuser/management contexts).
* :class:`TenantResolverMixin` -- resolve and set the active tenant in a DRF
  view's ``initial()`` (after authentication, so the user is known).
* :class:`TenantScopedQuerySetMixin` / :class:`TenantScopedViewSetMixin` -- also
  filter reads and stamp writes.
"""
from django.db import models

from apps.tenancy.context import get_current_organization, set_current_organization
from apps.tenancy.resolution import resolve_request_organization


class TenantScopedModel(models.Model):
    """Adds an ``organization`` FK and auto-stamps it on create.

    The FK is nullable so platform-wide reference data and pre-tenancy rows
    remain valid; isolation is enforced at the API layer.
    """

    organization = models.ForeignKey(
        "tenancy.Organization",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_set",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self._state.adding and self.organization_id is None:
            org = get_current_organization()
            if org is not None:
                self.organization = org
        super().save(*args, **kwargs)


def scope_to_current_organization(queryset):
    """Restrict ``queryset`` to the active tenant when one is set."""
    org = get_current_organization()
    if org is None:
        return queryset
    return queryset.filter(organization=org)


class TenantResolverMixin:
    """Resolve the active tenant once per request, after authentication.

    DRF performs authentication in the view (not middleware), so the tenant must
    be resolved here where ``request.user`` is reliable for both JWT and session
    auth. An inaccessible ``X-Organization`` header fails closed (403).
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        org = resolve_request_organization(request, raise_on_denied=True)
        request.organization = org
        set_current_organization(org)


class TenantScopedQuerySetMixin(TenantResolverMixin):
    """Resolve the tenant and filter list/detail querysets to it."""

    def get_queryset(self):
        return scope_to_current_organization(super().get_queryset())


class TenantScopedViewSetMixin(TenantScopedQuerySetMixin):
    """Also stamp the tenant explicitly on create (belt and braces)."""

    def perform_create(self, serializer):
        serializer.save(organization=get_current_organization())
