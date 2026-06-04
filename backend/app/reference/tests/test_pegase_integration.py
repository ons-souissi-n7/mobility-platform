"""
Tests pour la couche de transformation et validation Pegase.

Valide que chaque étape du pipeline (transform -> validate) fonctionne
indépendamment.
"""

import pytest

from app.reference.services.pegase_schema import validate_raw_payload
from app.reference.services.pegase_transformer import transform_department
from app.reference.services.pegase_validator import (
    ValidationError,
    validate_department,
)


class TestPegaseSchema:
    """Tests pour la validation de la structure brute."""

    def test_validate_raw_payload_accepts_dict(self):
        payload = {"pegase_id": "101", "code": "SN", "name": "Sciences"}
        result = validate_raw_payload(payload)
        assert result == payload

    def test_validate_raw_payload_rejects_non_dict(self):
        with pytest.raises(ValueError, match="objet JSON est attendu"):
            validate_raw_payload("invalid")

        with pytest.raises(ValueError, match="objet JSON est attendu"):
            validate_raw_payload([])


class TestPegaseTransformer:
    """Tests pour la transformation des données brutes."""

    def test_transform_normalizes_strings(self):
        payload = {
            "pegase_id": "  101  ",
            "code": "  SN  ",
            "name": "  Sciences du Numerique  ",
        }
        result = transform_department(payload)

        assert result.pegase_id == "101"
        assert result.code == "SN"
        assert result.name == "Sciences du Numerique"

    def test_transform_handles_missing_fields(self):
        payload = {"pegase_id": "101"}
        result = transform_department(payload)

        assert result.pegase_id == "101"
        assert result.code == ""
        assert result.name == ""

    def test_transform_to_dict(self):
        payload = {"pegase_id": "101", "code": "SN", "name": "Sciences"}
        result = transform_department(payload)
        dict_form = result.to_dict()

        assert dict_form == {
            "pegase_id": "101",
            "code": "SN",
            "name": "Sciences",
        }


class TestPegaseValidator:
    """Tests pour la validation des règles métier."""

    def test_validate_rejects_missing_pegase_id(self):
        from app.reference.services.pegase_transformer import TransformedDepartment

        data = TransformedDepartment(pegase_id="", code="SN", name="Sciences")

        with pytest.raises(ValidationError, match="Identifiant Pégase"):
            validate_department(data)

    def test_validate_rejects_missing_code(self):
        from app.reference.services.pegase_transformer import TransformedDepartment

        data = TransformedDepartment(pegase_id="101", code="", name="Sciences")

        with pytest.raises(ValidationError, match="Code du département"):
            validate_department(data)

    def test_validate_rejects_missing_name(self):
        from app.reference.services.pegase_transformer import TransformedDepartment

        data = TransformedDepartment(pegase_id="101", code="SN", name="")

        with pytest.raises(ValidationError, match="Nom du département"):
            validate_department(data)

    def test_validate_accepts_complete_data(self):
        from app.reference.services.pegase_transformer import TransformedDepartment

        data = TransformedDepartment(pegase_id="101", code="SN", name="Sciences")
        # Should not raise
        validate_department(data)
