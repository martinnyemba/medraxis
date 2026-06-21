from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.users.api.serializers import (
    PrivilegeSerializer,
    ProviderSerializer,
    RoleSerializer,
    UserSerializer,
)
from apps.users.models import Privilege, Provider, Role, User


class PrivilegeViewSet(viewsets.ModelViewSet):
    queryset = Privilege.objects.all()
    serializer_class = PrivilegeSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "description"]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related("privileges", "inherited_roles")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "description"]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("roles__privileges")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["username", "email", "first_name", "last_name"]
    filterset_fields = ["is_active", "is_staff", "is_system_account"]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return the authenticated user's account and effective privileges."""
        return Response(self.get_serializer(request.user).data)


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.select_related("person", "user")
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "identifier", "provider_role"]
    filterset_fields = ["provider_role", "retired"]
