from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.api.serializers import NotificationSerializer, ReportRunSerializer
from apps.notifications.models import Notification, ReportRun
from apps.notifications.reports import REPORT_REGISTRY
from apps.tenancy.mixins import TenantResolverMixin


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """The authenticated user's own notifications (in-app inbox)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["channel", "status"]

    def get_queryset(self):
        return Notification.objects.filter(recipient_user=self.request.user)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        qs = self.get_queryset().exclude(status=Notification.Status.READ)
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.status = Notification.Status.READ
        notification.save(update_fields=["status"])
        return Response(self.get_serializer(notification).data)


class ReportRunViewSet(TenantResolverMixin, viewsets.ModelViewSet):
    """Request and track asynchronous report generation."""

    serializer_class = ReportRunSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["report_type", "status"]

    def get_queryset(self):
        qs = ReportRun.objects.all()
        org = getattr(self.request, "organization", None)
        if org is not None and not self.request.user.is_superuser:
            qs = qs.filter(organization=org)
        return qs

    def create(self, request, *args, **kwargs):
        report_type = request.data.get("report_type")
        if report_type not in REPORT_REGISTRY:
            raise ValidationError(
                {"report_type": f"Must be one of: {', '.join(sorted(REPORT_REGISTRY))}"}
            )
        report_run = ReportRun.objects.create(
            report_type=report_type,
            parameters=request.data.get("parameters", {}) or {},
            requested_by=request.user,
            organization=getattr(request, "organization", None),
        )
        # Kick off async generation (runs inline in eager mode).
        from apps.notifications.tasks import generate_report_task

        generate_report_task.delay(report_run.id)
        report_run.refresh_from_db()
        serializer = self.get_serializer(report_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def types(self, request):
        return Response({"report_types": sorted(REPORT_REGISTRY)})
