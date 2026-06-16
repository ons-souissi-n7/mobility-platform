"""Unit tests for mobility validators and agreement validity (no DB for validators)."""

from datetime import date

import pytest

from app.mobility.services.moveon_transformer import (
    TransformedAgreement,
    TransformedAgreementQuota,
    TransformedMobilityCategory,
)
from app.mobility.services.moveon_validator import (
    ValidationError,
    validate_agreement,
    validate_agreement_quota,
    validate_mobility_category,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_category(**kwargs) -> TransformedMobilityCategory:
    defaults = {"moveon_id": "CAT-001", "name": "Erasmus+"}
    defaults.update(kwargs)
    return TransformedMobilityCategory(**defaults)


def make_agreement(**kwargs) -> TransformedAgreement:
    defaults = {
        "moveon_id": "REL-001",
        "reference": "REF-001",
        "name": "Test Agreement",
        "partner_university_moveon_id": 1,
        "partner_university_id": None,
        "partner_university_erasmus_code": "",
        "partner_university_name": "TU Berlin",
        "relation_type": "student",
        "category_name": "Erasmus",
        "direction": "outgoing",
        "status": "active",
        "is_active": True,
        "start_date": None,
        "end_date": None,
        "start_academic_year": "2024-2025",
        "end_academic_year": "2026-2027",
        "discipline": "",
        "isced": "",
        "level": "3A",
        "formation": "",
        "url": "",
        "restrictions": "",
        "remarks": "",
        "inp_institutions": "N7",
        "department_tokens": (),
        "level_tokens": (),
        "availabilities": (),
    }
    defaults.update(kwargs)
    return TransformedAgreement(**defaults)


def make_quota(**kwargs) -> TransformedAgreementQuota:
    defaults = {
        "moveon_id": "Q-001",
        "agreement_id": None,
        "academic_year_id": None,
        "academic_year_label": "2024-2025",
        "period": "",
        "places_id": None,
        "total_places": 5,
        "remaining_places": 3,
        "total_duration": None,
        "duration_unit": "",
        "is_effective": True,
        "remarks": "",
    }
    defaults.update(kwargs)
    return TransformedAgreementQuota(**defaults)


# ---------------------------------------------------------------------------
# validate_mobility_category
# ---------------------------------------------------------------------------


class TestValidateMobilityCategory:
    def test_valid_category_raises_nothing(self):
        validate_mobility_category(make_category())

    def test_missing_moveon_id_raises(self):
        with pytest.raises(ValidationError, match="Identifiant MoveON du cadre"):
            validate_mobility_category(make_category(moveon_id=""))

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError, match="Nom du cadre"):
            validate_mobility_category(make_category(name=""))


# ---------------------------------------------------------------------------
# validate_agreement
# ---------------------------------------------------------------------------


class TestValidateAgreement:
    def test_valid_agreement_raises_nothing(self):
        validate_agreement(make_agreement())

    def test_missing_moveon_id_raises(self):
        with pytest.raises(ValidationError, match="Identifiant MoveON de l'accord"):
            validate_agreement(make_agreement(moveon_id=""))

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError, match="Nom de l'accord"):
            validate_agreement(make_agreement(name=""))

    def test_start_date_after_end_date_raises(self):
        with pytest.raises(ValidationError, match="Date de début"):
            validate_agreement(
                make_agreement(
                    start_date=date(2026, 9, 1),
                    end_date=date(2025, 8, 31),
                )
            )

    def test_valid_dates_do_not_raise(self):
        validate_agreement(
            make_agreement(
                start_date=date(2020, 9, 1),
                end_date=date(2027, 8, 31),
            )
        )


# ---------------------------------------------------------------------------
# validate_agreement_quota
# ---------------------------------------------------------------------------


class TestValidateAgreementQuota:
    def test_valid_quota_raises_nothing(self):
        validate_agreement_quota(make_quota())

    def test_missing_both_ids_raises(self):
        with pytest.raises(ValidationError, match="Identifiant de quota"):
            validate_agreement_quota(make_quota(moveon_id="", agreement_id=None))

    def test_missing_academic_year_label_raises(self):
        with pytest.raises(ValidationError, match="Année académique"):
            validate_agreement_quota(make_quota(academic_year_label=""))

    def test_negative_total_places_raises(self):
        with pytest.raises(ValidationError, match="places total"):
            validate_agreement_quota(make_quota(total_places=-1, remaining_places=0))

    def test_negative_remaining_places_raises(self):
        with pytest.raises(ValidationError, match="places restantes"):
            validate_agreement_quota(make_quota(remaining_places=-1))

    def test_remaining_exceeds_total_raises(self):
        with pytest.raises(ValidationError, match="Incohérence"):
            validate_agreement_quota(make_quota(total_places=3, remaining_places=5))

    def test_negative_total_duration_raises(self):
        with pytest.raises(ValidationError, match="Durée totale"):
            validate_agreement_quota(make_quota(total_duration=-1))

    def test_none_total_duration_is_valid(self):
        validate_agreement_quota(make_quota(total_duration=None))


# ---------------------------------------------------------------------------
# agreement_validity (requires DB)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAgreementValidity:
    def setup_method(self):
        from app.academic.models import AcademicYear
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import Agreement, AgreementYear
        from app.reference.models import Country, CTIRegion

        self.country = Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        self.university = PartnerUniversity.objects.create(
            moveon_id=9001, name="TU Berlin", country=self.country
        )
        self.year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
        )
        self.agreement = Agreement.objects.create(
            moveon_id="REL-VALID-001",
            name="Validity Test Agreement",
            partner_university=self.university,
        )
        self.AgreementYear = AgreementYear

    def test_active_when_agreement_year_exists(self):
        from app.mobility.services.agreement_validity import (
            is_agreement_active_for_year,
        )

        self.AgreementYear.objects.create(
            agreement=self.agreement,
            academic_year=self.year,
            is_active=True,
        )

        assert is_agreement_active_for_year(self.agreement, self.year) is True

    def test_inactive_when_agreement_year_is_false(self):
        from app.mobility.services.agreement_validity import (
            is_agreement_active_for_year,
        )

        self.AgreementYear.objects.create(
            agreement=self.agreement,
            academic_year=self.year,
            is_active=False,
        )

        assert is_agreement_active_for_year(self.agreement, self.year) is False

    def test_falls_back_to_validity_when_no_agreement_year(self):
        from app.mobility.services.agreement_validity import (
            is_agreement_active_for_year,
        )

        self.agreement.valid_from = date(2020, 1, 1)
        self.agreement.valid_until = date(2030, 12, 31)
        self.agreement.save()

        assert is_agreement_active_for_year(self.agreement, self.year) is True

    def test_not_active_when_valid_from_after_year_end(self):
        from app.mobility.services.agreement_validity import is_within_validity

        self.agreement.valid_from = date(2027, 1, 1)
        self.agreement.valid_until = None
        self.agreement.save()

        assert is_within_validity(self.agreement, self.year) is False

    def test_not_active_when_valid_until_before_year_start(self):
        from app.mobility.services.agreement_validity import is_within_validity

        self.agreement.valid_from = None
        self.agreement.valid_until = date(2024, 8, 31)
        self.agreement.save()

        assert is_within_validity(self.agreement, self.year) is False

    def test_active_when_no_validity_dates(self):
        from app.mobility.services.agreement_validity import is_within_validity

        self.agreement.valid_from = None
        self.agreement.valid_until = None
        self.agreement.save()

        assert is_within_validity(self.agreement, self.year) is True
