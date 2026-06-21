"""Common types for analyzer drivers.

A *driver* parses a raw message produced by a laboratory instrument (analyzer)
into a normalised list of :class:`ResultMessage` records. The LIS ingestion
service then matches those to open test orders and records the results -- the
parsing concern is kept separate from the persistence concern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ResultMessage:
    """One normalised analyte result emitted by an analyzer."""

    test_code: str                      # analyzer's test/analyte code
    value: str                          # raw value (numeric or coded text)
    units: str = ""
    reference_range: str = ""
    flag: str = ""                      # analyzer-supplied flag (H/L/HH/LL/A/N)
    specimen_id: str = ""               # accession number / sample id
    patient_id: str = ""
    observed_at: datetime | None = None
    raw: str = ""                       # original segment, for audit

    @property
    def numeric_value(self):
        try:
            return float(self.value)
        except (TypeError, ValueError):
            return None


@dataclass
class ParsedMessage:
    """The full parse of one analyzer transmission."""

    protocol: str
    results: list[ResultMessage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class AnalyzerDriver:
    """Base class for analyzer protocol drivers."""

    protocol = "generic"

    def parse(self, payload: str) -> ParsedMessage:  # pragma: no cover - interface
        raise NotImplementedError


# Map common analyzer flag tokens onto Medraxis LabResult flags.
FLAG_NORMALISATION = {
    "H": "H", "HIGH": "H",
    "L": "L", "LOW": "L",
    "HH": "HH", "H!": "HH", "CH": "HH",
    "LL": "LL", "L!": "LL", "CL": "LL",
    "A": "A", "ABNORMAL": "A",
    "N": "N", "NORMAL": "N", "": "",
}


def normalise_flag(token: str) -> str:
    return FLAG_NORMALISATION.get((token or "").strip().upper(), "")
