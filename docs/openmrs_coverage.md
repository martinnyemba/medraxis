# OpenMRS Data Model — Coverage Map

How the Medraxis Django models map onto the OpenMRS Java domain model
(`org.openmrs.*`). This documents what is implemented, what was deliberately
replaced with a modern equivalent, and what remains out of scope.

Legend: ✅ implemented · ➕ implemented with an extension · 🔁 replaced by a
modern equivalent · ⬜ not implemented (out of scope this iteration).

## Person & relationships
| OpenMRS | Medraxis | Status |
|---|---|---|
| Person | `emr.Person` | ✅ |
| PersonName | `emr.PersonName` | ✅ |
| PersonAddress | `emr.PersonAddress` | ✅ |
| PersonAttribute / PersonAttributeType | `emr.PersonAttribute(Type)` | ✅ |
| Relationship / RelationshipType | `emr.Relationship(Type)` | ✅ |
| Patient | `emr.Patient` | ✅ |
| PatientIdentifier / Type | `emr.PatientIdentifier(Type)` | ✅ |
| Allergy | `emr.Allergy` | ✅ |
| AllergyReaction | `emr.AllergyReaction` | ✅ |
| Condition | `emr.Condition` | ✅ |
| Diagnosis | `emr.Diagnosis` | ✅ |
| PersonMergeLog | — | ⬜ |

## Concept dictionary
| OpenMRS | Medraxis | Status |
|---|---|---|
| Concept (+ ConceptNumeric) | `emr.Concept` (numeric fields folded in) | ➕ |
| ConceptName | `emr.ConceptName` | ✅ |
| ConceptDescription | `emr.ConceptDescription` | ✅ |
| ConceptClass | `emr.ConceptClass` | ✅ |
| ConceptDatatype | `emr.ConceptDatatype` | ✅ |
| ConceptAnswer | `emr.ConceptAnswer` | ✅ |
| ConceptSet | `emr.ConceptSetMembership` | ✅ |
| ConceptSource | `emr.ConceptSource` | ✅ |
| ConceptReferenceTerm | `emr.ConceptReferenceTerm` | ✅ |
| ConceptMap (concept↔term) | `emr.ConceptMapping` | ✅ |
| ConceptMapType | `emr.ConceptMapType` | ✅ |
| ConceptReferenceTermMap (term↔term) | `emr.ConceptReferenceTermMap` | ✅ |
| ConceptProposal | `emr.ConceptProposal` | ✅ |
| ConceptAttribute / Type | `emr.ConceptAttribute(Type)` | ✅ |
| Drug | `emr.Drug` | ✅ |
| DrugIngredient | `emr.DrugIngredient` | ✅ |
| ConceptStopWord / ConceptNameTag / DrugReferenceMap | — | ⬜ |

## Encounters, visits & observations
| OpenMRS | Medraxis | Status |
|---|---|---|
| Encounter | `emr.Encounter` | ✅ |
| EncounterType | `emr.EncounterType` | ✅ |
| EncounterRole | `emr.EncounterRole` | ✅ |
| EncounterProvider | `emr.EncounterProvider` | ✅ |
| Visit | `emr.Visit` | ✅ |
| VisitType | `emr.VisitType` | ✅ |
| VisitAttribute / Type | `emr.VisitAttribute(Type)` | ✅ |
| Obs | `emr.Obs` | ✅ |

## Orders
| OpenMRS | Medraxis | Status |
|---|---|---|
| Order | `emr.Order` | ✅ |
| OrderType | `emr.OrderType` | ✅ |
| CareSetting | `emr.CareSetting` | ✅ |
| TestOrder | `lis.TestOrder` (MTI) | ✅ |
| DrugOrder | `pharmacy.DrugOrder` (MTI, links `Drug` + `OrderFrequency`) | ➕ |
| OrderFrequency | `emr.OrderFrequency` | ✅ |
| OrderGroup | `emr.OrderGroup` | ✅ |
| OrderSet / OrderSetMember | `emr.OrderSet` / `emr.OrderSetMember` | ✅ |
| OrderAttribute / Type | — | ⬜ |

## Forms
| OpenMRS | Medraxis | Status |
|---|---|---|
| Form | `emr.Form` | ✅ |
| FormField | `emr.FormField` | ✅ |
| Field | `emr.Field` | ✅ |
| FieldType | `emr.FieldType` | ✅ |
| FormResource | `emr.FormResource` | ✅ |
| FieldAnswer | — | ⬜ |

## Programs & cohorts
| OpenMRS | Medraxis | Status |
|---|---|---|
| Program | `emr.Program` | ✅ |
| ProgramWorkflow | `emr.ProgramWorkflow` | ✅ |
| ProgramWorkflowState | `emr.ProgramWorkflowState` | ✅ |
| PatientProgram | `emr.PatientProgram` | ✅ |
| PatientState | `emr.PatientState` | ✅ |
| ConceptStateConversion | `emr.ConceptStateConversion` | ✅ |
| ProgramAttributeType / PatientProgramAttribute | `emr.ProgramAttributeType` / `emr.PatientProgramAttribute` | ✅ |
| Cohort | `emr.Cohort` | ✅ |
| CohortMembership | `emr.CohortMembership` | ✅ |

## Users, providers & security
| OpenMRS | Medraxis | Status |
|---|---|---|
| User | `users.User` | ✅ |
| Role | `users.Role` | ✅ |
| Privilege | `users.Privilege` | ✅ |
| Provider | `users.Provider` | ✅ |
| ProviderAttribute / Type | `users.ProviderAttribute(Type)` | ✅ |
| LoginCredential / UserProperty | Django auth internals | 🔁 |

## Location
| OpenMRS | Medraxis | Status |
|---|---|---|
| Location | `emr.Location` | ✅ |
| LocationTag | `emr.LocationTag` | ✅ |
| LocationAttribute / Type | `emr.LocationAttribute(Type)` | ✅ |

## Infrastructure (deliberately replaced or out of scope)
| OpenMRS | Medraxis | Status |
|---|---|---|
| GlobalProperty | `core.GlobalProperty` | ✅ |
| BaseOpenmrsObject / Data / Metadata | `core` abstract bases | ✅ |
| HL7 inbound queue (HL7InQueue/Error/Archive) | `lis.AnalyzerMessage` + HL7/ASTM drivers | 🔁 |
| Alert / AlertRecipient | `notifications.Notification` | 🔁 |
| SchedulerTask (TaskDefinition) | Celery tasks/beat | 🔁 |
| SerializedObject / CustomDatatype storage | Django ORM + migrations | 🔁 |
| Reporting / Cohort builder module | `notifications.ReportRun` | 🔁 |
| FHIR module | `apps.fhir` facade | 🔁 |
| Multi-facility (Location-based) | `apps.tenancy` row-level tenancy | ➕ |
| ConceptProposalTag, HtmlFormEntry schema, OrderAttribute | — | ⬜ |

## Notes on faithful-but-pragmatic choices
- **ConceptNumeric** is folded into `Concept` (numeric range fields) rather than
  a separate table; behaviour is equivalent and simpler in Django.
- **Drug vs Product:** OpenMRS `Drug` is the clinical formulation;
  `inventory.Product` is the stockable item. `DrugOrder.drug_formulation` → `Drug`
  and `Product.drug` → `Drug` keep the clinical and commercial sides linked while
  allowing one formulation to map to several suppliers' products.
- **The customizable Attribute framework** (`core.attributes.BaseAttributeType` /
  `BaseAttribute`) is OpenMRS's key extensibility pattern and is now implemented
  for Person, Visit, Location, Concept, Provider and Program enrolment.
