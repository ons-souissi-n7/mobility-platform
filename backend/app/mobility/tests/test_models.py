from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementQuota, DepartmentQuota
from app.reference.models import Country, CTIRegion, Department


@pytest.mark.django_db
class TestAgreement:
    def test_create_agreement(self):
        university = create_university()

        agreement = Agreement.objects.create(
            moveon_relation_id="REL-001",
            name="Erasmus outgoing agreement",
            partner_university=university,
            direction="outgoing",
            status="active",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
        )

        assert agreement.pk is not None
        assert str(agreement) == "Erasmus outgoing agreement - Universidad Test"

    def test_start_date_must_be_before_end_date(self):
        agreement = Agreement(
            name="Invalid agreement",
            partner_university=create_university(),
            start_date=date(2027, 8, 31),
            end_date=date(2026, 9, 1),
        )

        with pytest.raises(ValidationError):
            agreement.full_clean()

    def test_moveon_relation_id_unique(self):
        university = create_university()
        Agreement.objects.create(
            moveon_relation_id="REL-001",
            name="First agreement",
            partner_university=university,
        )

        with pytest.raises(IntegrityError):
            Agreement.objects.create(
                moveon_relation_id="REL-001",
                name="Duplicate agreement",
                partner_university=university,
            )


@pytest.mark.django_db
class TestAgreementQuota:
    def test_create_agreement_quota(self):
        quota = create_agreement_quota()

        assert quota.allocated_places == 2
        assert str(quota).endswith("(2026-2027)")

    def test_remaining_places_cannot_exceed_total_places(self):
        quota = AgreementQuota(
            agreement=create_agreement(),
            academic_year_label="2026-2027",
            total_places=2,
            remaining_places=3,
        )

        with pytest.raises(ValidationError):
            quota.full_clean()

    def test_unique_quota_period(self):
        agreement = create_agreement()
        AgreementQuota.objects.create(
            agreement=agreement,
            academic_year_label="2026-2027",
            period="S1",
            total_places=2,
            remaining_places=1,
        )

        with pytest.raises(IntegrityError):
            AgreementQuota.objects.create(
                agreement=agreement,
                academic_year_label="2026-2027",
                period="S1",
                total_places=3,
                remaining_places=2,
            )


@pytest.mark.django_db
class TestDepartmentQuota:
    def test_create_department_quota(self):
        department = Department.objects.create(code="SN", name="Sciences du Numerique")
        quota = create_agreement_quota()

        department_quota = DepartmentQuota.objects.create(
            agreement_quota=quota,
            department=department,
            places=2,
        )

        assert str(department_quota) == "SN: 2"

    def test_department_quota_unique_per_quota(self):
        department = Department.objects.create(code="SN", name="Sciences du Numerique")
        quota = create_agreement_quota()
        DepartmentQuota.objects.create(
            agreement_quota=quota,
            department=department,
            places=2,
        )

        with pytest.raises(IntegrityError):
            DepartmentQuota.objects.create(
                agreement_quota=quota,
                department=department,
                places=1,
            )


def create_country():
    return Country.objects.create(
        iso2="ES",
        name_fr="Espagne",
        name_en="Spain",
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )


def create_university():
    return PartnerUniversity.objects.create(
        moveon_id=1001,
        name="Universidad Test",
        country=create_country(),
    )


def create_academic_year():
    return AcademicYear.objects.create(
        label="2026-2027",
        start_date=date(2026, 9, 1),
        end_date=date(2027, 8, 31),
    )


def create_agreement():
    return Agreement.objects.create(
        moveon_relation_id="REL-001",
        name="Erasmus outgoing agreement",
        partner_university=create_university(),
    )


def create_agreement_quota():
    return AgreementQuota.objects.create(
        agreement=create_agreement(),
        academic_year=create_academic_year(),
        academic_year_label="2026-2027",
        period="S1",
        total_places=4,
        remaining_places=2,
    )
