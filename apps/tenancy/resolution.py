"""Resolve the active organization for a request.

Resolution order:

1. ``X-Organization`` header carrying an organization slug (API clients).
2. The authenticated user's default :class:`Membership`.
3. The user's first membership.

Superusers may target any organization via the header; other users are limited
to organizations they belong to. An explicit header naming an inaccessible
organization fails closed (raises ``PermissionDenied`` when ``raise_on_denied``).
"""
from rest_framework.exceptions import PermissionDenied

HEADER_META = "HTTP_X_ORGANIZATION"


def resolve_request_organization(request, *, raise_on_denied=False):
    from apps.tenancy.models import Membership, Organization

    user = getattr(request, "user", None)
    slug = request.META.get(HEADER_META)

    if slug:
        org = Organization.objects.filter(slug=slug, is_active=True).first()
        authorized = (
            org is not None
            and user is not None
            and user.is_authenticated
            and (user.is_superuser
                 or Membership.objects.filter(user=user, organization=org).exists())
        )
        if authorized:
            return org
        if raise_on_denied:
            raise PermissionDenied(
                f"You do not have access to organization '{slug}'."
            )
        return None

    if user is None or not user.is_authenticated:
        return None

    membership = (
        Membership.objects.filter(user=user, organization__is_active=True)
        .select_related("organization")
        .order_by("-is_default", "id")
        .first()
    )
    return membership.organization if membership else None
