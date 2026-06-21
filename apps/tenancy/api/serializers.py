from rest_framework import serializers

from apps.tenancy.models import Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "org_type", "is_active", "legal_name",
                  "tax_identifier", "phone", "email", "address", "currency", "timezone"]


class MembershipSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "username", "organization", "organization_name",
                  "is_default", "is_admin"]
