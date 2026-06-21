"""Minimal ASTM E1394 driver for analyzer result messages.

ASTM records are typed by their first character: ``H`` header, ``P`` patient,
``O`` order, ``R`` result, ``L`` terminator. Fields are ``|``-delimited and
components ``^``-delimited; records are separated by CR.

Result (``R``) record fields used: R-2 universal test id
(``^^^code^name``), R-3 value, R-4 units, R-5 reference range,
R-6 abnormal flags, R-12 datetime.
"""
from __future__ import annotations

from datetime import datetime

from apps.lis.drivers.base import (
    AnalyzerDriver,
    ParsedMessage,
    ResultMessage,
    normalise_flag,
)


def _parse_astm_datetime(value: str):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            return datetime.strptime(value[: len(fmt) - 6 + 6], fmt)
        except ValueError:
            continue
    try:
        return datetime.strptime(value[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return None


class ASTMDriver(AnalyzerDriver):
    protocol = "ASTM"

    def parse(self, payload: str) -> ParsedMessage:
        message = ParsedMessage(protocol=self.protocol)
        records = [
            r for r in payload.replace("\r\n", "\r").replace("\n", "\r").split("\r")
            if r.strip()
        ]

        patient_id = ""
        specimen_id = ""

        for record in records:
            fields = record.split("|")
            rec_type = fields[0].strip()[-1:] if fields else ""

            if rec_type == "P":
                # P-3 is typically the practice-assigned patient id.
                patient_id = self._get(fields, 3) or patient_id
            elif rec_type == "O":
                specimen_id = self._get(fields, 2) or specimen_id
            elif rec_type == "R":
                try:
                    message.results.append(
                        self._parse_result(fields, patient_id, specimen_id)
                    )
                except Exception as exc:  # noqa: BLE001
                    message.errors.append(f"R parse error: {exc} :: {record}")

        if not message.results and not message.errors:
            message.errors.append("No R result records found.")
        return message

    def _parse_result(self, fields, patient_id, specimen_id) -> ResultMessage:
        universal_id = self._get(fields, 2)
        components = universal_id.split("^")
        # Test code is usually the 4th component (^^^CODE) or the last non-empty.
        non_empty = [c for c in components if c.strip()]
        test_code = (components[3].strip() if len(components) > 3 and components[3].strip()
                     else (non_empty[0] if non_empty else ""))
        return ResultMessage(
            test_code=test_code,
            value=self._get(fields, 3).strip(),
            units=self._get(fields, 4).strip(),
            reference_range=self._get(fields, 5).strip(),
            flag=normalise_flag(self._get(fields, 6)),
            specimen_id=specimen_id,
            patient_id=patient_id,
            observed_at=_parse_astm_datetime(self._get(fields, 12)),
            raw="|".join(fields),
        )

    @staticmethod
    def _get(fields, index):
        return fields[index] if index < len(fields) else ""


DRIVERS = {}


def get_driver(protocol: str) -> AnalyzerDriver:
    """Return a driver instance for ``protocol`` (HL7 or ASTM)."""
    from apps.lis.drivers.hl7 import HL7Driver

    registry = {"HL7": HL7Driver, "ASTM": ASTMDriver}
    cls = registry.get((protocol or "").upper())
    if cls is None:
        raise ValueError(f"No driver for protocol '{protocol}'. Supported: HL7, ASTM.")
    return cls()
