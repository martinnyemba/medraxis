"""Thread-local storage for the current tenant (organization / facility).

The active organization is set per request by the tenant-resolving mixin (DRF)
or middleware (session/admin) and read by the scoping helpers and the
``TenantScopedModel.save`` auto-stamp, so callers never thread the organization
through every function.
"""
import threading

_state = threading.local()


def set_current_organization(organization):
    _state.organization = organization


def get_current_organization():
    return getattr(_state, "organization", None)


def clear_current_organization():
    _state.organization = None


class organization_context:
    """Run a block scoped to a specific organization.

    Used in management commands, Celery tasks and tests where there is no HTTP
    request to resolve the tenant::

        with organization_context(org):
            Patient.objects.create(...)
    """

    def __init__(self, organization):
        self.organization = organization
        self._previous = None

    def __enter__(self):
        self._previous = get_current_organization()
        set_current_organization(self.organization)
        return self.organization

    def __exit__(self, *exc):
        set_current_organization(self._previous)
        return False
