"""Tests for the additional OpenMRS core domain models."""
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.emr.models import (
    Allergy,
    AllergyReaction,
    Cohort,
    CohortMembership,
    Concept,
    ConceptClass,
    ConceptDatatype,
    Drug,
    DrugIngredient,
    OrderFrequency,
    Patient,
    Person,
    Relationship,
    RelationshipType,
    VisitAttribute,
    VisitAttributeType,
    VisitType,
    Visit,
)
from apps.users.models import User


class RelationshipTests(TestCase):
    def test_directional_relationship(self):
        rtype = RelationshipType.objects.create(
            name="Parent/Child", a_is_to_b="Parent", b_is_to_a="Child")
        parent = Person.objects.create(gender="F")
        child = Person.objects.create(gender="M")
        rel = Relationship.objects.create(
            person_a=parent, person_b=child, relationship_type=rtype)
        # Readable from both directions via related names.
        self.assertEqual(parent.relationships_as_a.count(), 1)
        self.assertEqual(child.relationships_as_b.count(), 1)
        self.assertEqual(rel.relationship_type.b_is_to_a, "Child")


class DrugFormulationTests(TestCase):
    def test_drug_with_ingredients(self):
        drug_class = ConceptClass.objects.create(name="Drug")
        text = ConceptDatatype.objects.create(name="Text")
        amox_concept = Concept.objects.create(
            name="Amoxicillin", concept_class=drug_class, datatype=text)
        clav = Concept.objects.create(
            name="Clavulanic acid", concept_class=drug_class, datatype=text)
        drug = Drug.objects.create(
            name="Co-amoxiclav 625mg", concept=amox_concept, combination=True,
            strength="500mg/125mg")
        DrugIngredient.objects.create(drug=drug, ingredient=amox_concept, strength=500)
        DrugIngredient.objects.create(drug=drug, ingredient=clav, strength=125)
        self.assertEqual(drug.ingredients.count(), 2)


class AllergyReactionTests(TestCase):
    def test_multiple_coded_reactions(self):
        klass = ConceptClass.objects.create(name="Finding")
        coded = ConceptDatatype.objects.create(name="Coded")
        allergen = Concept.objects.create(
            name="Penicillin", concept_class=klass, datatype=coded)
        rash = Concept.objects.create(name="Rash", concept_class=klass, datatype=coded)
        anaph = Concept.objects.create(name="Anaphylaxis", concept_class=klass, datatype=coded)
        person = Person.objects.create(gender="M")
        patient = Patient.objects.create(person=person)
        allergy = Allergy.objects.create(patient=patient, allergen=allergen)
        AllergyReaction.objects.create(allergy=allergy, reaction=rash)
        AllergyReaction.objects.create(allergy=allergy, reaction=anaph)
        self.assertEqual(allergy.reactions.count(), 2)


class VisitAttributeTests(TestCase):
    def test_custom_visit_attribute(self):
        attr_type = VisitAttributeType.objects.create(
            name="Bed number", datatype="str", max_occurs=1)
        person = Person.objects.create(gender="F")
        patient = Patient.objects.create(person=person)
        vtype = VisitType.objects.create(name="Inpatient")
        from django.utils import timezone
        visit = Visit.objects.create(
            patient=patient, visit_type=vtype, started_at=timezone.now())
        VisitAttribute.objects.create(
            visit=visit, attribute_type=attr_type, value_reference="Ward-3 Bed-12")
        self.assertEqual(visit.attributes.first().value_reference, "Ward-3 Bed-12")
        self.assertTrue(attr_type.required is False)


class CohortTests(TestCase):
    def test_cohort_membership_count(self):
        cohort = Cohort.objects.create(name="ART patients")
        for _ in range(3):
            person = Person.objects.create(gender="F")
            patient = Patient.objects.create(person=person)
            CohortMembership.objects.create(cohort=cohort, patient=patient)
        self.assertEqual(cohort.memberships.count(), 3)


class NewModelApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", "u@x.io", "pw-strong-123")

    def test_drug_and_relationship_endpoints_exist(self):
        self.client.force_authenticate(self.user)
        for path in ["/api/v1/drugs/", "/api/v1/relationships/",
                     "/api/v1/relationship-types/", "/api/v1/cohorts/",
                     "/api/v1/forms/", "/api/v1/order-frequencies/"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"{path}: {resp.status_code}")
