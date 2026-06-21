"""Shared serializer base classes."""
from rest_framework import serializers


class AuditReadOnlyMixin(serializers.ModelSerializer):
    """Marks system-managed audit fields read-only on the API surface."""

    class Meta:
        read_only_fields = (
            "uuid",
            "created_at",
            "creator",
            "changed_at",
            "changed_by",
            "voided",
            "voided_at",
            "voided_by",
            "retired",
            "retired_at",
            "retired_by",
        )
