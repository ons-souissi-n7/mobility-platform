"""Unit tests for institution services — validator and transformer (no DB required)."""

from datetime import date

import pytest

from app.institutions.services.moveon_transformer import (
    TransformedInstitution,
    _optional_date,
    transform_institution,
)
from app.institutions.services.moveon_validator import validate_institution
from app.shared.validators import DomainValidationError


class TestValidateInstitution:
    def _make(self, moveon_id=1, name="TU Berlin", country_payload=None):
        if country_payload is None:
            country_payload = {"name": "Germany"}
        inst = TransformedInstitution(
            moveon_id=moveon_id,
            name=name,
            short_name="",
            translated_name="",
            erasmus_code="",
            city="",
            url="",
            email="",
            country_payload=country_payload,
        )
        return inst

    def test_valid_institution_passes(self):
        validate_institution(self._make())

    def test_missing_moveon_id_raises(self):
        with pytest.raises(DomainValidationError, match="moveon_id"):
            validate_institution(self._make(moveon_id=0))

    def test_missing_name_raises(self):
        with pytest.raises(DomainValidationError, match="name"):
            validate_institution(self._make(name=""))

    def test_missing_country_payload_raises(self):
        with pytest.raises(DomainValidationError, match="country"):
            validate_institution(self._make(country_payload={}))


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


class TestTransformInstitution:
    def _payload(self, **kwargs):
        base = {
            "moveon_id": 42,
            "name": "TU Berlin",
            "short_name": "TUB",
            "translated_name": "",
            "erasmus_code": "D BERLIN01",
            "city": "Berlin",
            "url": "https://tu.berlin",
            "email": "info@tu.berlin",
            "country": {"name": "Germany", "iso2": "DE"},
        }
        base.update(kwargs)
        return base

    def test_transform_valid_payload(self):
        result = transform_institution(self._payload())
        assert result.moveon_id == 42
        assert result.name == "TU Berlin"
        assert result.country_payload == {"name": "Germany", "iso2": "DE"}

    def test_non_dict_country_wrapped(self):
        result = transform_institution(self._payload(country="Germany"))
        assert result.country_payload == {"name": "Germany"}

    def test_to_dict_returns_all_fields(self):
        result = transform_institution(self._payload())
        d = result.to_dict()
        assert d["moveon_id"] == 42
        assert d["erasmus_code"] == "D BERLIN01"
        assert "country_payload" in d

    def test_missing_moveon_id_raises(self):
        with pytest.raises(ValueError, match="moveon_id"):
            transform_institution(self._payload(moveon_id=None))
