from django.db import transaction
from rest_framework import serializers

from apps.emr import models as m
from apps.emr.services import generate_patient_identifier


class ConceptSerializer(serializers.ModelSerializer):
    concept_class_name = serializers.CharField(source="concept_class.name", read_only=True)
    datatype_name = serializers.CharField(source="datatype.name", read_only=True)

    class Meta:
        model = m.Concept
        fields = [
            "id", "uuid", "name", "short_name", "concept_class", "concept_class_name",
            "datatype", "datatype_name", "is_set", "units", "hi_normal", "low_normal",
            "hi_critical", "low_critical", "retired",
        ]
        read_only_fields = ["uuid", "retired"]


class PersonNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PersonName
        fields = ["id", "preferred", "prefix", "given_name", "middle_name",
                  "family_name", "family_name_suffix"]


class PatientIdentifierSerializer(serializers.ModelSerializer):
    identifier_type_name = serializers.CharField(
        source="identifier_type.name", read_only=True
    )

    class Meta:
        model = m.PatientIdentifier
        fields = ["id", "identifier_type", "identifier_type_name", "identifier",
                  "location", "preferred"]
        extra_kwargs = {"identifier": {"required": False}}


class PatientSerializer(serializers.ModelSerializer):
    """Read/write serializer that registers a patient + person + name + id atomically."""

    gender = serializers.ChoiceField(
        choices=m.Person.Gender.choices, source="person.gender", required=False
    )
    birthdate = serializers.DateField(source="person.birthdate", required=False, allow_null=True)
    names = PersonNameSerializer(source="person.names", many=True, read_only=True)
    identifiers = PatientIdentifierSerializer(many=True, read_only=True)

    # Write-only convenience fields for quick registration.
    given_name = serializers.CharField(write_only=True, required=False)
    family_name = serializers.CharField(write_only=True, required=False)
    identifier_type = serializers.PrimaryKeyRelatedField(
        queryset=m.PatientIdentifierType.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = m.Patient
        fields = ["id", "uuid", "gender", "birthdate", "names", "identifiers",
                  "allergy_status", "voided", "given_name", "family_name", "identifier_type"]
        read_only_fields = ["uuid", "voided"]

    @transaction.atomic
    def create(self, validated_data):
        person_data = validated_data.pop("person", {})
        given = validated_data.pop("given_name", None)
        family = validated_data.pop("family_name", None)
        id_type = validated_data.pop("identifier_type", None)

        person = m.Person.objects.create(**person_data)
        if given or family:
            m.PersonName.objects.create(
                person=person, given_name=given or "", family_name=family or "", preferred=True
            )
        patient = m.Patient.objects.create(person=person, **validated_data)

        # Auto-assign a primary identifier.
        if id_type is None:
            id_type = m.PatientIdentifierType.objects.filter(required=True).first() \
                or m.PatientIdentifierType.objects.first()
        if id_type is not None:
            m.PatientIdentifier.objects.create(
                patient=patient, identifier_type=id_type,
                identifier=generate_patient_identifier(), preferred=True,
            )
        return patient

    @transaction.atomic
    def update(self, instance, validated_data):
        person_data = validated_data.pop("person", {})
        validated_data.pop("given_name", None)
        validated_data.pop("family_name", None)
        validated_data.pop("identifier_type", None)
        for attr, value in person_data.items():
            setattr(instance.person, attr, value)
        instance.person.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class VisitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VisitType
        fields = ["id", "uuid", "name", "description", "retired"]
        read_only_fields = fields


class EncounterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.EncounterType
        fields = ["id", "uuid", "name", "description", "retired"]
        read_only_fields = fields


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Location
        fields = ["id", "uuid", "name", "description", "parent",
                  "city_village", "country", "retired"]
        read_only_fields = fields


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Visit
        fields = ["id", "uuid", "patient", "visit_type", "location",
                  "started_at", "stopped_at", "voided"]
        read_only_fields = ["uuid", "voided"]


class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Encounter
        fields = ["id", "uuid", "patient", "encounter_type", "visit", "location",
                  "encounter_datetime", "form_reference", "voided"]
        read_only_fields = ["uuid", "voided"]


class ObsSerializer(serializers.ModelSerializer):
    display_value = serializers.ReadOnlyField()

    class Meta:
        model = m.Obs
        fields = ["id", "uuid", "person", "concept", "encounter", "order", "obs_datetime",
                  "location", "obs_group", "value_coded", "value_numeric", "value_text",
                  "value_datetime", "value_boolean", "interpretation", "comments",
                  "status", "display_value", "voided"]
        read_only_fields = ["uuid", "voided", "display_value"]


class AllergyReactionSerializer(serializers.ModelSerializer):
    reaction_name = serializers.CharField(source="reaction.name", read_only=True)

    class Meta:
        model = m.AllergyReaction
        fields = ["id", "reaction", "reaction_name", "reaction_non_coded"]


class AllergySerializer(serializers.ModelSerializer):
    allergen_name = serializers.CharField(source="allergen.name", read_only=True)
    reactions = AllergyReactionSerializer(many=True, read_only=True)

    class Meta:
        model = m.Allergy
        fields = ["id", "uuid", "patient", "allergen", "allergen_name", "category",
                  "severity", "reaction", "comment", "reactions", "voided"]
        read_only_fields = ["uuid", "voided"]


class ConditionSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source="concept.name", read_only=True)

    class Meta:
        model = m.Condition
        fields = ["id", "uuid", "patient", "concept", "concept_name", "clinical_status",
                  "onset_date", "end_date", "voided"]
        read_only_fields = ["uuid", "voided"]


class DiagnosisSerializer(serializers.ModelSerializer):
    diagnosis_concept_name = serializers.CharField(source="diagnosis_concept.name", read_only=True)

    class Meta:
        model = m.Diagnosis
        fields = ["id", "uuid", "patient", "encounter", "diagnosis_concept",
                  "diagnosis_concept_name", "certainty", "rank", "voided"]
        read_only_fields = ["uuid", "voided"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Order
        fields = ["id", "uuid", "order_number", "order_type", "concept", "patient",
                  "encounter", "orderer", "care_setting", "order_action", "urgency",
                  "instructions", "date_activated", "scheduled_date", "date_stopped",
                  "fulfiller_status", "fulfiller_comment", "voided"]
        read_only_fields = ["uuid", "order_number", "voided"]


class RelationshipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.RelationshipType
        fields = ["id", "uuid", "name", "a_is_to_b", "b_is_to_a", "weight", "retired"]
        read_only_fields = ["uuid", "retired"]


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Relationship
        fields = ["id", "uuid", "person_a", "person_b", "relationship_type",
                  "start_date", "end_date", "voided"]
        read_only_fields = ["uuid", "voided"]


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Drug
        fields = ["id", "uuid", "name", "concept", "combination", "dosage_form",
                  "strength", "dose_units", "maximum_daily_dose", "minimum_daily_dose",
                  "retired"]
        read_only_fields = ["uuid", "retired"]


class OrderFrequencySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.OrderFrequency
        fields = ["id", "uuid", "name", "concept", "frequency_per_day", "retired"]
        read_only_fields = ["uuid", "retired"]


class CohortSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = m.Cohort
        fields = ["id", "uuid", "name", "description", "member_count", "retired"]
        read_only_fields = ["uuid", "retired", "member_count"]

    def get_member_count(self, obj):
        return obj.memberships.filter(end_date__isnull=True).count()


class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Form
        fields = ["id", "uuid", "name", "version", "build", "published",
                  "encounter_type", "retired"]
        read_only_fields = ["uuid", "retired"]
