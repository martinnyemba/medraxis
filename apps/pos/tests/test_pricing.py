"""Tests for unified price resolution and B2B client billing."""
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APITestCase

from apps.billing.models import BillableService
from apps.emr.models import Concept, ConceptClass, ConceptDatatype, Location
from apps.inventory.models import Product, ProductCategory, TaxRate, UnitOfMeasure
from apps.lis.models import (
    Client,
    LabSection,
    LabTest,
    PriceList,
    PriceListItem,
    TestProfile,
)
from apps.pos.models import Sale, SaleLine
from apps.pos.pricing import price_line, resolve_unit_price
from apps.pos.services import next_invoice_number, reprice_sale
from apps.users.models import User


def _lab_test(price, code="T1"):
    klass = ConceptClass.objects.create(name=f"C{code}")
    dt = ConceptDatatype.objects.create(name=f"N{code}")
    concept = Concept.objects.create(name=f"Analyte{code}", concept_class=klass, datatype=dt)
    section = LabSection.objects.create(name=f"Sec{code}")
    return LabTest.objects.create(
        name=f"Test {code}", test_code=code, concept=concept, section=section,
        price=Decimal(price))


class PriceResolutionTests(TestCase):
    def test_product_uses_sale_price(self):
        cat = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tab")
        product = Product.objects.create(
            name="Amox", sku="AMOX", category=cat, unit=unit, sale_price=Decimal("2.50"))
        price = resolve_unit_price(line_type=SaleLine.LineType.PRODUCT, product=product)
        self.assertEqual(price, Decimal("2.50"))

    def test_lab_test_falls_back_to_list_price(self):
        test = _lab_test("80.00", "FBG")
        price = resolve_unit_price(line_type=SaleLine.LineType.LAB_TEST, lab_test=test)
        self.assertEqual(price, Decimal("80.00"))

    def test_client_price_list_overrides_list_price(self):
        test = _lab_test("80.00", "HB")
        client = Client.objects.create(name="City Hospital", code="HOSP1")
        pl = PriceList.objects.create(name="Hosp rate", client=client)
        PriceListItem.objects.create(price_list=pl, lab_test=test, price=Decimal("55.00"))

        # With the client, the negotiated rate applies.
        self.assertEqual(
            resolve_unit_price(line_type=SaleLine.LineType.LAB_TEST, lab_test=test, client=client),
            Decimal("55.00"))
        # Without the client, the list price applies.
        self.assertEqual(
            resolve_unit_price(line_type=SaleLine.LineType.LAB_TEST, lab_test=test),
            Decimal("80.00"))

    def test_default_price_list_used_without_client(self):
        test = _lab_test("80.00", "LFT")
        pl = PriceList.objects.create(name="Default", client=None, is_default=True)
        PriceListItem.objects.create(price_list=pl, lab_test=test, price=Decimal("70.00"))
        self.assertEqual(
            resolve_unit_price(line_type=SaleLine.LineType.LAB_TEST, lab_test=test),
            Decimal("70.00"))

    def test_profile_and_service_pricing(self):
        profile = TestProfile.objects.create(name="Checkup", code="CHK", price=Decimal("250.00"))
        self.assertEqual(
            resolve_unit_price(line_type=SaleLine.LineType.LAB_PROFILE, test_profile=profile),
            Decimal("250.00"))
        service = BillableService.objects.create(
            name="Consult", service_code="CONS", price=Decimal("100.00"))
        self.assertEqual(
            resolve_unit_price(line_type=SaleLine.LineType.CONSULTATION, billable_service=service),
            Decimal("100.00"))

    def test_price_line_respects_explicit_override(self):
        test = _lab_test("80.00", "OVR")
        line = SaleLine(line_type=SaleLine.LineType.LAB_TEST, lab_test=test,
                        unit_price=Decimal("60.00"))
        price_line(line)
        # Explicit price is kept, not overwritten by the catalogue.
        self.assertEqual(line.unit_price, Decimal("60.00"))

    def test_price_line_resolves_service_tax(self):
        tax = TaxRate.objects.create(name="GST5", rate_percent=Decimal("5.00"))
        service = BillableService.objects.create(
            name="Proc", service_code="PRC", price=Decimal("100.00"), tax_rate=tax)
        line = SaleLine(line_type=SaleLine.LineType.SERVICE, billable_service=service)
        price_line(line)
        self.assertEqual(line.unit_price, Decimal("100.00"))
        self.assertEqual(line.tax_percent, Decimal("5.00"))


class SalePricingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", "u@x.io", "pw-strong-123")
        self.location = Location.objects.create(name="Counter")
        self.client.force_authenticate(self.user)

    def test_sale_line_autoresolves_price_for_client(self):
        test = _lab_test("80.00", "API")
        client = Client.objects.create(name="Corp", code="CORP1")
        pl = PriceList.objects.create(name="Corp rate", client=client)
        PriceListItem.objects.create(price_list=pl, lab_test=test, price=Decimal("60.00"))

        resp = self.client.post("/api/v1/pos/sales/", {
            "location": self.location.id,
            "client": client.id,
            "lines": [{"line_type": "LAB_TEST", "lab_test": test.id, "quantity": "1"}],
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        # Price resolved from the client's rate card, not entered manually.
        self.assertEqual(resp.data["lines"][0]["unit_price"], "60.00")
        self.assertEqual(resp.data["grand_total"], "60.00")
        # The sale is billed to the B2B client.
        self.assertEqual(resp.data["client"], client.id)

    def test_reprice_after_setting_client(self):
        test = _lab_test("80.00", "RP")
        client = Client.objects.create(name="Corp2", code="CORP2")
        pl = PriceList.objects.create(name="r", client=client)
        PriceListItem.objects.create(price_list=pl, lab_test=test, price=Decimal("50.00"))

        sale = Sale.objects.create(invoice_number=next_invoice_number(), location=self.location)
        SaleLine.objects.create(sale=sale, line_type=SaleLine.LineType.LAB_TEST,
                                lab_test=test, unit_price=Decimal("80.00"))
        # Assign the client and reprice.
        sale.client = client
        sale.save()
        reprice_sale(sale)
        self.assertEqual(sale.lines.first().unit_price, Decimal("50.00"))
        self.assertEqual(sale.grand_total, Decimal("50.00"))
