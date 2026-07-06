"""Unit tests for mobility validators, agreement validity and Hamilton quota distribution."""

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


# ---------------------------------------------------------------------------
# _hamilton — méthode Hamilton (plus grands restes), fonction pure
# ---------------------------------------------------------------------------


class TestHamilton:
    """Tests unitaires de la fonction _hamilton sans accès à la base de données."""

    @pytest.fixture(autouse=True)
    def import_hamilton(self):
        from app.mobility.services.quota_estimator import _hamilton

        self._hamilton = _hamilton

    def test_exact_proportions(self):
        # 2 depts avec effectifs 2:1, 3 places → 2 et 1
        result = self._hamilton(3, {1: 2, 2: 1})
        assert result == {1: 2, 2: 1}
        assert sum(result.values()) == 3

    def test_remainder_goes_to_highest_fraction(self):
        # 3 depts à poids égal, 10 places → 4, 3, 3 (premier dept récupère le reste)
        result = self._hamilton(10, {1: 1, 2: 1, 3: 1})
        assert sum(result.values()) == 10
        assert sorted(result.values(), reverse=True) == [4, 3, 3]

    def test_sum_always_equals_total(self):
        # Invariant principal : la somme == total
        for total in range(1, 20):
            result = self._hamilton(total, {1: 3, 2: 5, 3: 2})
            assert sum(result.values()) == total

    def test_all_weights_zero_falls_back_to_equal_split(self):
        result = self._hamilton(6, {1: 0, 2: 0, 3: 0})
        assert sum(result.values()) == 6
        assert result[1] == result[2] == result[3] == 2

    def test_single_department_gets_all_places(self):
        result = self._hamilton(7, {1: 100})
        assert result == {1: 7}

    def test_more_depts_than_places(self):
        # 5 places pour 8 depts → 5 depts reçoivent 1, 3 depts reçoivent 0
        result = self._hamilton(5, {i: 1 for i in range(8)})
        assert sum(result.values()) == 5
        assert list(result.values()).count(1) == 5
        assert list(result.values()).count(0) == 3

    def test_zero_total_returns_all_zeros(self):
        result = self._hamilton(0, {1: 10, 2: 5})
        assert result == {1: 0, 2: 0}

    def test_proportional_large_enrollment(self):
        # SN=200, 3EA=150, MF2E=50 étudiants, 8 places
        # exact: SN=4.0, 3EA=3.0, MF2E=1.0 → aucun reste
        result = self._hamilton(8, {"SN": 200, "3EA": 150, "MF2E": 50})
        assert result == {"SN": 4, "3EA": 3, "MF2E": 1}
        assert sum(result.values()) == 8

    def test_hamilton_remainder_example(self):
        # SN=100, 3EA=100, MF2E=100 étudiants, 7 places
        # exact: 2.33 chacun → floor=2 chacun, reste=1 → premier dept (par ordre) +1
        result = self._hamilton(7, {"SN": 100, "3EA": 100, "MF2E": 100})
        assert sum(result.values()) == 7
        values = sorted(result.values(), reverse=True)
        assert values == [3, 2, 2]


# ---------------------------------------------------------------------------
# redistribute_department_quotas — intégration DB avec historique voeux/affectations
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRedistributeByHistory:
    """Tests d'intégration : redistribute_department_quotas via historique voeux+affectations."""

    def setup_method(self):
        from app.academic.models import AcademicYear
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import Agreement, AgreementDepartment, AgreementYear
        from app.reference.models import Country, CTIRegion, Department, Level

        self.country = Country.objects.create(
            iso2="FR",
            name_fr="France",
            name_en="France",
            cti_region=CTIRegion.FRANCE,
        )
        self.university = PartnerUniversity.objects.create(
            moveon_id=8001, name="Test Univ", country=self.country
        )
        # Année passée fermée (source de l'historique)
        self.past_year = AcademicYear.objects.create(
            label="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 8, 31),
            status="closed",
        )
        # Année courante (pour laquelle on redistribue)
        self.current_year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
        )
        self.agreement = Agreement.objects.create(
            moveon_id="REL-HAMILTON-01",
            name="Hamilton Test Agreement",
            partner_university=self.university,
        )
        self.level = Level.objects.create(code="3A", name="3ème année")
        self.dept_sn = Department.objects.create(code="SN", name="Systèmes Numériques")
        self.dept_3ea = Department.objects.create(code="3EA", name="Electronique")
        self.dept_mf2e = Department.objects.create(code="MF2E", name="Fluides")
        self.ad_sn = AgreementDepartment.objects.create(
            agreement=self.agreement, department=self.dept_sn
        )
        self.ad_3ea = AgreementDepartment.objects.create(
            agreement=self.agreement, department=self.dept_3ea
        )
        self.ad_mf2e = AgreementDepartment.objects.create(
            agreement=self.agreement, department=self.dept_mf2e
        )
        # AgreementYear passée (nécessaire pour lier les voeux à l'accord)
        self.past_ay = AgreementYear.objects.create(
            agreement=self.agreement,
            academic_year=self.past_year,
            n7_places=6,
            is_active=True,
        )
        # Instance courante à redistribuer
        self.instance = AgreementYear.objects.create(
            agreement=self.agreement,
            academic_year=self.current_year,
            n7_places=6,
            is_active=True,
        )

    def _make_wish(self, dept, n=1):
        """Crée n voeux pour cet accord depuis le département dept (année passée)."""
        from app.students.models import AnnualEnrollment, Student, StudentWish

        for i in range(n):
            s = Student.objects.create(
                ine=f"{dept.pk:06d}{i:05d}",
                last_name=f"NomW{i}",
                first_name="Prénom",
            )
            enrollment = AnnualEnrollment.objects.create(
                student=s,
                academic_year=self.past_year,
                department=dept,
                level=self.level,
            )
            StudentWish.objects.create(
                annual_enrollment=enrollment,
                agreement_year=self.past_ay,
                rank=1,
            )

    def test_redistribution_uses_wish_history(self):
        from app.mobility.models import AgreementYearDepartment
        from app.mobility.services.quota_estimator import redistribute_department_quotas

        # SN=4 voeux, 3EA=2 voeux, MF2E=0 → 6 places : SN=4, 3EA=2, MF2E=0
        self._make_wish(self.dept_sn, 4)
        self._make_wish(self.dept_3ea, 2)

        redistribute_department_quotas(self.instance)

        quotas = {
            dq.agreement_department.department.code: dq.estimated_places
            for dq in AgreementYearDepartment.objects.filter(
                agreement_year=self.instance
            ).select_related("agreement_department__department")
        }
        assert sum(quotas.values()) == 6
        assert quotas["SN"] == 4
        assert quotas["3EA"] == 2
        assert quotas["MF2E"] == 0

    def test_no_history_falls_back_to_equal_split(self):
        from app.mobility.models import AgreementYearDepartment
        from app.mobility.services.quota_estimator import redistribute_department_quotas

        # Aucun voeux historique → répartition égale
        redistribute_department_quotas(self.instance)

        quotas = {
            dq.agreement_department.department.code: dq.estimated_places
            for dq in AgreementYearDepartment.objects.filter(
                agreement_year=self.instance
            ).select_related("agreement_department__department")
        }
        assert sum(quotas.values()) == 6
        assert all(v == 2 for v in quotas.values())

    def test_total_always_equals_n7_places(self):
        from app.mobility.models import AgreementYearDepartment
        from app.mobility.services.quota_estimator import redistribute_department_quotas

        self._make_wish(self.dept_sn, 7)
        self._make_wish(self.dept_3ea, 3)
        self._make_wish(self.dept_mf2e, 1)
        self.instance.n7_places = 7
        self.instance.save()

        redistribute_department_quotas(self.instance)

        total = sum(
            dq.estimated_places
            for dq in AgreementYearDepartment.objects.filter(
                agreement_year=self.instance
            )
        )
        assert total == 7
