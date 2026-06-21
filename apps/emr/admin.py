from django.contrib import admin

from apps.emr import models as m


class PersonNameInline(admin.TabularInline):
    model = m.PersonName
    extra = 1


class PatientIdentifierInline(admin.TabularInline):
    model = m.PatientIdentifier
    extra = 1


@admin.register(m.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("uuid", "gender", "birthdate", "dead")
    list_filter = ("gender", "dead")
    inlines = [PersonNameInline]
    search_fields = ("uuid", "names__given_name", "names__family_name")


@admin.register(m.Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("__str__", "uuid", "allergy_status", "voided")
    inlines = [PatientIdentifierInline]
    search_fields = ("uuid", "identifiers__identifier", "person__names__family_name")


@admin.register(m.Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ("name", "concept_class", "datatype", "is_set", "retired")
    list_filter = ("concept_class", "datatype", "is_set", "retired")
    search_fields = ("name", "short_name")


@admin.register(m.Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("__str__", "encounter_type", "location", "encounter_datetime")
    list_filter = ("encounter_type", "location")
    date_hierarchy = "encounter_datetime"


@admin.register(m.Obs)
class ObsAdmin(admin.ModelAdmin):
    list_display = ("concept", "person", "display_value", "obs_datetime", "interpretation")
    list_filter = ("interpretation", "status")
    date_hierarchy = "obs_datetime"


@admin.register(m.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "order_type", "concept", "patient", "fulfiller_status")
    list_filter = ("order_type", "fulfiller_status", "urgency")
    search_fields = ("order_number",)


for model in (
    m.ConceptClass,
    m.ConceptDatatype,
    m.Location,
    m.LocationTag,
    m.VisitType,
    m.Visit,
    m.EncounterType,
    m.EncounterRole,
    m.OrderType,
    m.CareSetting,
    m.PatientIdentifierType,
    m.PersonAttributeType,
    m.Program,
    m.Allergy,
    m.Condition,
    m.Diagnosis,
    m.ConceptSource,
    m.ConceptReferenceTerm,
):
    admin.site.register(model)
