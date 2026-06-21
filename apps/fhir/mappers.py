"""Map Medraxis models to FHIR R4 resource dictionaries.

These are read-side projections: the Medraxis data model was deliberately
shaped to be FHIR-friendly (stable UUID ids, coded concepts, terminology
mappings), so each mapper is a thin, lossless-enough translation. Concept
``ConceptMapping`` rows surface as FHIR ``coding`` entries (LOINC/SNOMED/etc.).
"""
from __future__ import annotations

GENDER_MAP = {"M": "male", "F": "female", "O": "other", "U": "unknown"}

# Medraxis order fulfiller status -> FHIR request status (simplified).
ORDER_STATUS_MAP = {
    "": "active",
    "RECEIVED": "active",
    "IN_PROGRESS": "active",
    "ON_HOLD": "on-hold",
    "DECLINED": "revoked",
    "EXCEPTION": "active",
    "COMPLETED": "completed",
}


def _codeable_concept(concept):
    """Build a FHIR CodeableConcept from a Medraxis Concept, including mappings."""
    coding = []
    for mapping in concept.mappings.select_related("reference_term__source").all():
        coding.append({
            "system": mapping.reference_term.source.name,
            "code": mapping.reference_term.code,
            "display": concept.name,
        })
    cc = {"text": concept.name}
    if coding:
        cc["coding"] = coding
    return cc


def patient_to_fhir(patient):
    person = patient.person
    identifiers = [
        {"system": pi.identifier_type.name, "value": pi.identifier,
         "use": "official" if pi.preferred else "secondary"}
        for pi in patient.identifiers.select_related("identifier_type").all()
    ]
    names = [
        {"use": "official" if n.preferred else "usual",
         "family": n.family_name,
         "given": [g for g in [n.given_name, n.middle_name] if g],
         "prefix": [n.prefix] if n.prefix else []}
        for n in person.names.all()
    ]
    resource = {
        "resourceType": "Patient",
        "id": str(patient.uuid),
        "active": not patient.voided,
        "identifier": identifiers,
        "name": names,
        "gender": GENDER_MAP.get(person.gender, "unknown"),
    }
    if person.birthdate:
        resource["birthDate"] = person.birthdate.isoformat()
    if person.dead:
        resource["deceasedBoolean"] = True
    return resource


def encounter_to_fhir(encounter):
    resource = {
        "resourceType": "Encounter",
        "id": str(encounter.uuid),
        "status": "finished" if encounter.voided is False else "cancelled",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                  "code": "AMB", "display": "ambulatory"},
        "type": [{"text": encounter.encounter_type.name}],
        "subject": {"reference": f"Patient/{encounter.patient.uuid}"},
        "period": {"start": encounter.encounter_datetime.isoformat()},
    }
    if encounter.visit_id:
        resource["partOf"] = {"reference": f"Encounter/{encounter.visit.uuid}"}
    return resource


def obs_to_fhir(obs):
    resource = {
        "resourceType": "Observation",
        "id": str(obs.uuid),
        "status": (obs.status or "final").lower(),
        "code": _codeable_concept(obs.concept),
        "subject": {"reference": f"Patient/{obs.person.uuid}"},
        "effectiveDateTime": obs.obs_datetime.isoformat(),
    }
    if obs.encounter_id:
        resource["encounter"] = {"reference": f"Encounter/{obs.encounter.uuid}"}
    if obs.value_numeric is not None:
        resource["valueQuantity"] = {"value": obs.value_numeric,
                                     "unit": obs.concept.units or ""}
    elif obs.value_coded_id:
        resource["valueCodeableConcept"] = _codeable_concept(obs.value_coded)
    elif obs.value_boolean is not None:
        resource["valueBoolean"] = obs.value_boolean
    elif obs.value_datetime is not None:
        resource["valueDateTime"] = obs.value_datetime.isoformat()
    elif obs.value_text:
        resource["valueString"] = obs.value_text
    if obs.interpretation:
        resource["interpretation"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": obs.interpretation,
            }]
        }]
    return resource


def service_request_to_fhir(order):
    return {
        "resourceType": "ServiceRequest",
        "id": str(order.uuid),
        "status": ORDER_STATUS_MAP.get(order.fulfiller_status, "active"),
        "intent": "order",
        "priority": "stat" if order.urgency == "STAT" else "routine",
        "code": _codeable_concept(order.concept),
        "subject": {"reference": f"Patient/{order.patient.uuid}"},
        "authoredOn": order.date_activated.isoformat(),
        "requisition": {"value": order.order_number},
    }


def medication_request_to_fhir(drug_order):
    dosage = {"text": drug_order.dosing_instructions or
              " ".join(p for p in [str(drug_order.dose or ""), drug_order.dose_units,
                                   drug_order.frequency, drug_order.route] if p)}
    return {
        "resourceType": "MedicationRequest",
        "id": str(drug_order.uuid),
        "status": ORDER_STATUS_MAP.get(drug_order.fulfiller_status, "active"),
        "intent": "order",
        "medicationCodeableConcept": {"text": drug_order.drug.name},
        "subject": {"reference": f"Patient/{drug_order.patient.uuid}"},
        "authoredOn": drug_order.date_activated.isoformat(),
        "dosageInstruction": [dosage],
        "dispenseRequest": {"quantity": {"value": float(drug_order.quantity)}},
    }


def diagnostic_report_to_fhir(test_order):
    results = test_order.results.select_related("obs").all()
    return {
        "resourceType": "DiagnosticReport",
        "id": str(test_order.uuid),
        "status": "final" if test_order.fulfiller_status == "COMPLETED" else "partial",
        "code": _codeable_concept(test_order.concept),
        "subject": {"reference": f"Patient/{test_order.patient.uuid}"},
        "result": [
            {"reference": f"Observation/{r.obs.uuid}"}
            for r in results if r.obs_id
        ],
    }


def organization_to_fhir(org):
    return {
        "resourceType": "Organization",
        "id": str(org.id),
        "active": org.is_active,
        "name": org.name,
        "alias": [org.legal_name] if org.legal_name else [],
        "identifier": ([{"value": org.tax_identifier}] if org.tax_identifier else []),
    }


def bundle(resources, total=None, bundle_type="searchset"):
    """Wrap mapped resources in a FHIR Bundle."""
    entries = [{"resource": r} for r in resources]
    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "total": total if total is not None else len(entries),
        "entry": entries,
    }


def operation_outcome(severity, code, diagnostics):
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": severity, "code": code, "diagnostics": diagnostics}],
    }
