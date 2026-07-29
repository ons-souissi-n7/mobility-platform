"""Tests d'intégration pour l'endpoint d'export CTI."""

from __future__ import annotations

from datetime import date

import pytest
from ninja.testing import TestClient

from app.cti.api import router
from app.cti.services_export import _parse_incoming_duration


@pytest.fixture()
def client() -> TestClient:
    return TestClient(router)


@pytest.fixture()
def academic_year(db):
    from app.academic.models import AcademicYear

    return AcademicYear.objects.create(
        label="2024-2025",
        start_date=date(2024, 9, 1),
        end_date=date(2025, 8, 31),
    )


# ---------------------------------------------------------------------------
# _parse_incoming_duration (pure function — no DB)
# ---------------------------------------------------------------------------


class TestParseIncomingDuration:
    def test_1_semestre_is_eq(self):
        assert _parse_incoming_duration("1 semestre") == "eq"

    def test_un_semestre_is_eq(self):
        assert _parse_incoming_duration("un semestre") == "eq"

    def test_2_semestres_is_gt(self):
        assert _parse_incoming_duration("2 semestres") == "gt"

    def test_1_an_is_gt(self):
        # régression : "1 an" doit être > 1 sem, pas < 1 sem
        assert _parse_incoming_duration("1 an") == "gt"

    def test_un_an_is_gt(self):
        assert _parse_incoming_duration("un an") == "gt"

    def test_1_annee_is_gt(self):
        assert _parse_incoming_duration("1 année") == "gt"

    def test_12_mois_is_gt(self):
        assert _parse_incoming_duration("12 mois") == "gt"

    def test_3_mois_is_lt(self):
        assert _parse_incoming_duration("3 mois") == "lt"

    def test_4_mois_is_lt(self):
        # 4 × 4.33 ≈ 17 sem < 20 → lt
        assert _parse_incoming_duration("4 mois") == "lt"

    def test_5_mois_is_eq(self):
        # 5 × 4.33 ≈ 21.6 sem ≥ 20 et < 40 → eq
        assert _parse_incoming_duration("5 mois") == "eq"

    def test_empty_string_defaults_to_lt(self):
        assert _parse_incoming_duration("") == "lt"

    def test_none_defaults_to_lt(self):
        assert _parse_incoming_duration(None) == "lt"  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# GET /stats/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetCtiStats:
    def test_returns_404_for_unknown_year(self, client, db):
        response = client.get("/stats/?academic_year_id=99999")

        assert response.status_code == 404

    def test_returns_correct_top_level_structure(self, client, academic_year):
        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        assert response.status_code == 200
        data = response.json()
        for field in (
            "academic_year_label",
            "enrolled_fise",
            "enrolled_fisa",
            "exchanges",
            "internships",
            "incoming",
            "dd_outgoing",
            "dd_incoming",
            "pct_fise",
            "pct_fisa",
            "avg_months_fise",
            "avg_months_fisa",
        ):
            assert field in data, f"champ manquant : {field}"

    def test_academic_year_label_matches(self, client, academic_year):
        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        assert response.json()["academic_year_label"] == "2024-2025"

    def test_dd_outgoing_contains_six_regions(self, client, academic_year):
        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        dd = response.json()["dd_outgoing"]
        assert len(dd) == 6
        region_names = {r["region"] for r in dd}
        assert "Europe (hors France)" in region_names
        assert "Canada / États-Unis" in region_names
        assert "Pays d'Afrique" in region_names

    def test_dd_incoming_contains_six_regions(self, client, academic_year):
        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        dd = response.json()["dd_incoming"]
        assert len(dd) == 6

    def test_dd_outgoing_region_row_has_correct_fields(self, client, academic_year):
        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        row = response.json()["dd_outgoing"][0]
        assert "region" in row
        assert "hommes" in row
        assert "femmes" in row
        assert "total" in row

    def test_dd_outgoing_counts_dd_fise_exchange_by_region(
        self, client, academic_year, db
    ):
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import Agreement, AgreementYear, MobilityCategory
        from app.outgoing.models import Assignment, AssignmentResult, SlotType
        from app.reference.models import Country, CTIRegion, Department, Level, Parcours
        from app.students.models import AnnualEnrollment, Student

        year = academic_year

        level = Level.objects.create(code="3ING", name="3ème année", is_terminal=True)
        dept = Department.objects.create(code="SN", name="Sciences du Numérique")
        parc = Parcours.objects.create(
            code="IA", label="Intelligence Artificielle", department=dept
        )
        cat_dd = MobilityCategory.objects.create(name="DD")
        country_ca = Country.objects.create(
            iso2="CA",
            name_fr="Canada",
            name_en="Canada",
            cti_region=CTIRegion.CANADA_USA,
        )
        pu = PartnerUniversity.objects.create(
            name="Univ. Laval", country=country_ca, city="Québec"
        )
        ag = Agreement.objects.create(
            name="DD Laval", partner_university=pu, category=cat_dd
        )
        ay = AgreementYear.objects.create(
            agreement=ag,
            academic_year=year,
            duration_weeks=40,
            is_active=True,
            n7_places=2,
            inp_total_places=2,
        )
        student = Student.objects.create(
            ine="CTIDDT0001B",
            first_name="Marc",
            last_name="Roux",
            email="marc.roux@test.fr",
            gender="M",
        )
        enrollment = AnnualEnrollment.objects.create(
            student=student,
            academic_year=year,
            level=level,
            department=dept,
            parcours=parc,
            is_alternant=False,
        )
        assignment = Assignment.objects.create(academic_year=year, status="published")
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            agreement_year=ay,
            slot_type=SlotType.DEPT,
        )

        response = client.get(f"/stats/?academic_year_id={year.id}")

        dd = response.json()["dd_outgoing"]
        canada = next(r for r in dd if r["region"] == "Canada / États-Unis")
        assert canada["hommes"] == 1
        assert canada["femmes"] == 0
        assert canada["total"] == 1

    def test_dd_incoming_counts_incoming_students_with_dd_category(
        self, client, academic_year, db
    ):
        from app.incoming.models import IncomingStudent
        from app.mobility.models import MobilityCategory
        from app.reference.models import Country, CTIRegion

        cat_dd = MobilityCategory.objects.create(name="DD_inc")
        country_sn = Country.objects.create(
            iso2="SN",
            name_fr="Sénégal",
            name_en="Senegal",
            cti_region=CTIRegion.AFRIQUE,
        )
        IncomingStudent.objects.create(
            first_name="Fatou",
            last_name="Diallo",
            civility="Mme",
            personal_email="fatou@ext.test",
            academic_year=academic_year,
            country=country_sn,
            duration="2 semestres",
            mobility_category=cat_dd,
        )

        response = client.get(f"/stats/?academic_year_id={academic_year.id}")

        dd = response.json()["dd_incoming"]
        afrique = next(r for r in dd if r["region"] == "Pays d'Afrique")
        assert afrique["femmes"] == 1
        assert afrique["total"] == 1


@pytest.mark.django_db
class TestExportCtiReport:
    def test_returns_404_for_unknown_year(self, client, db):
        response = client.get("/export/?academic_year_id=99999")

        assert response.status_code == 404

    def test_returns_xlsx_for_empty_year(self, client, academic_year):
        response = client.get(f"/export/?academic_year_id={academic_year.id}")

        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_content_disposition_contains_year_label(self, client, academic_year):
        response = client.get(f"/export/?academic_year_id={academic_year.id}")

        assert response.status_code == 200
        cd = response.headers.get("content-disposition", "")
        assert "rapport_cti_2024-2025.xlsx" in cd

    def test_response_body_is_valid_xlsx(self, client, academic_year):
        from io import BytesIO

        import openpyxl

        response = client.get(f"/export/?academic_year_id={academic_year.id}")

        assert response.status_code == 200
        wb = openpyxl.load_workbook(BytesIO(response.content))
        assert wb.sheetnames == ["VII.D3 CTI"]

    def test_export_with_internship_data(self, client, academic_year, db):
        from app.internships.models import Internship
        from app.reference.models import Country, CTIRegion
        from app.students.models import Student

        country = Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        student = Student.objects.create(
            ine="EXPTEST01B",
            first_name="Ana",
            last_name="Müller",
            email="a.muller@example.com",
            gender="F",
        )
        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Siemens AG",
            country=country,
            weeks_in_company=24,
        )

        response = client.get(f"/export/?academic_year_id={academic_year.id}")

        assert response.status_code == 200
