from apps.users.api.views import (
    PrivilegeViewSet,
    ProviderViewSet,
    RoleViewSet,
    UserViewSet,
)


def register_routes(router):
    router.register("users", UserViewSet, basename="user")
    router.register("roles", RoleViewSet, basename="role")
    router.register("privileges", PrivilegeViewSet, basename="privilege")
    router.register("providers", ProviderViewSet, basename="provider")
