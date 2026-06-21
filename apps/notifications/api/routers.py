from apps.notifications.api.views import NotificationViewSet, ReportRunViewSet


def register_routes(router):
    router.register("notifications", NotificationViewSet, basename="notification")
    router.register("reports", ReportRunViewSet, basename="report-run")
