from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementYear, AgreementYearDepartment
from app.reference.models import Country, CTIRegion, Department


@pytest.mark.django_db
class TestAgreement:
    def test_create_agreement(self):
        university = create_university()

        agreement = Agreement.objects.create(
            moveon_id="REL-001",
            name="Erasmus outgoing agreement",
            partner_university=university,
            direction="outgoing",
        )

        assert agreement.pk is not None
        assert str(agreement) == "Erasmus outgoing agreement - Universidad Test"

    def test_valid_from_must_be_before_valid_until(self):
        agreement = Agreement(
            name="Invalid agreement",
            partner_university=create_university(),
            valid_from=date(2027, 8, 31),
            valid_until=date(2026, 9, 1),
        )

        with pytest.raises(ValidationError):
            agreement.full_clean()

    def test_moveon_id_unique(self):
        university = create_university()
        Agreement.objects.create(
            moveon_id="REL-001",
            name="First agreement",
            partner_university=university,
        )

        with pytest.raises(IntegrityError):
            Agreement.objects.create(
                moveon_id="REL-001",
                name="Duplicate agreement",
                partner_university=university,
            )


@pytest.mark.django_db
class TestAgreementYear:
    def test_create_agreement_year(self):
        year = create_agreement_year()

        assert year.pk is not None
        assert "actif" in str(year)

    def test_str_shows_inactive(self):
        agreement = create_agreement()
        academic_year = create_academic_year()
        year = AgreementYear.objects.create(
            agreement=agreement,
            academic_year=academic_year,
            is_active=False,
            n7_places=0,
        )

        assert "inactif" in str(year)

    def test_n7_places_cannot_exceed_inp_total(self):
        agreement = create_agreement()
        agreement.inp_total_places = 2
        agreement.save()

        year = AgreementYear(
            agreement=agreement,
            academic_year=create_academic_year(),
            n7_places=3,
        )

        with pytest.raises(ValidationError):
            year.full_clean()

    def test_n7_places_negative_raises(self):
        agreement = create_agreement()
        agreement.inp_total_places = 10
        agreement.save()

        year = AgreementYear(
            agreement=agreement,
            academic_year=create_academic_year(),
            n7_places=-1,
        )

        with pytest.raises(ValidationError):
            year.full_clean()

    def test_unique_agreement_academic_year(self):
        agreement = create_agreement()
        academic_year = create_academic_year()
        AgreementYear.objects.create(
            agreement=agreement,
            academic_year=academic_year,
            n7_places=2,
        )

        with pytest.raises(IntegrityError):
            AgreementYear.objects.create(
                agreement=agreement,
                academic_year=academic_year,
                n7_places=3,
            )


@pytest.mark.django_db
class TestAgreementYearDepartment:
    def test_create_department_quota(self):
        department = Department.objects.create(code="SN", name="Sciences du Numerique")
        year = create_agreement_year()

        dept_quota = AgreementYearDepartment.objects.create(
            agreement_year=year,
            department=department,
            estimated_places=2,
        )

        assert str(dept_quota) == "SN: 2"

    def test_department_quota_unique_per_year(self):
        department = Department.objects.create(code="SN", name="Sciences du Numerique")
        year = create_agreement_year()
        AgreementYearDepartment.objects.create(
            agreement_year=year,
            department=department,
            estimated_places=2,
        )

        with pytest.raises(IntegrityError):
            AgreementYearDepartment.objects.create(
                agreement_year=year,
                department=department,
                estimated_places=1,
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
        moveon_id="REL-001",
        name="Erasmus outgoing agreement",
        partner_university=create_university(),
        inp_total_places=10,
    )


def create_agreement_year():
    return AgreementYear.objects.create(
        agreement=create_agreement(),
        academic_year=create_academic_year(),
        is_active=True,
        n7_places=2,
    )
