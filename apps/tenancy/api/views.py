from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.tenancy.api.serializers import MembershipSerializer, OrganizationSerializer
from apps.tenancy.mixins import TenantResolverMixin
from apps.tenancy.models import Membership, Organization


class OrganizationViewSet(TenantResolverMixin, viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "slug", "legal_name"]
    filterset_fields = ["org_type", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        # Non-superusers only see organizations they belong to.
        return qs.filter(memberships__user=user).distinct()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Return the organization resolved for this request, if any."""
        org = getattr(request, "organization", None)
        if org is None:
            return Response({"organization": None})
        return Response(self.get_serializer(org).data)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        """List organizations the authenticated user belongs to."""
        orgs = Organization.objects.filter(memberships__user=request.user).distinct()
        return Response(self.get_serializer(orgs, many=True).data)


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("user", "organization")
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["user", "organization", "is_default", "is_admin"]
