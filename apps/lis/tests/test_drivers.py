"""Tests for HL7/ASTM parsing and analyzer message ingestion."""
from django.test import TestCase
from django.utils import timezone

from apps.emr.models import (
    Concept,
    ConceptClass,
    ConceptDatatype,
    OrderType,
    Patient,
    Person,
)
from apps.lis.drivers.astm import ASTMDriver
from apps.lis.drivers.hl7 import HL7Driver
from apps.lis.ingest import ingest_message
from apps.lis.models import (
    AnalyzerMessage,
    LabResult,
    LabSection,
    LabTest,
    Specimen,
    SpecimenType,
    TestOrder,
)


class HL7ParseTests(TestCase):
    def test_parses_obx_results(self):
        msg = (
            "MSH|^~\\&|ANALYZER|LAB|LIS|LAB|20260101120000||ORU^R01|1|P|2.3\r"
            "PID|1||P12345||DOE^JANE\r"
            "OBR|1||ACC-20260101-00001|CBC\r"
            "OBX|1|NM|HB^Haemoglobin^L||6.0|g/dL|12-16|L|||F|||20260101120500\r"
        )
        parsed = HL7Driver().parse(msg)
        self.assertEqual(len(parsed.results), 1)
        result = parsed.results[0]
        self.assertEqual(result.test_code, "HB")
        self.assertEqual(result.numeric_value, 6.0)
        self.assertEqual(result.units, "g/dL")
        self.assertEqual(result.specimen_id, "ACC-20260101-00001")
        self.assertEqual(result.flag, "L")


class ASTMParseTests(TestCase):
    def test_parses_r_records(self):
        msg = (
            "H|\\^&|||ANALYZER\r"
            "P|1||P12345||DOE^JANE\r"
            "O|1|ACC-20260101-00001||^^^HB\r"
            "R|1|^^^HB^Haemoglobin|6.0|g/dL|12-16|L||||20260101120500\r"
            "L|1|N\r"
        )
        parsed = ASTMDriver().parse(msg)
        self.assertEqual(len(parsed.results), 1)
        result = parsed.results[0]
        self.assertEqual(result.test_code, "HB")
        self.assertEqual(result.numeric_value, 6.0)
        self.assertEqual(result.specimen_id, "ACC-20260101-00001")


class IngestionTests(TestCase):
    def setUp(self):
        klass = ConceptClass.objects.create(name="Test")
        numeric = ConceptDatatype.objects.create(name="Numeric")
        self.analyte = Concept.objects.create(
            name="Haemoglobin", concept_class=klass, datatype=numeric,
            low_normal=12, hi_normal=16, low_critical=7)
        section = LabSection.objects.create(name="Haematology")
        self.lab_test = LabTest.objects.create(
            name="Hb", test_code="HB", concept=self.analyte, section=section)
        blood = SpecimenType.objects.create(name="Blood")
        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)
        order_type = OrderType.objects.create(name="Test Order")
        self.order = TestOrder.objects.create(
            order_number="ORD-T-1", order_type=order_type, concept=self.analyte,
            patient=self.patient, lab_test=self.lab_test, date_activated=timezone.now())
        self.specimen = Specimen.objects.create(
            accession_number="ACC-20260101-00001", patient=self.patient,
            specimen_type=blood)
        self.specimen.orders.add(self.order)

    def test_hl7_ingestion_creates_entered_result_with_flag(self):
        msg = (
            "MSH|^~\\&|ANALYZER|LAB|LIS|LAB|20260101120000||ORU^R01|1|P|2.3\r"
            "PID|1||P12345||DOE^JANE\r"
            "OBR|1||ACC-20260101-00001|CBC\r"
            "OBX|1|NM|HB^Haemoglobin^L||6.0|g/dL|12-16|L|||F|||20260101120500\r"
        )
        message = ingest_message(msg, protocol="HL7")
        self.assertEqual(message.status, AnalyzerMessage.Status.PROCESSED)
        self.assertEqual(message.results_matched, 1)

        result = LabResult.objects.get(test_order=self.order, analyte=self.analyte)
        self.assertEqual(result.status, LabResult.Status.ENTERED)
        self.assertEqual(result.value_numeric, 6.0)
        # Value below critical low -> computed flag.
        self.assertEqual(result.flag, LabResult.Flag.CRITICAL_LOW)

    def test_unmatched_specimen_is_logged_not_dropped(self):
        msg = (
            "MSH|^~\\&|ANALYZER|LAB|LIS|LAB|20260101120000||ORU^R01|1|P|2.3\r"
            "OBR|1||ACC-DOES-NOT-EXIST|CBC\r"
            "OBX|1|NM|HB^Haemoglobin^L||6.0|g/dL|12-16|L|||F|||20260101120500\r"
        )
        message = ingest_message(msg, protocol="HL7")
        self.assertEqual(message.status, AnalyzerMessage.Status.FAILED)
        self.assertEqual(message.results_unmatched, 1)
        self.assertTrue(message.log)
