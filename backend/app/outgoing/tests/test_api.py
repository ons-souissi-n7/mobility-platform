from datetime import date

import pytest
from django.test import Client

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    AgreementYear,
    AgreementYearDepartment,
)
from app.outgoing.models import Assignment, AssignmentResult, AssignmentStatus, SlotType
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_year(label="2026-2027", **kwargs) -> AcademicYear:
    defaults = {
        "label": label,
        "start_date": date(2026, 9, 1),
        "end_date": date(2027, 8, 31),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


def make_dept(code="SN") -> Department:
    return Department.objects.create(code=code, name=f"Departement {code}")


def make_level(code="3A") -> Level:
    return Level.objects.create(code=code, name=f"Niveau {code}")


def make_student(ine, first_name="Jean", last_name="Dupont") -> Student:
    return Student.objects.create(ine=ine, first_name=first_name, last_name=last_name)


def make_enrollment(student, year, dept, level) -> AnnualEnrollment:
    return AnnualEnrollment.objects.create(
        student=student, academic_year=year, department=dept, level=level
    )


def make_assignment(year, **kwargs) -> Assignment:
    defaults = {"total_students": 0, "assigned_count": 0, "unassigned_count": 0}
    defaults.update(kwargs)
    return Assignment.objects.create(academic_year=year, **defaults)


def make_agreement_year(academic_year, n7_places=3) -> AgreementYear:
    country = Country.objects.create(
        iso2="FR", name_fr="France", name_en="France", cti_region=CTIRegion.FRANCE
    )
    university = PartnerUniversity.objects.create(name="Universite Test", country=country)
    agreement = Agreement.objects.create(
        name="Accord Test",
        partner_university=university,
        direction="outgoing",
        inp_total_places=10,
    )
    return AgreementYear.objects.create(
        agreement=agreement,
        academic_year=academic_year,
        is_active=True,
        n7_places=n7_places,
    )


# ---------------------------------------------------------------------------
# GET /outgoing/assignments/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListAssignments:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()

    def test_list_empty(self):
        response = self.client.get("/api/v1/outgoing/assignments/")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 0
        assert body["results"] == []

    def test_list_returns_assignment(self):
        make_assignment(self.year, total_students=10, assigned_count=8, unassigned_count=2)
        response = self.client.get("/api/v1/outgoing/assignments/")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        result = body["results"][0]
        assert result["academic_year_label"] == "2026-2027"
        assert result["status"] == AssignmentStatus.PROPOSED
        assert result["total_students"] == 10
        assert result["assigned_count"] == 8
        assert result["unassigned_count"] == 2

    def test_list_filter_by_year(self):
        other_year = make_year(
            label="2027-2028",
            start_date=date(2027, 9, 1),
            end_date=date(2028, 8, 31),
        )
        make_assignment(self.year)
        make_assignment(other_year)

        response = self.client.get(f"/api/v1/outgoing/assignments/?year_id={self.year.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["academic_year_label"] == "2026-2027"

    def test_list_returns_most_recent_first(self):
        a1 = make_assignment(self.year)
        a2 = make_assignment(self.year)
        response = self.client.get("/api/v1/outgoing/assignments/")
        body = response.json()
        assert body["results"][0]["id"] == a2.id
        assert body["results"][1]["id"] == a1.id

    def test_list_pagination(self):
        for _ in range(5):
            make_assignment(self.year)
        response = self.client.get("/api/v1/outgoing/assignments/?page=1&page_size=3")
        body = response.json()
        assert body["count"] == 5
        assert len(body["results"]) == 3

    def test_list_response_fields(self):
        make_assignment(self.year)
        body = self.client.get("/api/v1/outgoing/assignments/").json()
        keys = body["results"][0].keys()
        for field in ("id", "academic_year_id", "academic_year_label", "status", "run_by",
                      "total_students", "assigned_count", "unassigned_count", "created_at"):
            assert field in keys


# ---------------------------------------------------------------------------
# GET /outgoing/assignments/{id}/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetAssignment:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.assignment = make_assignment(
            self.year, total_students=5, assigned_count=4, unassigned_count=1
        )

    def test_get_found(self):
        response = self.client.get(f"/api/v1/outgoing/assignments/{self.assignment.id}/")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == self.assignment.id
        assert body["total_students"] == 5
        assert body["assigned_count"] == 4
        assert body["unassigned_count"] == 1
        assert body["status"] == AssignmentStatus.PROPOSED

    def test_get_not_found(self):
        response = self.client.get("/api/v1/outgoing/assignments/9999/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /outgoing/assignments/{id}/results/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListAssignmentResults:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.dept_sn = make_dept("SN")
        self.dept_gi = make_dept("GI")
        self.level = make_level()
        self.assignment = make_assignment(
            self.year, total_students=3, assigned_count=2, unassigned_count=1
        )

        s1 = make_student("INE001", "Alice", "Martin")
        s2 = make_student("INE002", "Bob", "Bernard")
        s3 = make_student("INE003", "Charlie", "Dupont")

        e1 = make_enrollment(s1, self.year, self.dept_sn, self.level)
        e2 = make_enrollment(s2, self.year, self.dept_gi, self.level)
        e3 = make_enrollment(s3, self.year, self.dept_sn, self.level)

        AssignmentResult.objects.create(
            assignment=self.assignment, annual_enrollment=e1, slot_type=SlotType.DEPT
        )
        AssignmentResult.objects.create(
            assignment=self.assignment, annual_enrollment=e2, slot_type=SlotType.SURPLUS
        )
        AssignmentResult.objects.create(
            assignment=self.assignment, annual_enrollment=e3, slot_type=SlotType.UNASSIGNED
        )

    def test_list_returns_all_results(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3

    def test_filter_by_slot_type_unassigned(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?slot_type=unassigned"
        )
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["slot_type"] == "unassigned"

    def test_filter_by_slot_type_dept(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?slot_type=dept"
        )
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["slot_type"] == "dept"

    def test_filter_by_slot_type_surplus(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?slot_type=surplus"
        )
        body = response.json()
        assert body["count"] == 1

    def test_filter_by_department(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/"
            f"?department_id={self.dept_sn.id}"
        )
        body = response.json()
        assert body["count"] == 2

    def test_filter_by_search_last_name(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?search=martin"
        )
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["student_last_name"] == "Martin"

    def test_filter_by_search_first_name(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?search=alice"
        )
        body = response.json()
        assert body["count"] == 1

    def test_filter_by_search_ine(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?search=INE002"
        )
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["student_ine"] == "INE002"

    def test_combined_filters(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/"
            f"?department_id={self.dept_sn.id}&slot_type=dept"
        )
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["department_code"] == "SN"

    def test_result_fields_without_agreement(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?slot_type=unassigned"
        )
        result = response.json()["results"][0]
        assert result["agreement_year_id"] is None
        assert result["agreement_name"] is None
        assert result["university_name"] is None
        assert result["assigned_rank"] is None
        assert "student_ine" in result
        assert "student_last_name" in result
        assert "student_first_name" in result
        assert "department_code" in result

    def test_pagination(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/"
            "?page=1&page_size=2"
        )
        body = response.json()
        assert body["count"] == 3
        assert len(body["results"]) == 2
        assert body["page"] == 1
        assert body["page_size"] == 2

    def test_assignment_not_found_returns_404(self):
        response = self.client.get("/api/v1/outgoing/assignments/9999/results/")
        assert response.status_code == 404

    def test_results_ordered_alphabetically(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/"
        )
        last_names = [r["student_last_name"] for r in response.json()["results"]]
        assert last_names == sorted(last_names)


# ---------------------------------------------------------------------------
# GET /outgoing/assignments/{id}/stats/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetAssignmentStats:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.dept_sn = make_dept("SN")
        self.dept_gi = make_dept("GI")
        self.level = make_level()
        self.assignment = make_assignment(
            self.year, total_students=4, assigned_count=3, unassigned_count=1
        )

        students = [make_student(f"INE{i:03d}", f"Student{i}", "Test") for i in range(4)]
        enrollments = [
            make_enrollment(students[0], self.year, self.dept_sn, self.level),
            make_enrollment(students[1], self.year, self.dept_sn, self.level),
            make_enrollment(students[2], self.year, self.dept_gi, self.level),
            make_enrollment(students[3], self.year, self.dept_sn, self.level),
        ]

        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[0],
            slot_type=SlotType.DEPT,
        )
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[1],
            slot_type=SlotType.SURPLUS,
        )
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[2],
            slot_type=SlotType.DEPT,
        )
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[3],
            slot_type=SlotType.UNASSIGNED,
        )

    def test_stats_totals(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_students"] == 4
        assert body["assigned_count"] == 3
        assert body["unassigned_count"] == 1

    def test_stats_by_slot_type(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        assert body["by_slot_type"]["dept"] == 2
        assert body["by_slot_type"]["surplus"] == 1
        assert body["by_slot_type"]["unassigned"] == 1

    def test_stats_by_department_excludes_unassigned(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        dept_counts = {d["department_code"]: d["count"] for d in body["by_department"]}
        # SN has 2 assigned (1 unassigned not counted)
        assert dept_counts["SN"] == 2
        assert dept_counts["GI"] == 1

    def test_stats_by_agreement_empty_when_no_agreement_year(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        assert body["by_agreement"] == []

    def test_stats_not_found(self):
        response = self.client.get("/api/v1/outgoing/assignments/9999/stats/")
        assert response.status_code == 404

    def test_stats_response_fields(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        for field in ("total_students", "assigned_count", "unassigned_count",
                      "by_slot_type", "by_department", "by_agreement"):
            assert field in body


@pytest.mark.django_db
class TestGetAssignmentStatsWithAgreement:
    """Tests for by_agreement fill rate computation."""

    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.dept = make_dept("SN")
        self.level = make_level()
        self.assignment = make_assignment(
            self.year, total_students=3, assigned_count=2, unassigned_count=1
        )
        self.agreement_year = make_agreement_year(self.year, n7_places=3)

        students = [make_student(f"STA{i:03d}") for i in range(3)]
        enrollments = [
            make_enrollment(s, self.year, self.dept, self.level) for s in students
        ]

        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[0],
            slot_type=SlotType.DEPT,
            agreement_year=self.agreement_year,
            assigned_rank=1,
        )
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[1],
            slot_type=SlotType.SURPLUS,
            agreement_year=self.agreement_year,
            assigned_rank=2,
        )
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollments[2],
            slot_type=SlotType.UNASSIGNED,
            agreement_year=None,
        )

    def test_by_agreement_fill_rate(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        assert len(body["by_agreement"]) == 1
        stat = body["by_agreement"][0]
        assert stat["agreement_name"] == "Accord Test"
        assert stat["total_places"] == 3
        assert stat["assigned"] == 2
        assert stat["fill_rate"] == pytest.approx(66.7)

    def test_by_agreement_includes_university_name(self):
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        stat = body["by_agreement"][0]
        assert stat["university_name"] == "Universite Test"
        assert stat["agreement_year_id"] == self.agreement_year.id

    def test_results_with_agreement_year_fields(self):
        response = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/results/?slot_type=dept"
        )
        result = response.json()["results"][0]
        assert result["agreement_year_id"] == self.agreement_year.id
        assert result["agreement_name"] == "Accord Test"
        assert result["university_name"] == "Universite Test"
        assert result["assigned_rank"] == 1

    def test_fill_rate_100_percent(self):
        students = [make_student(f"STA{i:03d}", "X", "Y") for i in range(10, 11)]
        enrollment = make_enrollment(students[0], self.year, self.dept, self.level)
        AssignmentResult.objects.create(
            assignment=self.assignment,
            annual_enrollment=enrollment,
            slot_type=SlotType.DEPT,
            agreement_year=self.agreement_year,
        )
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        stat = body["by_agreement"][0]
        assert stat["assigned"] == 3
        assert stat["total_places"] == 3
        assert stat["fill_rate"] == pytest.approx(100.0)

    def test_by_agreement_includes_by_department(self):
        """by_department contient quota + assigned par département."""
        agreement_dept = AgreementDepartment.objects.create(
            agreement=self.agreement_year.agreement,
            department=self.dept,
        )
        AgreementYearDepartment.objects.create(
            agreement_year=self.agreement_year,
            agreement_department=agreement_dept,
            estimated_places=2,
        )
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        stat = body["by_agreement"][0]
        assert "by_department" in stat
        dept_stats = stat["by_department"]
        assert len(dept_stats) == 1
        sn = dept_stats[0]
        assert sn["dept_code"] == "SN"
        assert sn["quota"] == 2
        assert sn["assigned"] == 2  # 2 résultats non-unassigned pour SN

    def test_by_department_empty_when_no_quota(self):
        """Sans AgreementYearDepartment, by_department liste quand même les depts affectés."""
        body = self.client.get(
            f"/api/v1/outgoing/assignments/{self.assignment.id}/stats/"
        ).json()
        stat = body["by_agreement"][0]
        # Pas de quota explicite → quota=0, assigned récupéré via AssignmentResult
        assert "by_department" in stat
        dept_stats = stat["by_department"]
        assert len(dept_stats) == 1
        sn = dept_stats[0]
        assert sn["dept_code"] == "SN"
        assert sn["quota"] == 0
        assert sn["assigned"] == 2
