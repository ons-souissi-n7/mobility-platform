from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.analytics.services import (
    get_country_breakdown,
    get_department_breakdown,
    get_mobility_trends,
    get_university_breakdown,
)
from app.complementary.models import ComplementaryMobility
from app.incoming.models import IncomingStudent
from app.institutions.models import PartnerUniversity
from app.internships.models import Internship
from app.mobility.models import Agreement, AgreementYear
from app.outgoing.models import Assignment, AssignmentResult, SlotType
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_year(label: str, *, start_year: int) -> AcademicYear:
    return AcademicYear.objects.create(
        label=label,
        start_date=date(start_year, 9, 1),
        end_date=date(start_year + 1, 8, 31),
    )


def _make_country(iso2: str, name_fr: str) -> Country:
    return Country.objects.create(
        iso2=iso2,
        name_fr=name_fr,
        name_en=name_fr,
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )


def _make_department(code: str) -> Department:
    return Department.objects.create(code=code, name=code)


def _make_level() -> Level:
    return Level.objects.get_or_create(code="3A", defaults={"name": "Troisième année"})[
        0
    ]


def _make_student(ine: str) -> Student:
    return Student.objects.create(
        ine=ine,
        first_name="Test",
        last_name=ine,
        email=f"{ine.lower()}@example.com",
    )


def _make_enrollment(
    student: Student, year: AcademicYear, dept: Department
) -> AnnualEnrollment:
    return AnnualEnrollment.objects.create(
        student=student,
        academic_year=year,
        department=dept,
        level=_make_level(),
    )


def _make_assignment(year: AcademicYear, **kwargs) -> Assignment:
    return Assignment.objects.create(academic_year=year, **kwargs)


def _publish(assignment: Assignment) -> Assignment:
    Assignment.objects.filter(pk=assignment.pk).update(status="published")
    return Assignment.objects.get(pk=assignment.pk)


def _make_university(name: str, country: Country) -> PartnerUniversity:
    return PartnerUniversity.objects.create(name=name, country=country)


def _make_agreement_year(
    university: PartnerUniversity, year: AcademicYear
) -> AgreementYear:
    agreement = Agreement.objects.create(
        name=f"Accord {university.name}",
        partner_university=university,
    )
    return AgreementYear.objects.create(agreement=agreement, academic_year=year)


# ── get_mobility_trends ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetMobilityTrends:
    def test_returns_empty_when_no_years(self):
        assert get_mobility_trends(5) == []

    def test_returns_one_entry_per_year_with_label(self):
        _make_year("2024-2025", start_year=2024)
        result = get_mobility_trends(1)
        assert len(result) == 1
        assert result[0]["label"] == "2024-2025"

    def test_outgoing_uses_assigned_count_from_published_assignment(self):
        year = _make_year("2024-2025", start_year=2024)
        assignment = _make_assignment(
            year, assigned_count=7, total_students=10, unassigned_count=3
        )
        _publish(assignment)

        result = get_mobility_trends(1)
        assert result[0]["outgoing"] == 7

    def test_outgoing_zero_when_assignment_not_published(self):
        year = _make_year("2024-2025", start_year=2024)
        _make_assignment(year, assigned_count=5, total_students=10, unassigned_count=5)

        result = get_mobility_trends(1)
        assert result[0]["outgoing"] == 0

    def test_incoming_counts_all_incoming_students(self):
        year = _make_year("2024-2025", start_year=2024)
        for i in range(3):
            IncomingStudent.objects.create(
                academic_year=year,
                first_name=f"Prénom{i}",
                last_name=f"Nom{i}",
            )

        result = get_mobility_trends(1)
        assert result[0]["incoming"] == 3

    def test_internship_counts_all_internships(self):
        year = _make_year("2024-2025", start_year=2024)
        student = _make_student("ANA001SRV")
        Internship.objects.create(
            student=student, academic_year=year, company_name="Acme"
        )

        result = get_mobility_trends(1)
        assert result[0]["internships"] == 1

    def test_complementary_counts_only_validated(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("DE", "Allemagne")

        # Pending — must NOT be counted
        ComplementaryMobility.objects.create(
            student=_make_student("ANA002PND"),
            academic_year=year,
            experience_type="Summer school",
            destination_country=country,
            destination_institution="TU Munich",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 7, 31),
        )
        # Validated — must be counted
        mob = ComplementaryMobility.objects.create(
            student=_make_student("ANA003VAL"),
            academic_year=year,
            experience_type="Stage",
            destination_country=country,
            destination_institution="Siemens",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
        )
        ComplementaryMobility.objects.filter(pk=mob.pk).update(status="validated")

        result = get_mobility_trends(1)
        assert result[0]["complementary"] == 1

    def test_respects_n_years_limit(self):
        for i in range(3):
            _make_year(f"202{i}-202{i+1}", start_year=2020 + i)

        result = get_mobility_trends(2)
        assert len(result) == 2
        # The 2 most recent years in chronological order
        assert result[0]["label"] == "2021-2022"
        assert result[1]["label"] == "2022-2023"


# ── get_department_breakdown ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetDepartmentBreakdown:
    def test_structure_has_required_keys(self):
        result = get_department_breakdown(1)
        for key in ("outgoing", "incoming", "internships"):
            assert "years" in result[key]
            assert "series" in result[key]

    def test_outgoing_counted_per_department(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("SN")
        student = _make_student("ANA010OUT")
        enrollment = _make_enrollment(student, year, dept)
        assignment = _publish(_make_assignment(year))

        country = _make_country("DE", "Allemagne")
        ay = _make_agreement_year(_make_university("TU Berlin", country), year)
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            agreement_year=ay,
            slot_type=SlotType.DEPT,
        )

        result = get_department_breakdown(1)
        sn = next((s for s in result["outgoing"]["series"] if s["label"] == "SN"), None)
        assert sn is not None
        assert sn["values"][0] == 1

    def test_outgoing_excludes_results_without_agreement_year(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("EA")
        student = _make_student("ANA011UNS")
        enrollment = _make_enrollment(student, year, dept)
        assignment = _publish(_make_assignment(year))
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            agreement_year=None,
            slot_type=SlotType.UNASSIGNED,
        )

        result = get_department_breakdown(1)
        assert result["outgoing"]["series"] == []

    def test_incoming_counted_per_department(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("MF")
        IncomingStudent.objects.create(
            academic_year=year, department=dept, first_name="Maria", last_name="Santos"
        )

        result = get_department_breakdown(1)
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "MF" in labels

    def test_filter_by_dept_ids_restricts_results(self):
        year = _make_year("2024-2025", start_year=2024)
        dept_a = _make_department("GE")
        dept_b = _make_department("TC")
        for dept in (dept_a, dept_b):
            IncomingStudent.objects.create(
                academic_year=year,
                department=dept,
                first_name="X",
                last_name=f"Student-{dept.code}",
            )

        result = get_department_breakdown(1, dept_ids=[dept_a.id])
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "GE" in labels
        assert "TC" not in labels

    def test_internships_counted_per_department_via_enrollment(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("IN")
        student = _make_student("ANA020INT")
        _make_enrollment(student, year, dept)
        Internship.objects.create(
            student=student, academic_year=year, company_name="IBM"
        )

        result = get_department_breakdown(1)
        labels = [s["label"] for s in result["internships"]["series"]]
        assert "IN" in labels


# ── get_country_breakdown ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetCountryBreakdown:
    def test_structure_has_required_keys(self):
        result = get_country_breakdown(1)
        for key in ("outgoing", "incoming", "internships"):
            assert "years" in result[key]
            assert "series" in result[key]

    def test_incoming_counted_by_country(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("JP", "Japon")
        IncomingStudent.objects.create(
            academic_year=year, country=country, first_name="Yuki", last_name="Tanaka"
        )

        result = get_country_breakdown(1)
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "Japon" in labels

    def test_internships_counted_by_country(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("US", "États-Unis")
        student = _make_student("ANA030INT")
        Internship.objects.create(
            student=student, academic_year=year, company_name="Google", country=country
        )

        result = get_country_breakdown(1)
        labels = [s["label"] for s in result["internships"]["series"]]
        assert "États-Unis" in labels

    def test_outgoing_counted_by_country(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("SN5")
        student = _make_student("ANA031OUT")
        enrollment = _make_enrollment(student, year, dept)
        assignment = _publish(_make_assignment(year))

        country = _make_country("GB", "Royaume-Uni")
        ay = _make_agreement_year(_make_university("Imperial College", country), year)
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            agreement_year=ay,
            slot_type=SlotType.DEPT,
        )

        result = get_country_breakdown(1)
        labels = [s["label"] for s in result["outgoing"]["series"]]
        assert "Royaume-Uni" in labels

    def test_top_10_limit_applied_without_filter(self):
        year = _make_year("2024-2025", start_year=2024)
        iso_chars = "ABCDEFGHIJKL"
        for i in range(12):
            country = Country.objects.create(
                iso2=f"{iso_chars[i]}Z",
                name_fr=f"Pays{i}",
                name_en=f"Country{i}",
                cti_region=CTIRegion.EUROPE_HORS_FRANCE,
            )
            IncomingStudent.objects.create(
                academic_year=year,
                country=country,
                first_name="X",
                last_name=f"Student{i}",
            )

        result = get_country_breakdown(1)
        assert len(result["incoming"]["series"]) == 10

    def test_filter_by_country_ids_restricts_results(self):
        year = _make_year("2024-2025", start_year=2024)
        fr = _make_country("FR", "France")
        es = _make_country("ES", "Espagne")
        for country in (fr, es):
            IncomingStudent.objects.create(
                academic_year=year,
                country=country,
                first_name="A",
                last_name=f"B-{country.iso2}",
            )

        result = get_country_breakdown(1, country_ids=[fr.id])
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "France" in labels
        assert "Espagne" not in labels


# ── get_university_breakdown ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetUniversityBreakdown:
    def test_internships_series_always_empty(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("AU", "Australie")
        student = _make_student("ANA040INT")
        Internship.objects.create(
            student=student, academic_year=year, company_name="Telstra", country=country
        )
        result = get_university_breakdown(1)
        assert result["internships"]["series"] == []

    def test_outgoing_counted_by_university(self):
        year = _make_year("2024-2025", start_year=2024)
        dept = _make_department("SN6")
        student = _make_student("ANA041OUT")
        enrollment = _make_enrollment(student, year, dept)
        assignment = _publish(_make_assignment(year))

        country = _make_country("SE", "Suède")
        univ = _make_university("KTH Stockholm", country)
        ay = _make_agreement_year(univ, year)
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            agreement_year=ay,
            slot_type=SlotType.DEPT,
        )

        result = get_university_breakdown(1)
        labels = [s["label"] for s in result["outgoing"]["series"]]
        assert "KTH Stockholm" in labels

    def test_incoming_counted_by_origin_university(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("IT", "Italie")
        univ = _make_university("Politecnico di Milano", country)
        IncomingStudent.objects.create(
            academic_year=year,
            origin_university=univ,
            first_name="Marco",
            last_name="Rossi",
        )

        result = get_university_breakdown(1)
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "Politecnico di Milano" in labels

    def test_top_10_limit_applied_without_filter(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("PL", "Pologne")
        for i in range(12):
            univ = PartnerUniversity.objects.create(name=f"UnivPL{i}", country=country)
            IncomingStudent.objects.create(
                academic_year=year,
                origin_university=univ,
                first_name="X",
                last_name=f"StudentPL{i}",
            )

        result = get_university_breakdown(1)
        assert len(result["incoming"]["series"]) == 10

    def test_filter_by_univ_ids_restricts_results(self):
        year = _make_year("2024-2025", start_year=2024)
        country = _make_country("CH", "Suisse")
        epfl = _make_university("EPFL", country)
        eth = _make_university("ETH Zurich", country)
        for univ in (epfl, eth):
            IncomingStudent.objects.create(
                academic_year=year,
                origin_university=univ,
                first_name="X",
                last_name=f"Student-{univ.name}",
            )

        result = get_university_breakdown(1, univ_ids=[epfl.id])
        labels = [s["label"] for s in result["incoming"]["series"]]
        assert "EPFL" in labels
        assert "ETH Zurich" not in labels
