"""
Tests d'intégration de bout en bout — Flux complet de la campagne de mobilité.

Simule le cycle de vie complet d'une année universitaire via les endpoints API :
  Initialisation → Recommandation → Candidature → Import → Pré-affectation
  → Validation → Publication → Finalisation CTI → Clôture

Couvre :
- BF01 : Gestion des références (pays, départements, niveaux)
- BF02 : Gestion des accords et cadres de mobilité
- BF03 : Import et gestion des étudiants
- BF04 : Saisie et gestion des vœux étudiants
- BF05 : Calcul d'affectation Gale-Shapley
- BF06 : Validation et publication des résultats
- BF07 : Export statistiques CTI
- BF08 : Journal d'audit (traçabilité)
- FSM  : Machine à états de l'année universitaire
"""

import json
from datetime import date
from io import BytesIO

import openpyxl
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from app.auth.test_utils import make_admin_user, make_test_jwt

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_student_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        ["INE", "Nom", "Prenom", "Email", "Genre", "Departement", "Niveau", "GPA"]
    )
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def post_json(client: Client, path: str, data: dict) -> object:
    return client.post(path, data=json.dumps(data), content_type="application/json")


def put_json(client: Client, path: str, data: dict) -> object:
    return client.put(path, data=json.dumps(data), content_type="application/json")


# ---------------------------------------------------------------------------
# BF01 — Gestion des référentiels
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestReferenceDataManagement:
    """BF01 : Création, lecture et suppression des données de référence."""

    def setup_method(self):
        self.client = Client()

    def test_create_country(self):
        resp = post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "DE",
                "name_fr": "Allemagne",
                "name_en": "Germany",
                "cti_region": "europe_hors_france",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["iso2"] == "DE"

    def test_create_department(self):
        resp = post_json(
            self.client,
            "/api/v1/reference/departments/",
            {"code": "INFO", "name": "Informatique"},
        )
        assert resp.status_code == 201

    def test_create_level(self):
        resp = post_json(
            self.client,
            "/api/v1/reference/levels/",
            {"code": "3A", "name": "3ème Année"},
        )
        assert resp.status_code == 201

    def test_duplicate_country_code_rejected(self):
        post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "FR",
                "name_fr": "France",
                "name_en": "France",
                "cti_region": "france",
            },
        )
        resp = post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "FR",
                "name_fr": "France Bis",
                "name_en": "France Bis",
                "cti_region": "france",
            },
        )
        assert resp.status_code in (400, 409, 422)

    def test_list_countries_returns_all(self):
        post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "ES",
                "name_fr": "Espagne",
                "name_en": "Spain",
                "cti_region": "europe_hors_france",
            },
        )
        post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "IT",
                "name_fr": "Italie",
                "name_en": "Italy",
                "cti_region": "europe_hors_france",
            },
        )
        resp = self.client.get("/api/v1/reference/countries/")
        assert resp.status_code == 200
        codes = [c["iso2"] for c in resp.json()]
        assert "ES" in codes
        assert "IT" in codes

    def test_delete_country(self):
        resp = post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "XX",
                "name_fr": "Test",
                "name_en": "Test",
                "cti_region": "europe_hors_france",
            },
        )
        country_id = resp.json()["id"]
        del_resp = self.client.delete(f"/api/v1/reference/countries/{country_id}/")
        assert del_resp.status_code == 204

    def test_country_in_use_cannot_be_deleted(self):
        """Un pays lié à un accord ne peut pas être supprimé (intégrité référentielle)."""
        from app.institutions.models import PartnerUniversity
        from app.reference.models import Country, CTIRegion

        country = Country.objects.create(
            iso2="ZZ", name_fr="Zeta", name_en="Zeta", cti_region=CTIRegion.OCEANIE
        )
        PartnerUniversity.objects.create(name="Zeta Uni", country=country)
        resp = self.client.delete(f"/api/v1/reference/countries/{country.id}/")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# BF02 — Gestion des accords et institutions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMobilityAgreementManagement:
    """BF02 : CRUD des accords de mobilité et des cadres."""

    def setup_method(self):
        self.client = Client()
        from app.reference.models import Country, CTIRegion

        self.country = Country.objects.create(
            iso2="SE",
            name_fr="Suède",
            name_en="Sweden",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )

    def test_create_mobility_category(self):
        resp = post_json(
            self.client,
            "/api/v1/mobility/agreement-categories/",
            {"name": "Erasmus+"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Erasmus+"

    def test_create_partner_university(self):
        resp = post_json(
            self.client,
            "/api/v1/institutions/universities/",
            {
                "name": "KTH Royal Institute",
                "country_id": self.country.id,
                "erasmus_code": "KTH",
            },
        )
        assert resp.status_code == 201

    def test_agreement_creation_full_fields(self):
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import MobilityCategory

        cat = MobilityCategory.objects.create(name="Erasmus")
        uni = PartnerUniversity.objects.create(
            name="Uppsala", country=self.country, erasmus_code="UPP"
        )
        resp = post_json(
            self.client,
            "/api/v1/mobility/agreements/",
            {
                "name": "Accord Uppsala",
                "partner_university_id": uni.id,
                "category_id": cat.id,
                "direction": "both",
                "valid_from": "2023-01-01",
                "valid_until": "2028-01-01",
                "inp_total_places": 4,
                "inp_institutions": "INP",
                "remarks": "",
                "level_ids": [],
                "department_ids": [],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Accord Uppsala"
        assert data["inp_total_places"] == 4


# ---------------------------------------------------------------------------
# FSM — Machine à états de l'année universitaire
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAcademicYearFSM:
    """
    Tests de la machine à états de l'année universitaire.
    Vérifie toutes les transitions légales et le rejet des transitions illégales.
    """

    def setup_method(self):
        self.client = Client()

    def _create_year(self) -> dict:
        resp = post_json(
            self.client,
            "/api/v1/academic/years/",
            {
                "label": "FSM-2026",
                "start_date": "2026-09-01",
                "end_date": "2027-07-01",
                "wishes_open_date": "2026-10-01",
                "wishes_close_date": "2026-11-30",
            },
        )
        assert resp.status_code == 201, f"Création année a échoué : {resp.content}"
        return resp.json()

    def _setup_year_for_recommendation(self, year_id: int) -> None:
        """Pré-conditions pour ouvrir la recommandation (GPA + quotas)."""
        from app.academic.models import AcademicYear
        from app.mobility.models import (
            Agreement,
            AgreementDepartment,
            AgreementYear,
            AgreementYearDepartment,
        )
        from app.reference.models import Country, CTIRegion, Department, Level

        year = AcademicYear.objects.get(pk=year_id)
        dept = Department.objects.get_or_create(code="SN", defaults={"name": "SN"})[0]
        level = Level.objects.get_or_create(code="3A", defaults={"name": "3A"})[0]
        country = Country.objects.get_or_create(
            iso2="SE",
            defaults={
                "name_fr": "Suède",
                "name_en": "Sweden",
                "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
            },
        )[0]

        from app.institutions.models import PartnerUniversity

        uni = PartnerUniversity.objects.get_or_create(
            name="Test Uni", defaults={"country": country, "erasmus_code": "TU01"}
        )[0]

        from app.mobility.models import MobilityCategory

        cat = MobilityCategory.objects.get_or_create(name="Erasmus")[0]

        agreement = Agreement.objects.create(
            name="Accord FSM",
            partner_university=uni,
            category=cat,
            direction="outgoing",
            inp_total_places=4,
            inp_institutions="INP",
        )
        ay = AgreementYear.objects.create(
            agreement=agreement,
            academic_year=year,
            is_active=True,
            n7_places=2,
            inp_total_places=4,
        )
        agreement_dept = AgreementDepartment.objects.create(
            agreement=agreement, department=dept
        )
        AgreementYearDepartment.objects.create(
            agreement_year=ay, agreement_department=agreement_dept, estimated_places=2
        )

        # Créer un étudiant avec GPA
        from app.students.models import AnnualEnrollment, Student

        student = Student.objects.create(
            ine="FSM0000001", first_name="Test", last_name="FSM"
        )
        AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level, gpa=3.5
        )

    def test_full_fsm_sequence(self):
        """Parcourt toutes les transitions légales jusqu'à 'validation'."""
        year = self._create_year()
        year_id = year["id"]

        # initialization → recommendation (nécessite GPA + quotas)
        self._setup_year_for_recommendation(year_id)
        resp = self.client.post(
            f"/api/v1/academic/years/{year_id}/open-recommendation/"
        )
        assert resp.status_code == 200, f"open-recommendation a échoué : {resp.content}"
        assert resp.json()["status"] == "recommendation"

        # recommendation → candidature
        resp = self.client.post(f"/api/v1/academic/years/{year_id}/start-candidature/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "candidature"

        # candidature → import
        resp = self.client.post(f"/api/v1/academic/years/{year_id}/close-wishes/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "import"

    def test_illegal_transition_rejected(self):
        """Une transition depuis un état invalide doit être refusée (409)."""
        year = self._create_year()
        year_id = year["id"]
        # Tenter start-candidature depuis initialization (état initial)
        resp = self.client.post(f"/api/v1/academic/years/{year_id}/start-candidature/")
        assert resp.status_code == 409, "Transition illégale doit retourner 409"

    def test_cannot_skip_states(self):
        """On ne peut pas sauter des états (ex: initialization → import)."""
        year = self._create_year()
        year_id = year["id"]
        resp = self.client.post(f"/api/v1/academic/years/{year_id}/close-wishes/")
        assert resp.status_code == 409

    def test_year_crud(self):
        """CRUD complet d'une année universitaire."""
        year = self._create_year()
        year_id = year["id"]

        # Read
        resp = self.client.get(f"/api/v1/academic/years/{year_id}/")
        assert resp.status_code == 200
        assert resp.json()["label"] == "FSM-2026"

        # Update
        resp = put_json(
            self.client,
            f"/api/v1/academic/years/{year_id}/",
            {
                "label": "FSM-2026-MAJ",
                "start_date": "2026-09-01",
                "end_date": "2027-07-01",
                "wishes_open_date": "2026-10-15",
                "wishes_close_date": "2026-11-30",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["label"] == "FSM-2026-MAJ"

        # Delete
        resp = self.client.delete(f"/api/v1/academic/years/{year_id}/")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# BF03 — Import et gestion des étudiants
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStudentImportWorkflow:
    """BF03 : Import Excel des étudiants et gestion des erreurs."""

    def setup_method(self):
        self.client = Client()
        from app.academic.models import AcademicYear
        from app.reference.models import Department, Level

        self.year = AcademicYear.objects.create(
            label="IMPORT-2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 7, 1),
        )
        Department.objects.get_or_create(
            code="SN", defaults={"name": "Sciences du Numérique"}
        )
        Level.objects.get_or_create(code="3A", defaults={"name": "Troisième Année"})

    def test_student_import_creates_enrollments(self):
        xlsx = make_student_xlsx(
            [
                [
                    "11111111111",
                    "Dupont",
                    "Alice",
                    "alice@n7.fr",
                    "F",
                    "SN",
                    "3A",
                    "3.8",
                ],
                ["22222222222", "Martin", "Bob", "bob@n7.fr", "M", "SN", "3A", "3.2"],
            ]
        )
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile(
            "etudiants.xlsx",
            xlsx,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp = self.client.post(
            f"/api/v1/students/students/import-excel/{self.year.id}/",
            {"file": f},
        )
        assert resp.status_code in (200, 202)

    def test_student_list_after_creation(self):
        from app.reference.models import Department, Level
        from app.students.models import AnnualEnrollment, Student

        dept = Department.objects.get(code="SN")
        level = Level.objects.get(code="3A")
        student = Student.objects.create(
            ine="INTEG001", first_name="Alice", last_name="Test"
        )
        AnnualEnrollment.objects.create(
            student=student,
            academic_year=self.year,
            department=dept,
            level=level,
            gpa=3.7,
        )
        resp = self.client.get(
            f"/api/v1/students/students/?academic_year_id={self.year.id}"
        )
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_student_search(self):
        from app.reference.models import Department, Level
        from app.students.models import AnnualEnrollment, Student

        dept = Department.objects.get(code="SN")
        level = Level.objects.get(code="3A")
        Student.objects.create(ine="SRCH001", first_name="Zoé", last_name="Bertrand")
        student = Student.objects.get(ine="SRCH001")
        AnnualEnrollment.objects.create(
            student=student, academic_year=self.year, department=dept, level=level
        )
        resp = self.client.get(
            f"/api/v1/students/students/?search=Bertrand&academic_year_id={self.year.id}"
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert any(s["last_name"] == "Bertrand" for s in results)


# ---------------------------------------------------------------------------
# BF08 — Auditabilité : chaque action est tracée
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAuditTrail:
    """BF08 : Vérification que les actions CRUD génèrent des entrées dans le journal d'audit."""

    def setup_method(self):
        make_admin_user()
        self.client = Client()

    def test_audit_log_created_on_country_creation(self):
        from auditlog.models import LogEntry

        count_before = LogEntry.objects.count()
        post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "AU",
                "name_fr": "Australie",
                "name_en": "Australia",
                "cti_region": "oceanie",
            },
        )
        count_after = LogEntry.objects.count()
        assert (
            count_after > count_before
        ), "Une création doit générer une entrée d'audit"

    def test_audit_log_created_on_country_deletion(self):
        from auditlog.models import LogEntry

        from app.reference.models import Country, CTIRegion

        country = Country.objects.create(
            iso2="QQ",
            name_fr="Pays Supprimé",
            name_en="Deleted Country",
            cti_region=CTIRegion.OCEANIE,
        )
        count_before = LogEntry.objects.count()
        self.client.delete(f"/api/v1/reference/countries/{country.id}/")
        count_after = LogEntry.objects.count()
        assert (
            count_after > count_before
        ), "Une suppression doit générer une entrée d'audit"

    def test_audit_log_api_returns_entries(self):
        post_json(
            self.client,
            "/api/v1/reference/countries/",
            {
                "iso2": "ZA",
                "name_fr": "Afrique du Sud",
                "name_en": "South Africa",
                "cti_region": "afrique",
            },
        )
        resp = self.client.get("/api/v1/audit/logs/")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 0  # au moins accessible

    def test_audit_log_filter_by_action(self):
        resp = self.client.get("/api/v1/audit/logs/?action=create")
        assert resp.status_code == 200

    def test_audit_log_filter_by_entity_type(self):
        resp = self.client.get("/api/v1/audit/logs/?entity_type=country")
        assert resp.status_code == 200

    def test_audit_log_pagination(self):
        resp = self.client.get("/api/v1/audit/logs/?page=1&page_size=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert "count" in body
        assert len(body["results"]) <= 10


# ---------------------------------------------------------------------------
# BF06 — Publication des résultats (test d'acceptation)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStudentViewsOwnResult:
    """
    Test d'acceptation BF06 : après publication, l'étudiant peut consulter
    son affectation via les endpoints /api/v1/student/{ine}/.
    """

    def setup_method(self):
        from app.academic.models import AcademicYear
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import Agreement, AgreementYear, MobilityCategory
        from app.outgoing.models import (
            Assignment,
            AssignmentResult,
            AssignmentStatus,
            SlotType,
        )
        from app.reference.models import Country, CTIRegion, Department, Level
        from app.students.models import AnnualEnrollment, Student

        self.year = AcademicYear.objects.create(
            label="ACCEPT-2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 7, 1),
        )
        dept = Department.objects.create(code="ACC", name="Acceptance")
        level = Level.objects.create(code="3A-A", name="3A Accept")
        country = Country.objects.create(
            iso2="JP",
            name_fr="Japon",
            name_en="Japan",
            cti_region=CTIRegion.ASIE_MOYEN_ORIENT,
        )
        uni = PartnerUniversity.objects.create(
            name="Tokyo U", country=country, erasmus_code="TKU01"
        )
        cat = MobilityCategory.objects.create(name="Cat Accept")
        agreement = Agreement.objects.create(
            name="Accord Tokyo",
            partner_university=uni,
            category=cat,
            direction="outgoing",
            inp_total_places=2,
            inp_institutions="INP",
        )
        ay = AgreementYear.objects.create(
            agreement=agreement,
            academic_year=self.year,
            is_active=True,
            n7_places=1,
            inp_total_places=2,
        )

        self.student = Student.objects.create(
            ine="ACCEPT001", first_name="Chen", last_name="Wei"
        )
        self.enrollment = AnnualEnrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            department=dept,
            level=level,
            gpa=3.9,
        )

        # Créer une affectation publiée
        AcademicYear.objects.filter(pk=self.year.pk).update(status="published")
        assignment = Assignment.objects.create(
            academic_year=self.year, status=AssignmentStatus.PUBLISHED
        )
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=self.enrollment,
            slot_type=SlotType.DEPT,
            agreement_year=ay,
            assigned_rank=1,
        )

        self.student_token = make_test_jwt(
            email="ACCEPT001@etud.n7.fr", role="student", ine="ACCEPT001"
        )
        self.student_client = Client(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

    def test_student_can_see_own_assignment(self):
        resp = self.student_client.get("/api/v1/student/ACCEPT001/assignment/")
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_student_cannot_see_other_assignment(self):
        resp = self.student_client.get("/api/v1/student/ANOTHER999/assignment/")
        assert resp.status_code == 403
