"""Unit tests for institutions/services/pegase_validator.py and pegase_transformer.py — no DB."""

import pytest

from app.institutions.services.pegase_transformer import (
    TransformedDepartment,
    transform_department,
)
from app.institutions.services.pegase_validator import validate_department
from app.shared.validators import DomainValidationError


class TestInstitutionsPegaseTransformer:
    def test_transform_valid_payload(self):
        result = transform_department(
            {"pegase_id": "42", "code": "SN", "name": "Sciences du Numérique"}
        )
        assert result.pegase_id == "42"
        assert result.code == "SN"
        assert result.name == "Sciences du Numérique"

    def test_missing_pegase_id_raises(self):
        with pytest.raises(ValueError, match="pegase_id"):
            transform_department({"code": "SN", "name": "Sciences du Numérique"})

    def test_empty_pegase_id_raises(self):
        with pytest.raises(ValueError, match="pegase_id"):
            transform_department({"pegase_id": "", "code": "SN", "name": "Sciences"})

    def test_code_uppercased(self):
        result = transform_department(
            {"pegase_id": "1", "code": "sn", "name": "Sciences"}
        )
        assert result.code == "SN"

    def test_returns_transformed_department_dataclass(self):
        result = transform_department(
            {"pegase_id": "99", "code": "TC", "name": "Tronc Commun"}
        )
        assert isinstance(result, TransformedDepartment)
        assert result.pegase_id == "99"


class TestInstitutionsPegaseValidator:
    def _make(self, code="SN", name="Sciences du Numérique"):
        return TransformedDepartment(pegase_id="42", code=code, name=name)

    def test_valid_department_passes(self):
        validate_department(self._make())

    def test_missing_code_raises(self):
        with pytest.raises(DomainValidationError, match="code"):
            validate_department(self._make(code=""))

    def test_missing_name_raises(self):
        with pytest.raises(DomainValidationError, match="name"):
            validate_department(self._make(name=""))
