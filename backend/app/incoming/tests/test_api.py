from __future__ import annotations

import json
from datetime import date
from io import BytesIO

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from app.academic.models import AcademicYear
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.incoming.models import IncomingStudent
from app.reference.models import Country, CTIRegion, Department

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_year(**kwargs) -> AcademicYear:
    defaults = {
        "label": "2026-2027",
        "start_date": date(2026, 9, 1),
        "end_date": date(2027, 8, 31),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


def make_xlsx_incoming(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "DEPARTEMENT",
            "CIVILITE",
            "NOM",
            "PRENOM",
            "PAYS",
            "UNIV ORIGINE",
            "DATE NAISSANCE",
            "CADRE",
            "MAIL",
            "MAIL ENSEEIHT",
            "DUREE",
            "ANNEE",
            "PARCOURS",
            "REMARQUES",
            "STAGE",
            "DIPLOME",
            "POURSUITE DOCTORAT",
        ]
    )
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def xlsx_file(rows: list[list], name: str = "entrants.xlsx") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        make_xlsx_incoming(rows),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ---------------------------------------------------------------------------
# GET /api/v1/incoming/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListIncomingStudents:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        self.country = Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )

    def test_list_empty(self):
        response = self.client.get("/api/v1/incoming/")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 0
        assert body["results"] == []

    def test_list_returns_students(self):
        IncomingStudent.objects.create(
            academic_year=self.year,
            last_name="Muller",
            first_name="Hans",
            country=self.country,
        )
        response = self.client.get("/api/v1/incoming/")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["last_name"] == "Muller"

    def test_filter_by_year(self):
        year2 = make_year(
            label="2027-2028",
            start_date=date(2027, 9, 1),
            end_date=date(2028, 8, 31),
        )
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="A", first_name="A"
        )
        IncomingStudent.objects.create(
            academic_year=year2, last_name="B", first_name="B"
        )

        response = self.client.get(f"/api/v1/incoming/?year_id={self.year.id}")
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["last_name"] == "A"

    def test_filter_by_department(self):
        dept2 = Department.objects.create(code="TC", name="Tronc Commun")
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="A", first_name="A", department=self.dept
        )
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="B", first_name="B", department=dept2
        )

        response = self.client.get(f"/api/v1/incoming/?department_id={self.dept.id}")
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["last_name"] == "A"

    def test_filter_by_country(self):
        country2 = Country.objects.create(
            iso2="FR",
            name_fr="France",
            name_en="France",
            cti_region=CTIRegion.FRANCE,
        )
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="A", first_name="A", country=self.country
        )
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="B", first_name="B", country=country2
        )

        response = self.client.get(f"/api/v1/incoming/?country_id={self.country.id}")
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["last_name"] == "A"

    def test_search_by_last_name(self):
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="Muller", first_name="Hans"
        )
        IncomingStudent.objects.create(
            academic_year=self.year, last_name="Schmidt", first_name="Anna"
        )

        response = self.client.get("/api/v1/incoming/?search=Muller")
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["last_name"] == "Muller"

    def test_pagination(self):
        for i in range(5):
            IncomingStudent.objects.create(
                academic_year=self.year,
                last_name=f"Student{i:02d}",
                first_name="Test",
            )

        response = self.client.get("/api/v1/incoming/?page=1&page_size=2")
        body = response.json()
        assert body["count"] == 5
        assert len(body["results"]) == 2
        assert body["page"] == 1
        assert body["page_size"] == 2


# ---------------------------------------------------------------------------
# POST /api/v1/incoming/import/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestImportIncomingExcel:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()

    def test_import_returns_202(self, monkeypatch):
        import app.incoming.api as incoming_api

        calls: list = []
        monkeypatch.setattr(
            incoming_api,
            "enqueue_import_excel_incoming",
            lambda year_id, file_bytes, source_file, triggered_by="": (
                calls.append(year_id) or "fake-task-id"
            ),
        )

        response = self.client.post(
            f"/api/v1/incoming/import/?year_id={self.year.id}",
            data={"file": xlsx_file([])},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "fake-task-id"
        assert calls == [self.year.id]

    def test_import_wrong_file_type_returns_400(self):
        csv_file = SimpleUploadedFile(
            "entrants.csv", b"NOM,PRENOM\nMartin,Jean", content_type="text/csv"
        )
        response = self.client.post(
            f"/api/v1/incoming/import/?year_id={self.year.id}",
            data={"file": csv_file},
        )
        assert response.status_code == 400

    def test_import_file_too_large_returns_400(self):
        large_content = b"x" * (6 * 1024 * 1024)  # 6 MB exceeds the 5 MB limit
        large_file = SimpleUploadedFile(
            "entrants.xlsx",
            large_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response = self.client.post(
            f"/api/v1/incoming/import/?year_id={self.year.id}",
            data={"file": large_file},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET/POST /api/v1/incoming/import-errors/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIncomingImportErrors:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()

    def _make_raw(self, **kwargs) -> RawImport:
        defaults = {
            "source": "excel_incoming",
            "entity": RawImportEntity.INCOMING_STUDENT,
            "external_id": "row_2_Martin_Jean",
            "payload": {"NOM": "Martin", "PRENOM": "Jean"},
            "status": RawImportStatus.FAILED,
            "error_message": "Nom ou prenom manquant.",
            "academic_year": self.year,
        }
        defaults.update(kwargs)
        return RawImport.objects.create(**defaults)

    def test_list_import_errors(self):
        self._make_raw()
        response = self.client.get("/api/v1/incoming/import-errors/")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 1
        assert body["results"][0]["external_id"] == "row_2_Martin_Jean"

    def test_list_excludes_non_incoming_entities(self):
        RawImport.objects.create(
            source="pegase",
            entity=RawImportEntity.STUDENT,
            external_id="12345678901",
            payload={"ine": "12345678901"},
            status=RawImportStatus.FAILED,
            error_message="Departement introuvable",
        )
        response = self.client.get("/api/v1/incoming/import-errors/")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_ignore_import_error(self):
        raw = self._make_raw()
        response = self.client.post(f"/api/v1/incoming/import-errors/{raw.id}/ignore/")
        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IGNORED

    def test_ignore_nonexistent_returns_404(self):
        response = self.client.post("/api/v1/incoming/import-errors/99999/ignore/")
        assert response.status_code == 404

    def test_force_import_error_creates_student(self):
        raw = self._make_raw(
            payload={"NOM": "Martin", "PRENOM": "Jean"},
            error_message="Nom ou prenom manquant.",
        )
        response = self.client.post(
            f"/api/v1/incoming/import-errors/{raw.id}/force/",
            data=json.dumps({"payload": {"NOM": "Martin", "PRENOM": "Jean"}}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert IncomingStudent.objects.filter(
            last_name="Martin", first_name="Jean", academic_year=self.year
        ).exists()
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED

    def test_force_import_error_missing_name_returns_400(self):
        raw = self._make_raw(payload={"NOM": "", "PRENOM": ""})
        response = self.client.post(
            f"/api/v1/incoming/import-errors/{raw.id}/force/",
            data=json.dumps({"payload": {"NOM": "", "PRENOM": ""}}),
            content_type="application/json",
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/incoming/stats/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIncomingStats:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()

    def test_stats_by_university(self):
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        IncomingStudent.objects.create(
            academic_year=self.year,
            last_name="A",
            first_name="A",
            origin_university_name="MIT",
            department=dept,
        )
        response = self.client.get("/api/v1/incoming/stats/univ/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["university"] == "MIT"
        assert data[0]["count"] == 1

    def test_stats_by_country(self):
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        country = Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        IncomingStudent.objects.create(
            academic_year=self.year,
            last_name="A",
            first_name="A",
            country=country,
            department=dept,
        )
        response = self.client.get("/api/v1/incoming/stats/country/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["country"] == "Allemagne"
        assert data[0]["count"] == 1
