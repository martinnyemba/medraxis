"""FHIR R4 facade URLs, mounted at ``/fhir/``."""
from django.urls import path

from apps.fhir.views import (
    FHIRCapabilityStatementView,
    FHIRReadView,
    FHIRSearchView,
)

app_name = "fhir"

urlpatterns = [
    path("metadata", FHIRCapabilityStatementView.as_view(), name="metadata"),
    path("<str:resource_type>", FHIRSearchView.as_view(), name="search"),
    path("<str:resource_type>/<str:resource_id>", FHIRReadView.as_view(), name="read"),
]
