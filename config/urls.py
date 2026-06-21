"""Top-level URL configuration for the Medraxis platform."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Medraxis Unified Healthcare Platform API",
        default_version="v1",
        description=(
            "Integrated EMR (OpenMRS-inspired), LIS/LIMS, Pharmacy, Inventory "
            "and POS/Business operations for clinics, diagnostic centres, "
            "laboratories, pharmacies and medical businesses."
        ),
        contact=openapi.Contact(email="support@medraxis.local"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

api_v1_patterns = [
    # Authentication (JWT).
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Domain resources.
    path("", include("config.api_router")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "api"), namespace="v1")),
    # API documentation.
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
