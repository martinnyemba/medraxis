"""Aggregated DRF router for the versioned ``/api/v1/`` namespace.

Each domain app exposes a ``register_routes(router)`` callable in its
``api.routers`` module. This keeps API wiring modular: apps own their
endpoints, and this file only composes them.
"""
from rest_framework.routers import DefaultRouter

from apps.billing.api.routers import register_routes as register_billing
from apps.emr.api.routers import register_routes as register_emr
from apps.inventory.api.routers import register_routes as register_inventory
from apps.lis.api.routers import register_routes as register_lis
from apps.pharmacy.api.routers import register_routes as register_pharmacy
from apps.pos.api.routers import register_routes as register_pos
from apps.users.api.routers import register_routes as register_users

router = DefaultRouter()

register_users(router)
register_emr(router)
register_lis(router)
register_inventory(router)
register_pharmacy(router)
register_pos(router)
register_billing(router)

urlpatterns = router.urls
