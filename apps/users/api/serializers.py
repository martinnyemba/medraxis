from rest_framework import serializers

from apps.users.models import Privilege, Provider, Role, User


class PrivilegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Privilege
        fields = ["id", "name", "description"]


class RoleSerializer(serializers.ModelSerializer):
    privileges = serializers.SlugRelatedField(
        slug_field="name", queryset=Privilege.objects.all(), many=True, required=False
    )

    class Meta:
        model = Role
        fields = ["id", "name", "description", "privileges", "inherited_roles"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(
        slug_field="name", queryset=Role.objects.all(), many=True, required=False
    )
    privileges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "is_active",
            "is_staff",
            "is_system_account",
            "roles",
            "privileges",
        ]
        read_only_fields = ["is_staff"]

    def get_privileges(self, obj):
        return sorted(obj.privilege_names())


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = [
            "id",
            "uuid",
            "name",
            "identifier",
            "provider_role",
            "person",
            "user",
            "retired",
        ]
        read_only_fields = ["uuid", "retired"]
