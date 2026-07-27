"""Tests unitaires pour les services CTI."""

from __future__ import annotations

from datetime import date

import pytest

from app.cti.services import compute_cti_duration, get_student_mobility_history
from app.students.models import Student

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def student(db) -> Student:
    return Student.objects.create(
        ine="CTI0000001A",
        first_name="Léa",
        last_name="Martin",
        email="lea.martin@example.com",
    )


@pytest.fixture()
def country_de(db):
    from app.reference.models import Country, CTIRegion

    return Country.objects.create(
        iso2="DE",
        name_fr="Allemagne",
        name_en="Germany",
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )


@pytest.fixture()
def country_fr(db):
    from app.reference.models import Country, CTIRegion

    return Country.objects.create(
        iso2="FR",
        name_fr="France",
        name_en="France",
        cti_region=CTIRegion.FRANCE,
    )


@pytest.fixture()
def academic_year(db):
    from app.academic.models import AcademicYear

    return AcademicYear.objects.create(
        label="2024-2025",
        start_date=date(2024, 9, 1),
        end_date=date(2025, 8, 31),
    )


# ---------------------------------------------------------------------------
# compute_cti_duration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestComputeCtiDuration:
    def test_returns_zeros_for_student_with_no_mobility(self, student):
        result = compute_cti_duration(student)

        assert result["exchange_weeks"] == 0.0
        assert result["internship_weeks"] == 0.0
        assert result["complementary_weeks"] == 0.0
        assert result["total_weeks"] == 0.0

    def test_does_not_include_meets_cti_field(self, student):
        result = compute_cti_duration(student)

        assert "meets_cti" not in result
        assert "cti_threshold_weeks" not in result

    def test_counts_validated_complementary_mobility(
        self, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        # 14 jours = 2 semaines exactes
        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 15),
        )
        m.validate()
        m.save()

        result = compute_cti_duration(student)

        assert result["complementary_weeks"] == 2.0
        assert result["total_weeks"] == 2.0

    def test_ignores_pending_complementary_mobility(
        self, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 15),
        )

        result = compute_cti_duration(student)

        assert result["complementary_weeks"] == 0.0
        assert result["total_weeks"] == 0.0

    def test_ignores_rejected_complementary_mobility(
        self, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 15),
        )
        m.reject(reason="Documents insuffisants")
        m.save()

        result = compute_cti_duration(student)

        assert result["complementary_weeks"] == 0.0

    def test_counts_international_internship(self, student, country_de, academic_year):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="BOSCH GmbH",
            country=country_de,
            weeks_in_company=12,
        )

        result = compute_cti_duration(student)

        assert result["internship_weeks"] == 12.0
        assert result["total_weeks"] == 12.0

    def test_ignores_french_internship(self, student, country_fr, academic_year):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Airbus France",
            country=country_fr,
            weeks_in_company=12,
        )

        result = compute_cti_duration(student)

        assert result["internship_weeks"] == 0.0

    def test_ignores_internship_without_duration(
        self, student, country_de, academic_year
    ):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="BOSCH GmbH",
            country=country_de,
            weeks_in_company=None,
        )

        result = compute_cti_duration(student)

        assert result["internship_weeks"] == 0.0

    def test_sums_multiple_mobilities(self, student, country_de, academic_year):
        from app.complementary.models import ComplementaryMobility
        from app.internships.models import Internship

        # Stage : 8 sem.
        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="BOSCH GmbH",
            country=country_de,
            weeks_in_company=8,
        )

        # Mobilité complémentaire validée : 14 jours = 2 sem.
        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 15),
        )
        m.validate()
        m.save()

        result = compute_cti_duration(student)

        assert result["internship_weeks"] == 8.0
        assert result["complementary_weeks"] == 2.0
        assert result["total_weeks"] == 10.0


# ---------------------------------------------------------------------------
# get_student_mobility_history
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetStudentMobilityHistory:
    def test_returns_correct_structure_for_empty_student(self, student):
        result = get_student_mobility_history(student)

        assert result["ine"] == student.ine
        assert result["exchanges"] == []
        assert result["internships"] == []
        assert result["complementary_mobilities"] == []
        assert result["totals"]["total_weeks"] == 0.0

    def test_history_includes_all_internship_countries(
        self, student, country_fr, country_de, academic_year
    ):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Airbus",
            country=country_fr,
            weeks_in_company=6,
        )
        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="BOSCH",
            country=country_de,
            weeks_in_company=8,
        )

        result = get_student_mobility_history(student)

        assert len(result["internships"]) == 2
        companies = {i["company_name"] for i in result["internships"]}
        assert companies == {"Airbus", "BOSCH"}

    def test_history_flags_international_internships(
        self, student, country_fr, country_de, academic_year
    ):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Airbus",
            country=country_fr,
            weeks_in_company=6,
        )
        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="BOSCH",
            country=country_de,
            weeks_in_company=8,
        )

        result = get_student_mobility_history(student)
        by_company = {i["company_name"]: i for i in result["internships"]}

        assert by_company["Airbus"]["is_international"] is False
        assert by_company["BOSCH"]["is_international"] is True

    def test_history_includes_all_complementary_statuses(
        self, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 14),
        )

        validated = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Séjour linguistique",
            destination_country=country_de,
            start_date=date(2024, 8, 1),
            end_date=date(2024, 8, 15),  # 14 jours = 2 semaines exactes
        )
        validated.validate()
        validated.save()

        rejected = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Conférence",
            destination_country=country_de,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 9, 7),
        )
        rejected.reject(reason="Non éligible")
        rejected.save()

        result = get_student_mobility_history(student)
        statuses = {m["status"] for m in result["complementary_mobilities"]}

        assert statuses == {"pending", "validated", "rejected"}
        # Seule la validée compte dans les totaux
        assert result["totals"]["complementary_weeks"] == 2.0

    def test_history_computes_duration_weeks_for_complementary(
        self, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Programme court",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 22),  # 21 jours = 3 semaines exactes
        )
        m.validate()
        m.save()

        result = get_student_mobility_history(student)

        assert len(result["complementary_mobilities"]) == 1
        assert result["complementary_mobilities"][0]["duration_weeks"] == 3.0
