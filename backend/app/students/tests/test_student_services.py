"""Unit tests for student validator and transformer (no DB required)."""

import pytest

from app.shared.validators import DomainValidationError
from app.students.services.student_transformer import transform_student, transform_wish
from app.students.services.student_validator import validate_student, validate_wish

# ---------------------------------------------------------------------------
# validate_student
# ---------------------------------------------------------------------------


class TestValidateStudent:
    class _Student:
        def __init__(self, ine="1234567890A", dept="SN", level="3A", last="Dupont"):
            self.ine = ine
            self.department_code = dept
            self.level_code = level
            self.last_name = last

    def test_valid_student_raises_nothing(self):
        validate_student(self._Student())

    def test_missing_ine_raises(self):
        with pytest.raises(DomainValidationError, match="INE"):
            validate_student(self._Student(ine=""))

    def test_missing_department_raises(self):
        with pytest.raises(DomainValidationError, match="département"):
            validate_student(self._Student(dept=""))

    def test_missing_level_raises(self):
        with pytest.raises(DomainValidationError, match="niveau"):
            validate_student(self._Student(level=""))

    def test_missing_last_name_raises(self):
        with pytest.raises(DomainValidationError, match="nom"):
            validate_student(self._Student(last=""))


class TestValidateWish:
    class _Wish:
        def __init__(
            self, offre="Erasmus Berlin", rank=1, ine="1234567890A", individu=""
        ):
            self.offre_de_sejour = offre
            self.rank = rank
            self.ine = ine
            self.individu = individu

    def test_valid_wish_raises_nothing(self):
        validate_wish(self._Wish())

    def test_missing_offre_raises(self):
        with pytest.raises(DomainValidationError, match="offre"):
            validate_wish(self._Wish(offre=""))

    def test_rank_zero_raises(self):
        with pytest.raises(DomainValidationError, match="rang"):
            validate_wish(self._Wish(rank=0))

    def test_rank_negative_raises(self):
        with pytest.raises(DomainValidationError, match="rang"):
            validate_wish(self._Wish(rank=-1))

    def test_no_ine_and_no_individu_raises(self):
        with pytest.raises(DomainValidationError, match="INE"):
            validate_wish(self._Wish(ine="", individu=""))

    def test_individu_without_ine_is_valid(self):
        validate_wish(self._Wish(ine="", individu="Jean Martin"))


# ---------------------------------------------------------------------------
# transform_student
# ---------------------------------------------------------------------------


class TestTransformStudent:
    def _payload(self, **kwargs):
        base = {
            "ine": "1234567890A",
            "first_name": "Jean",
            "last_name": "Martin",
            "email": "jean.martin@etud.n7.fr",
            "gender": "M",
            "department_code": "SN",
            "level_code": "3A",
            "parcours_code": None,
            "gpa": 15.5,
            "nationality_iso2": None,
        }
        base.update(kwargs)
        return base

    def test_valid_payload(self):
        result = transform_student(self._payload())
        assert result.ine == "1234567890A"
        assert result.last_name == "Martin"
        assert result.gpa == 15.5

    def test_empty_ine_raises_value_error(self):
        with pytest.raises(ValueError, match="ine"):
            transform_student(self._payload(ine=""))

    def test_invalid_gpa_becomes_none(self):
        result = transform_student(self._payload(gpa="not-a-number"))
        assert result.gpa is None

    def test_none_gpa_becomes_none(self):
        result = transform_student(self._payload(gpa=None))
        assert result.gpa is None

    def test_empty_gpa_becomes_none(self):
        result = transform_student(self._payload(gpa=""))
        assert result.gpa is None

    def test_nationality_iso2_normalized(self):
        result = transform_student(self._payload(nationality_iso2="fr"))
        assert result.nationality_iso2 == "FR"

    def test_nationality_iso2_none_when_empty(self):
        result = transform_student(self._payload(nationality_iso2=""))
        assert result.nationality_iso2 is None

    def test_parcours_code_normalized(self):
        result = transform_student(self._payload(parcours_code="sesg"))
        assert result.parcours_code == "SESG"

    def test_parcours_code_none_when_absent(self):
        result = transform_student(self._payload(parcours_code=None))
        assert result.parcours_code is None


# ---------------------------------------------------------------------------
# transform_wish
# ---------------------------------------------------------------------------


class TestTransformWish:
    def _payload(self, **kwargs):
        base = {
            "ine": "1234567890A",
            "individu": "Jean Martin",
            "offre_de_sejour": "Erasmus+ TU Berlin 2025",
            "rank": 1,
        }
        base.update(kwargs)
        return base

    def test_valid_payload(self):
        result = transform_wish(self._payload())
        assert result.ine == "1234567890A"
        assert result.rank == 1

    def test_empty_offre_raises(self):
        with pytest.raises(ValueError, match="offre_de_sejour"):
            transform_wish(self._payload(offre_de_sejour=""))

    def test_rank_zero_raises(self):
        with pytest.raises(ValueError, match="rank"):
            transform_wish(self._payload(rank=0))

    def test_rank_negative_raises(self):
        with pytest.raises(ValueError, match="rank"):
            transform_wish(self._payload(rank=-5))
