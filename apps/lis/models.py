"""Laboratory Information System (LIS/LIMS).

Design philosophy: the lab does not reinvent ordering. A laboratory request is
an EMR :class:`~apps.emr.models.Order` specialised as :class:`TestOrder`
(multi-table inheritance), so lab work shares the patient, encounter,
order number and fulfilment lifecycle with the rest of the platform. On top of
that, the LIS adds the things a lab specifically needs: a test catalogue,
specimen/accession tracking, and a result entry -> technical verification ->
release workflow with instrument (analyzer) integration.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata, TimeStampedModel
from apps.emr.models import Order
from apps.tenancy.mixins import TenantScopedModel


class LabSection(BaseOpenmrsMetadata):
    """A bench/department: Haematology, Chemistry, Microbiology, Serology, ..."""

    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="lab_sections"
    )


class SpecimenType(BaseOpenmrsMetadata):
    """Blood, Serum, Plasma, Urine, Stool, CSF, Swab, Tissue, ..."""

    default_container = models.CharField(max_length=120, blank=True, default="")


class LabTest(BaseOpenmrsMetadata):
    """Orderable test or panel in the catalogue.

    Wraps an EMR ``Concept`` (the semantic definition) with the operational
    attributes a lab and a business need: section, specimen, turnaround time,
    price and whether it is a panel of analytes.
    """

    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="lab_tests"
    )
    test_code = models.CharField(max_length=64, unique=True, db_index=True)
    section = models.ForeignKey(
        LabSection, on_delete=models.PROTECT, related_name="tests"
    )
    specimen_type = models.ForeignKey(
        SpecimenType, on_delete=models.PROTECT, related_name="tests", null=True, blank=True
    )
    is_panel = models.BooleanField(default=False)
    analytes = models.ManyToManyField(
        "emr.Concept", related_name="panel_tests", blank=True,
        help_text="Component analyte concepts when this is a panel.",
    )
    turnaround_hours = models.PositiveIntegerField(default=24)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loinc_code = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return f"{self.test_code} - {self.name}"


class TestOrder(Order):
    """A laboratory request -- an EMR Order with lab-specific attributes."""

    lab_test = models.ForeignKey(
        LabTest, on_delete=models.PROTECT, related_name="test_orders"
    )
    specimen_source = models.ForeignKey(
        SpecimenType, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    laterality = models.CharField(max_length=20, blank=True, default="")
    clinical_history = models.TextField(blank=True, default="")

    # FLabs-inspired commercial/operational context.
    referring_doctor = models.ForeignKey(
        "lis.ReferringDoctor", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="test_orders",
    )
    client = models.ForeignKey(
        "lis.Client", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="test_orders",
    )
    collection_center = models.ForeignKey(
        "lis.CollectionCenter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="test_orders",
    )
    test_method = models.ForeignKey(
        "lis.TestMethod", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="test_orders",
    )
    # Outsourcing to an external reference lab.
    reference_lab = models.ForeignKey(
        "lis.ReferenceLab", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="test_orders",
    )
    is_outsourced = models.BooleanField(default=False)

    class Meta:
        verbose_name = "test order"


class Specimen(BaseOpenmrsData, TenantScopedModel):
    """A physical sample tracked by accession number through the lab."""

    class Status(models.TextChoices):
        ORDERED = "ORDERED", "Ordered"
        COLLECTED = "COLLECTED", "Collected"
        RECEIVED = "RECEIVED", "Received in lab"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        REJECTED = "REJECTED", "Rejected"
        DISPOSED = "DISPOSED", "Disposed"

    accession_number = models.CharField(max_length=64, unique=True, db_index=True)
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.PROTECT, related_name="specimens"
    )
    specimen_type = models.ForeignKey(
        SpecimenType, on_delete=models.PROTECT, related_name="specimens"
    )
    orders = models.ManyToManyField(
        TestOrder, related_name="specimens", blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDERED)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        "users.Provider", on_delete=models.SET_NULL, null=True, blank=True, related_name="collected_specimens"
    )
    received_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["patient"])]

    def __str__(self):
        return self.accession_number


class LabResult(BaseOpenmrsData):
    """A result value for one analyte of a test order, with a release workflow.

    The clinically-authoritative record is mirrored into an EMR ``Obs`` on
    release, so results appear seamlessly on the patient chart while the LIS
    keeps the richer verification metadata here.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ENTERED = "ENTERED", "Entered"
        VERIFIED = "VERIFIED", "Verified"
        RELEASED = "RELEASED", "Released"
        REJECTED = "REJECTED", "Rejected"

    class Flag(models.TextChoices):
        NORMAL = "N", "Normal"
        HIGH = "H", "High"
        LOW = "L", "Low"
        CRITICAL_HIGH = "HH", "Critical high"
        CRITICAL_LOW = "LL", "Critical low"
        ABNORMAL = "A", "Abnormal"

    test_order = models.ForeignKey(
        TestOrder, on_delete=models.CASCADE, related_name="results"
    )
    specimen = models.ForeignKey(
        Specimen, on_delete=models.SET_NULL, null=True, blank=True, related_name="results"
    )
    analyte = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="lab_results"
    )
    value_numeric = models.FloatField(null=True, blank=True)
    value_text = models.TextField(blank=True, default="")
    value_coded = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    units = models.CharField(max_length=50, blank=True, default="")
    reference_range = models.CharField(max_length=120, blank=True, default="")
    flag = models.CharField(max_length=2, choices=Flag.choices, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    entered_by = models.ForeignKey(
        "users.Provider", on_delete=models.SET_NULL, null=True, blank=True, related_name="entered_results"
    )
    entered_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "users.Provider", on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_results"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    analyzer = models.ForeignKey(
        "lis.Analyzer", on_delete=models.SET_NULL, null=True, blank=True, related_name="results"
    )
    obs = models.OneToOneField(
        "emr.Obs", on_delete=models.SET_NULL, null=True, blank=True, related_name="lab_result"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["test_order", "analyte"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.analyte} = {self.value_numeric or self.value_text} ({self.status})"


class Analyzer(BaseOpenmrsMetadata):
    """A laboratory instrument that feeds results into the LIS (HL7/ASTM)."""

    section = models.ForeignKey(
        LabSection, on_delete=models.PROTECT, related_name="analyzers"
    )
    manufacturer = models.CharField(max_length=120, blank=True, default="")
    model_number = models.CharField(max_length=120, blank=True, default="")
    protocol = models.CharField(
        max_length=20, default="HL7", help_text="HL7, ASTM, manual, ..."
    )
    is_bidirectional = models.BooleanField(default=False)


class Worklist(TimeStampedModel):
    """A batch of test orders grouped for a section/analyzer run."""

    name = models.CharField(max_length=120)
    section = models.ForeignKey(
        LabSection, on_delete=models.PROTECT, related_name="worklists"
    )
    analyzer = models.ForeignKey(
        Analyzer, on_delete=models.SET_NULL, null=True, blank=True, related_name="worklists"
    )
    test_orders = models.ManyToManyField(TestOrder, related_name="worklists", blank=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class AnalyzerMessage(TimeStampedModel):
    """An inbound raw message received from an analyzer, with its parse outcome.

    Persisting the raw payload gives an auditable, replayable record of every
    instrument transmission -- important when a result is queried clinically.
    """

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        PROCESSED = "PROCESSED", "Processed"
        PARTIAL = "PARTIAL", "Partially processed"
        FAILED = "FAILED", "Failed"

    analyzer = models.ForeignKey(
        Analyzer, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages"
    )
    protocol = models.CharField(max_length=20, default="HL7")
    raw_payload = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    results_matched = models.PositiveIntegerField(default=0)
    results_unmatched = models.PositiveIntegerField(default=0)
    log = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.protocol} message [{self.status}] ({self.results_matched} matched)"


# ---------------------------------------------------------------------------
# FLabs-inspired extensions. Defined in focused submodules and imported here so
# Django registers them under the ``lis`` app. (Models use string FK refs to
# avoid import cycles.)
# ---------------------------------------------------------------------------
from apps.lis.automation import AutoVerificationRule  # noqa: E402,F401
from apps.lis.catalog import (  # noqa: E402,F401
    ReferenceRange,
    ReportTemplate,
    TestMethod,
    TestProfile,
    TestProfileMember,
)
from apps.lis.clients import (  # noqa: E402,F401
    Client,
    CollectionAppointment,
    CollectionCenter,
    PriceList,
    PriceListItem,
    ReferenceLab,
    ReferringDoctor,
)
from apps.lis.delivery import ReportDelivery  # noqa: E402,F401
from apps.lis.microbiology import (  # noqa: E402,F401
    Antibiotic,
    MicrobiologyResult,
    Organism,
    SensitivityResult,
)
from apps.lis.qc import QCMaterial, QCResult  # noqa: E402,F401
