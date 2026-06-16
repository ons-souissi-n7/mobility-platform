"""Unit tests for reference/services/pegase_transformer.py — no DB required."""

from datetime import date

from app.reference.services.pegase_transformer import (
    _optional_date,
    transform_department,
)


class TestOptionalDate:
    def test_none_returns_none(self):
        assert _optional_date(None) is None

    def test_empty_string_returns_none(self):
        assert _optional_date("") is None

    def test_date_object_returned_as_is(self):
        d = date(2025, 6, 1)
        assert _optional_date(d) == d

    def test_iso_string_parsed(self):
        assert _optional_date("2025-06-01") == date(2025, 6, 1)

    def test_iso_with_time_parsed(self):
        assert _optional_date("2025-06-01T14:30:00") == date(2025, 6, 1)

    def test_dd_mm_yyyy_with_time_parsed(self):
        assert _optional_date("01/06/2025 14:30") == date(2025, 6, 1)

    def test_dd_mm_yyyy_parsed(self):
        assert _optional_date("01/06/2025") == date(2025, 6, 1)

    def test_invalid_string_returns_none(self):
        assert _optional_date("not-a-date") is None


class TestTransformDepartment:
    def test_valid_payload(self):
        result = transform_department(
            {"pegase_id": "D001", "code": "SN", "name": "Sciences du Numérique"}
        )
        assert result.pegase_id == "D001"
        assert result.code == "SN"
        assert result.name == "Sciences du Numérique"

    def test_to_dict(self):
        result = transform_department(
            {"pegase_id": "D002", "code": "TC", "name": "Tronc Commun"}
        )
        d = result.to_dict()
        assert d["code"] == "TC"
        assert d["pegase_id"] == "D002"

    def test_updated_at_parsed(self):
        result = transform_department(
            {
                "pegase_id": "D003",
                "code": "3EA",
                "name": "Electronique",
                "updated_at": "2024-09-01",
            }
        )
        assert result.source_updated_at == date(2024, 9, 1)
