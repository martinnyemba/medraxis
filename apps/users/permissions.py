"""DRF permission classes built on OpenMRS-style privileges."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasPrivilege(BasePermission):
    """Require a named privilege, declared on the view as ``required_privilege``.

    Optionally a view may declare ``required_privilege_map`` to require
    different privileges for read vs write::

        required_privilege_map = {"read": "View Patients", "write": "Edit Patients"}
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        privilege_map = getattr(view, "required_privilege_map", None)
        if privilege_map:
            key = "read" if request.method in SAFE_METHODS else "write"
            required = privilege_map.get(key)
        else:
            required = getattr(view, "required_privilege", None)

        if not required:
            return True
        return user.has_privilege(required)
