"""Idempotent seed command for reference data and a small demo dataset.

Run with::

    python manage.py seed            # reference metadata + RBAC
    python manage.py seed --demo     # also create demo patient/orders/sale

Safe to run repeatedly: everything uses get_or_create. No unsafe default
passwords are created for real accounts; the optional demo admin password must
be supplied via the DJANGO_SEED_ADMIN_PASSWORD environment variable.
"""
import os
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.billing.models import BillableService
from apps.emr import models as emr
from apps.inventory import models as inv
from apps.lis import models as lis
from apps.notifications.models import NotificationTemplate
from apps.tenancy.context import organization_context
from apps.tenancy.models import Membership, Organization
from apps.users.models import Privilege, Provider, Role, User

PRIVILEGES = [
    "View Patients", "Add Patients", "Edit Patients",
    "View Concepts", "Manage Concepts",
    "View Observations", "Add Observations",
    "Manage Lab Results", "Manage Inventory", "Run POS",
]

ROLES = {
    "Clinician": ["View Patients", "Add Patients", "Edit Patients", "View Concepts",
                  "View Observations", "Add Observations"],
    "Lab Technologist": ["View Patients", "View Concepts", "Manage Lab Results"],
    "Pharmacist": ["View Patients", "Manage Inventory", "Run POS"],
    "Cashier": ["Run POS"],
    "System Administrator": PRIVILEGES,
}


class Command(BaseCommand):
    help = "Seed reference data, RBAC and (optionally) a demo dataset."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create demo records.")

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding privileges & roles...")
        self._seed_rbac()
        self.stdout.write("Seeding organization (tenant)...")
        organization = self._seed_tenancy()
        self.stdout.write("Seeding notification templates...")
        self._seed_templates()
        self.stdout.write("Seeding clinical metadata...")
        concepts = self._seed_concepts()
        self.stdout.write("Seeding locations & encounter types...")
        self._seed_metadata()
        self.stdout.write("Seeding lab catalogue...")
        self._seed_lab(concepts)
        self.stdout.write("Seeding inventory & billing...")
        self._seed_inventory_billing(concepts)
        if options["demo"]:
            self.stdout.write("Seeding demo dataset...")
            # Demo data is owned by the demo organization (tenant).
            with organization_context(organization):
                self._seed_demo(concepts)
        self.stdout.write(self.style.SUCCESS("Seeding complete."))

    # -------------------------------------------------------------- tenancy
    def _seed_tenancy(self):
        organization, _ = Organization.objects.get_or_create(
            slug="demo-clinic",
            defaults={"name": "Demo Clinic", "org_type": Organization.OrgType.CLINIC},
        )
        admin = User.objects.filter(username="admin").first()
        if admin is not None:
            Membership.objects.get_or_create(
                user=admin, organization=organization,
                defaults={"is_default": True, "is_admin": True},
            )
        return organization

    def _seed_templates(self):
        NotificationTemplate.objects.get_or_create(
            code="critical-result",
            defaults={
                "description": "Critical lab result alert",
                "subject_template": "Critical result for {{ patient }}",
                "body_template": "{{ analyte }} = {{ value }} ({{ flag }}) for order {{ order }}.",
                "default_channel": "in_app",
            },
        )

    # ------------------------------------------------------------------ RBAC
    def _seed_rbac(self):
        priv_objs = {p: Privilege.objects.get_or_create(name=p)[0] for p in PRIVILEGES}
        for role_name, privs in ROLES.items():
            role, _ = Role.objects.get_or_create(name=role_name)
            role.privileges.set([priv_objs[p] for p in privs])

        admin_password = os.environ.get("DJANGO_SEED_ADMIN_PASSWORD")
        if admin_password:
            admin, created = User.objects.get_or_create(
                username="admin",
                defaults={"email": "admin@medraxis.local", "is_staff": True, "is_superuser": True},
            )
            if created:
                admin.set_password(admin_password)
                admin.save()
                admin.roles.add(Role.objects.get(name="System Administrator"))
                self.stdout.write("  created superuser 'admin'")

    # -------------------------------------------------------------- concepts
    def _seed_concepts(self):
        cls = {n: emr.ConceptClass.objects.get_or_create(name=n)[0]
               for n in ["Test", "Finding", "Diagnosis", "Drug", "Question", "Procedure"]}
        dt = {n: emr.ConceptDatatype.objects.get_or_create(name=n)[0]
              for n in ["Numeric", "Coded", "Text", "Boolean", "Datetime"]}

        def concept(name, klass, datatype, **extra):
            obj, _ = emr.Concept.objects.get_or_create(
                name=name, defaults={"concept_class": cls[klass], "datatype": dt[datatype], **extra}
            )
            return obj

        return {
            "weight": concept("Weight (kg)", "Finding", "Numeric", units="kg",
                              low_normal=2, hi_normal=200),
            "height": concept("Height (cm)", "Finding", "Numeric", units="cm"),
            "temp": concept("Temperature (C)", "Finding", "Numeric", units="C",
                           low_normal=36.0, hi_normal=37.5, hi_critical=40),
            "hb": concept("Haemoglobin", "Test", "Numeric", units="g/dL",
                         low_normal=12, hi_normal=16, low_critical=7),
            "glucose": concept("Fasting Blood Glucose", "Test", "Numeric", units="mmol/L",
                              low_normal=3.9, hi_normal=5.5, hi_critical=15),
            "malaria": concept("Malaria Diagnosis", "Diagnosis", "Coded"),
            "amox": concept("Amoxicillin 500mg", "Drug", "Text"),
            "consult": concept("General Consultation", "Procedure", "Text"),
        }

    # -------------------------------------------------------------- metadata
    def _seed_metadata(self):
        facility, _ = emr.Location.objects.get_or_create(name="Main Facility")
        for n in ["OPD", "Laboratory", "Pharmacy", "Main Store"]:
            emr.Location.objects.get_or_create(name=n, defaults={"parent": facility})
        for n in ["Consultation", "Triage", "Lab", "Dispensing"]:
            emr.EncounterType.objects.get_or_create(name=n)
        for n in ["Outpatient", "Lab Walk-in", "Pharmacy Sale"]:
            emr.VisitType.objects.get_or_create(name=n)
        emr.EncounterRole.objects.get_or_create(name="Consulting Clinician")
        emr.OrderType.objects.get_or_create(name="Test Order")
        emr.OrderType.objects.get_or_create(name="Drug Order")
        emr.CareSetting.objects.get_or_create(name="Outpatient")
        emr.PatientIdentifierType.objects.get_or_create(
            name="Medraxis ID", defaults={"required": True}
        )

    # ------------------------------------------------------------------- lab
    def _seed_lab(self, concepts):
        haem, _ = lis.LabSection.objects.get_or_create(name="Haematology")
        chem, _ = lis.LabSection.objects.get_or_create(name="Chemistry")
        blood, _ = lis.SpecimenType.objects.get_or_create(name="Blood")
        lis.LabTest.objects.get_or_create(
            test_code="HB", defaults={
                "name": "Haemoglobin", "concept": concepts["hb"], "section": haem,
                "specimen_type": blood, "price": Decimal("50.00"), "loinc_code": "718-7"},
        )
        lis.LabTest.objects.get_or_create(
            test_code="FBG", defaults={
                "name": "Fasting Blood Glucose", "concept": concepts["glucose"],
                "section": chem, "specimen_type": blood, "price": Decimal("80.00")},
        )
        self._seed_flabs(concepts, haem)

    # ---------------------------------------------------- FLabs extensions
    def _seed_flabs(self, concepts, haem_section):
        hb_test = lis.LabTest.objects.get(test_code="HB")
        # Demographic (sex-specific) reference ranges for haemoglobin.
        lis.ReferenceRange.objects.get_or_create(
            lab_test=hb_test, analyte=concepts["hb"], sex="M",
            defaults={"low_normal": 13, "hi_normal": 17, "low_critical": 7,
                      "units": "g/dL", "text_range": "13 - 17 g/dL (M)"},
        )
        lis.ReferenceRange.objects.get_or_create(
            lab_test=hb_test, analyte=concepts["hb"], sex="F",
            defaults={"low_normal": 12, "hi_normal": 15, "low_critical": 7,
                      "units": "g/dL", "text_range": "12 - 15 g/dL (F)"},
        )
        # An auto-verification rule for haemoglobin.
        lis.AutoVerificationRule.objects.get_or_create(
            name="Hb auto-verify", lab_test=hb_test,
            defaults={"require_in_range": True, "block_on_critical": True,
                      "delta_check_percent": 25},
        )
        # A referring doctor and a B2B client.
        lis.ReferringDoctor.objects.get_or_create(
            code="DR001", defaults={"name": "Dr. Mwansa", "specialty": "General"})
        lis.Client.objects.get_or_create(
            code="HOSP01", defaults={"name": "City Hospital",
                                     "client_type": lis.Client.ClientType.HOSPITAL})
        # Microbiology reference data.
        for org in ["Escherichia coli", "Staphylococcus aureus", "Klebsiella pneumoniae"]:
            lis.Organism.objects.get_or_create(name=org)
        for ab, abbr in [("Amoxicillin", "AMX"), ("Ciprofloxacin", "CIP"),
                         ("Ceftriaxone", "CRO")]:
            lis.Antibiotic.objects.get_or_create(
                name=ab, defaults={"abbreviation": abbr})

    # ----------------------------------------------------- inventory/billing
    def _seed_inventory_billing(self, concepts):
        meds, _ = inv.ProductCategory.objects.get_or_create(name="Medicines")
        tab, _ = inv.UnitOfMeasure.objects.get_or_create(
            name="Tablet", defaults={"abbreviation": "tab"})
        gst, _ = inv.TaxRate.objects.get_or_create(
            name="GST 5%", defaults={"rate_percent": Decimal("5.00"), "hsn_sac_code": "3004"})
        inv.Product.objects.get_or_create(
            sku="MED-AMOX-500", defaults={
                "name": "Amoxicillin 500mg", "category": meds, "unit": tab, "tax_rate": gst,
                "is_drug": True, "drug_concept": concepts["amox"], "strength": "500mg",
                "sale_price": Decimal("2.50"), "cost_price": Decimal("1.20"),
                "reorder_level": Decimal("100")},
        )
        BillableService.objects.get_or_create(
            service_code="CONSULT-GEN", defaults={
                "name": "General Consultation", "concept": concepts["consult"],
                "price": Decimal("100.00"), "tax_rate": gst},
        )

    # ------------------------------------------------------------------ demo
    def _seed_demo(self, concepts):
        from apps.emr.services import generate_patient_identifier

        person, _ = emr.Person.objects.get_or_create(
            gender="F", defaults={"birthdate": date(1990, 5, 14)})
        if not person.names.exists():
            emr.PersonName.objects.create(
                person=person, given_name="Jane", family_name="Banda", preferred=True)
        patient, created = emr.Patient.objects.get_or_create(person=person)
        if created:
            id_type = emr.PatientIdentifierType.objects.get(name="Medraxis ID")
            emr.PatientIdentifier.objects.create(
                patient=patient, identifier_type=id_type,
                identifier=generate_patient_identifier(), preferred=True)

        location = emr.Location.objects.get(name="OPD")
        enc_type = emr.EncounterType.objects.get(name="Consultation")
        encounter, _ = emr.Encounter.objects.get_or_create(
            patient=patient, encounter_type=enc_type, location=location,
            defaults={"encounter_datetime": timezone.now()})
        emr.Obs.objects.get_or_create(
            person=person, concept=concepts["weight"], encounter=encounter,
            defaults={"obs_datetime": timezone.now(), "value_numeric": 62.0})

        # Receive some pharmacy stock so dispensing/POS demos work.
        from apps.inventory.services import receive_stock
        product = inv.Product.objects.get(sku="MED-AMOX-500")
        store = emr.Location.objects.get(name="Pharmacy")
        if not product.batches.exists():
            receive_stock(product=product, location=store, quantity=500,
                          unit_cost=Decimal("1.20"), batch_number="B-DEMO-001",
                          expiry_date=date.today() + timedelta(days=365))
        self.stdout.write("  demo patient, encounter, observation and stock created")
