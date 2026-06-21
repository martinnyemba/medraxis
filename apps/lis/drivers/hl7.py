"""Minimal HL7 v2.x driver for analyzer result messages (ORU^R01).

This is a dependency-free parser covering the fields LIS result ingestion needs:
PID (patient), OBR (specimen/order) and OBX (observations). It is deliberately
lenient -- analyzers vary -- and records anything it cannot parse as an error
rather than raising, so one bad segment does not drop the whole batch.

HL7 encoding: segments separated by CR (``\\r``), fields by ``|``, components by
``^``. OBX fields used: OBX-3 identifier (``code^name^system``), OBX-5 value,
OBX-6 units, OBX-7 reference range, OBX-8 abnormal flags, OBX-14 datetime.
"""
from __future__ import annotations

from datetime import datetime

from apps.lis.drivers.base import (
    AnalyzerDriver,
    ParsedMessage,
    ResultMessage,
    normalise_flag,
)


def _parse_hl7_datetime(value: str):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            return datetime.strptime(value[: len(fmt.replace("%", "")) + 2], fmt)
        except ValueError:
            continue
    return None


class HL7Driver(AnalyzerDriver):
    protocol = "HL7"

    def parse(self, payload: str) -> ParsedMessage:
        message = ParsedMessage(protocol=self.protocol)
        # Normalise line endings; HL7 uses CR but analyzers/files often use LF.
        segments = [s for s in payload.replace("\r\n", "\r").replace("\n", "\r").split("\r") if s.strip()]

        patient_id = ""
        specimen_id = ""

        for segment in segments:
            fields = segment.split("|")
            seg_type = fields[0].strip()

            if seg_type == "PID":
                patient_id = self._component(self._get(fields, 3), 0)
            elif seg_type == "OBR":
                # OBR-3 is the filler order/specimen number.
                specimen_id = self._component(self._get(fields, 3), 0) or specimen_id
            elif seg_type == "OBX":
                try:
                    message.results.append(
                        self._parse_obx(fields, patient_id, specimen_id)
                    )
                except Exception as exc:  # noqa: BLE001
                    message.errors.append(f"OBX parse error: {exc} :: {segment}")

        if not message.results and not message.errors:
            message.errors.append("No OBX result segments found.")
        return message

    def _parse_obx(self, fields, patient_id, specimen_id) -> ResultMessage:
        identifier = self._get(fields, 3)
        test_code = self._component(identifier, 0)
        return ResultMessage(
            test_code=test_code,
            value=self._get(fields, 5).strip(),
            units=self._component(self._get(fields, 6), 0),
            reference_range=self._get(fields, 7).strip(),
            flag=normalise_flag(self._get(fields, 8)),
            specimen_id=specimen_id,
            patient_id=patient_id,
            observed_at=_parse_hl7_datetime(self._get(fields, 14)),
            raw="|".join(fields),
        )

    @staticmethod
    def _get(fields, index):
        return fields[index] if index < len(fields) else ""

    @staticmethod
    def _component(field, index):
        parts = field.split("^")
        return parts[index].strip() if index < len(parts) else ""
