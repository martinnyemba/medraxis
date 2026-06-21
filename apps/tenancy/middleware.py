"""Tenant lifecycle for non-DRF (session/admin) requests.

For Django session-authenticated requests (e.g. the admin), ``request.user`` is
already populated here, so we resolve the tenant eagerly. For DRF API requests,
authentication happens later in the view, so resolution is deferred to
:class:`apps.tenancy.mixins.TenantResolverMixin`; this middleware only
guarantees the thread-local is cleared at the end of every request.
"""
from apps.tenancy.context import clear_current_organization, set_current_organization
from apps.tenancy.resolution import resolve_request_organization


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        organization = None
        if user is not None and getattr(user, "is_authenticated", False):
            organization = resolve_request_organization(request, raise_on_denied=False)
        request.organization = organization
        set_current_organization(organization)
        try:
            return self.get_response(request)
        finally:
            clear_current_organization()
