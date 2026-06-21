from apps.tenancy.api.views import MembershipViewSet, OrganizationViewSet


def register_routes(router):
    router.register("organizations", OrganizationViewSet, basename="organization")
    router.register("memberships", MembershipViewSet, basename="membership")
