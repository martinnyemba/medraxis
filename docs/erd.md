# Medraxis — Entity Relationship Diagrams

Mermaid ER diagrams per domain. The abstract OpenMRS base classes
(`BaseOpenmrsData`, `BaseOpenmrsMetadata`) contribute `uuid`, audit and
soft-delete columns to every entity and are omitted from the diagrams for
readability.

> Legend: `||--o{` = one-to-many, `||--||` = one-to-one, `}o--o{` = many-to-many.

---

## 1. Concept dictionary (semantic core)

```mermaid
erDiagram
    ConceptClass    ||--o{ Concept : classifies
    ConceptDatatype ||--o{ Concept : "typed by"
    Concept ||--o{ ConceptName : "has names"
    Concept ||--o{ ConceptAnswer : "has answers"
    Concept ||--o{ ConceptSetMembership : "set members"
    Concept ||--o{ ConceptMapping : "mapped to"
    ConceptSource ||--o{ ConceptReferenceTerm : "defines codes"
    ConceptReferenceTerm ||--o{ ConceptMapping : "referenced by"

    Concept {
        uuid uuid
        string name
        string short_name
        bool is_set
        string units
        float hi_normal
        float low_normal
        float hi_critical
        float low_critical
    }
```

## 2. Person / Patient (demographics & identity)

```mermaid
erDiagram
    Person ||--o{ PersonName : "has"
    Person ||--o{ PersonAddress : "has"
    Person ||--o{ PersonAttribute : "has"
    PersonAttributeType ||--o{ PersonAttribute : "defines"
    Person ||--|| Patient : "is a"
    Patient ||--o{ PatientIdentifier : "identified by"
    PatientIdentifierType ||--o{ PatientIdentifier : "defines"
    Person ||--o{ Provider : "acts as"

    Patient {
        uuid uuid
        string allergy_status
    }
    PatientIdentifier {
        string identifier
        bool preferred
    }
```

## 3. Clinical activity (visit / encounter / obs / order)

```mermaid
erDiagram
    Patient ||--o{ Visit : "has"
    VisitType ||--o{ Visit : "typed by"
    Visit ||--o{ Encounter : "groups"
    Patient ||--o{ Encounter : "has"
    EncounterType ||--o{ Encounter : "typed by"
    Location ||--o{ Encounter : "at"
    Encounter ||--o{ EncounterProvider : "staffed by"
    Provider ||--o{ EncounterProvider : "participates"
    EncounterRole ||--o{ EncounterProvider : "as role"
    Encounter ||--o{ Obs : "records"
    Concept ||--o{ Obs : "question"
    Person ||--o{ Obs : "about"
    Patient ||--o{ Order : "for"
    OrderType ||--o{ Order : "typed by"
    Concept ||--o{ Order : "what"
    Provider ||--o{ Order : "ordered by"
    Order ||--o{ Obs : "fulfilled by"

    Obs {
        datetime obs_datetime
        float value_numeric
        string value_text
        string interpretation
        string status
    }
    Order {
        string order_number
        string order_action
        string urgency
        string fulfiller_status
    }
```

## 4. Programs (longitudinal care)

```mermaid
erDiagram
    Program ||--o{ ProgramWorkflow : "has"
    ProgramWorkflow ||--o{ ProgramWorkflowState : "has"
    Patient ||--o{ PatientProgram : "enrolled in"
    Program ||--o{ PatientProgram : "enrolment"
    PatientProgram ||--o{ PatientState : "moves through"
    ProgramWorkflowState ||--o{ PatientState : "state"
```

## 5. LIS / LIMS

```mermaid
erDiagram
    LabSection ||--o{ LabTest : "contains"
    SpecimenType ||--o{ LabTest : "sample"
    Concept ||--o{ LabTest : "defined by"
    Order ||--|| TestOrder : "is a"
    LabTest ||--o{ TestOrder : "ordered as"
    Patient ||--o{ Specimen : "from"
    SpecimenType ||--o{ Specimen : "of type"
    Specimen }o--o{ TestOrder : "covers"
    TestOrder ||--o{ LabResult : "produces"
    Specimen ||--o{ LabResult : "tested"
    Concept ||--o{ LabResult : "analyte"
    LabResult ||--|| Obs : "released as"
    LabSection ||--o{ Analyzer : "has"
    Analyzer ||--o{ LabResult : "measured by"
    LabSection ||--o{ Worklist : "batches"

    LabResult {
        float value_numeric
        string flag
        string status
        datetime verified_at
    }
    Specimen {
        string accession_number
        string status
    }
```

## 6. Inventory & stock

```mermaid
erDiagram
    ProductCategory ||--o{ Product : "categorises"
    UnitOfMeasure ||--o{ Product : "measured in"
    TaxRate ||--o{ Product : "taxed at"
    Concept ||--o{ Product : "drug concept"
    Product ||--o{ StockBatch : "stocked as"
    Location ||--o{ StockBatch : "at"
    Product ||--o{ StockTransaction : "moves"
    StockBatch ||--o{ StockTransaction : "ledger"
    Location ||--o{ StockTransaction : "at"
    Supplier ||--o{ PurchaseOrder : "supplies"
    PurchaseOrder ||--o{ PurchaseOrderItem : "lines"
    Product ||--o{ PurchaseOrderItem : "ordered"

    StockBatch {
        string batch_number
        date expiry_date
        decimal quantity_on_hand
    }
    StockTransaction {
        string transaction_type
        decimal quantity
        decimal unit_cost
    }
```

## 7. Pharmacy

```mermaid
erDiagram
    Order ||--|| DrugOrder : "is a"
    Product ||--o{ DrugOrder : "prescribes"
    DrugOrder ||--o{ Dispense : "dispensed by"
    Patient ||--o{ Dispense : "to"
    Product ||--o{ Dispense : "of"
    Location ||--o{ Dispense : "at"
    Provider ||--o{ Dispense : "by"

    DrugOrder {
        decimal dose
        string frequency
        string route
        decimal quantity
    }
```

## 8. POS & billing

```mermaid
erDiagram
    Customer ||--o{ Sale : "buys"
    Patient ||--o{ Sale : "billed"
    Location ||--o{ Sale : "at"
    Sale ||--o{ SaleLine : "lines"
    Sale ||--o{ Payment : "settled by"
    Product ||--o{ SaleLine : "product line"
    LabTest ||--o{ SaleLine : "test line"
    BillableService }o--o{ Sale : "service line"
    InsuranceScheme ||--o{ PatientInsurance : "covers"
    Patient ||--o{ PatientInsurance : "holds"

    Sale {
        string invoice_number
        string status
        decimal grand_total
        decimal amount_paid
    }
    SaleLine {
        string line_type
        decimal quantity
        decimal unit_price
        decimal tax_percent
    }
```

---

## Normalization note

The schema is designed to **3NF**. Deliberate denormalisations, each with a
clear maintenance strategy:

- `Sale.subtotal/tax_total/grand_total/amount_paid` — derived totals cached on
  the invoice header for fast listing/reporting; recomputed from lines via
  `Sale.recalculate()` and on every payment.
- `StockBatch.quantity_on_hand` — running balance maintained transactionally
  alongside the append-only `StockTransaction` ledger (the ledger is the source
  of truth and can fully reconstruct the balance).
- `Patient.allergy_status` — convenience flag for the chart banner.
