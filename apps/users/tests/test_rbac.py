"""Tests for role/privilege inheritance and the HasPrivilege permission gate."""
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.emr.models import Concept, ConceptClass, ConceptDatatype
from apps.users.models import Privilege, Role, User


class RoleInheritanceTests(TestCase):
    def test_all_privileges_aggregates_inherited_roles(self):
        view_p = Privilege.objects.create(name="View Concepts")
        manage_p = Privilege.objects.create(name="Manage Concepts")

        data_entry = Role.objects.create(name="Data Entry")
        data_entry.privileges.add(view_p)

        clinician = Role.objects.create(name="Clinician")
        clinician.privileges.add(manage_p)
        clinician.inherited_roles.add(data_entry)

        self.assertEqual(clinician.all_privileges(), {view_p, manage_p})
        self.assertEqual(data_entry.all_privileges(), {view_p})

    def test_all_privileges_handles_inheritance_cycles(self):
        role_a = Role.objects.create(name="A")
        role_b = Role.objects.create(name="B")
        role_a.inherited_roles.add(role_b)
        role_b.inherited_roles.add(role_a)

        # Must terminate rather than recurse forever.
        self.assertEqual(role_a.all_privileges(), set())


class HasPrivilegeUserMethodTests(TestCase):
    def test_user_without_role_lacks_privilege(self):
        user = User.objects.create_user("plain", "plain@x.io", "pw-strong-123")
        self.assertFalse(user.has_privilege("View Concepts"))

    def test_user_with_role_has_privilege(self):
        privilege = Privilege.objects.create(name="View Concepts")
        role = Role.objects.create(name="Viewer")
        role.privileges.add(privilege)
        user = User.objects.create_user("viewer", "viewer@x.io", "pw-strong-123")
        user.roles.add(role)
        self.assertTrue(user.has_privilege("View Concepts"))

    def test_superuser_bypasses_privilege_checks(self):
        superuser = User.objects.create_superuser("root", "root@x.io", "pw-strong-123")
        self.assertTrue(superuser.has_privilege("Anything At All"))


class HasPrivilegeApiTests(APITestCase):
    """Exercises HasPrivilege through ConceptViewSet's required_privilege_map."""

    def setUp(self):
        self.view_privilege = Privilege.objects.create(name="View Concepts")
        self.manage_privilege = Privilege.objects.create(name="Manage Concepts")

        self.viewer_role = Role.objects.create(name="Viewer")
        self.viewer_role.privileges.add(self.view_privilege)

        self.manager_role = Role.objects.create(name="Manager")
        self.manager_role.privileges.add(self.view_privilege, self.manage_privilege)

        self.viewer = User.objects.create_user("rbac-viewer", "v@x.io", "pw-strong-123")
        self.viewer.roles.add(self.viewer_role)

        self.manager = User.objects.create_user("rbac-manager", "m@x.io", "pw-strong-123")
        self.manager.roles.add(self.manager_role)

        klass = ConceptClass.objects.create(name="Finding")
        datatype = ConceptDatatype.objects.create(name="Coded")
        self.concept = Concept.objects.create(name="Fever", concept_class=klass, datatype=datatype)

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/v1/concepts/")
        self.assertEqual(resp.status_code, 401)

    def test_read_requires_view_privilege(self):
        no_privilege_user = User.objects.create_user("none", "none@x.io", "pw-strong-123")
        self.client.force_authenticate(no_privilege_user)
        resp = self.client.get("/api/v1/concepts/")
        self.assertEqual(resp.status_code, 403)

    def test_viewer_can_read(self):
        self.client.force_authenticate(self.viewer)
        resp = self.client.get("/api/v1/concepts/")
        self.assertEqual(resp.status_code, 200)

    def test_viewer_cannot_write(self):
        self.client.force_authenticate(self.viewer)
        resp = self.client.post("/api/v1/concepts/", {
            "name": "Cough",
            "concept_class": self.concept.concept_class_id,
            "datatype": self.concept.datatype_id,
        })
        self.assertEqual(resp.status_code, 403)

    def test_manager_can_write(self):
        self.client.force_authenticate(self.manager)
        resp = self.client.post("/api/v1/concepts/", {
            "name": "Cough",
            "concept_class": self.concept.concept_class_id,
            "datatype": self.concept.datatype_id,
        })
        self.assertEqual(resp.status_code, 201, resp.content)
