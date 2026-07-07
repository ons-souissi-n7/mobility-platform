from datetime import date
from unittest.mock import patch

import pytest
from django.test import Client

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)


def make_year(**kwargs) -> AcademicYear:
    defaults = {
        "label": "2026-2027",
        "start_date": date(2026, 9, 1),
        "end_date": date(2027, 8, 31),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


@pytest.mark.django_db
class TestListImportReports:
    def setup_method(self):
        self.client = Client()

    def test_list_reports_ordered_by_most_recent(self):
        year = make_year()
        r1 = ImportReport.objects.create(source=ImportSource.PEGASE, academic_year=year)
        r2 = ImportReport.objects.create(
            source=ImportSource.EUDONET, academic_year=year
        )

        response = self.client.get("/api/v1/imports/")

        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert ids == [r2.id, r1.id]

    def test_filter_by_source(self):
        year = make_year()
        ImportReport.objects.create(source=ImportSource.PEGASE, academic_year=year)
        report = ImportReport.objects.create(
            source=ImportSource.EUDONET, academic_year=year
        )

        response = self.client.get("/api/v1/imports/?source=eudonet")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == report.id

    def test_filter_by_academic_year(self):
        year1 = make_year()
        year2 = make_year(
            label="2027-2028", start_date=date(2027, 9, 1), end_date=date(2028, 8, 31)
        )
        ImportReport.objects.create(source=ImportSource.PEGASE, academic_year=year1)
        report2 = ImportReport.objects.create(
            source=ImportSource.PEGASE, academic_year=year2
        )

        response = self.client.get(f"/api/v1/imports/?academic_year_id={year2.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == report2.id


@pytest.mark.django_db
class TestLatestImportReports:
    def setup_method(self):
        self.client = Client()

    def test_returns_one_per_source(self):
        year = make_year()
        ImportReport.objects.create(source=ImportSource.PEGASE, academic_year=year)
        latest_pegase = ImportReport.objects.create(
            source=ImportSource.PEGASE, academic_year=year
        )
        latest_eudonet = ImportReport.objects.create(
            source=ImportSource.EUDONET, academic_year=year
        )

        response = self.client.get("/api/v1/imports/latest/")

        assert response.status_code == 200
        data = response.json()
        ids = {item["id"] for item in data}
        assert ids == {latest_pegase.id, latest_eudonet.id}


@pytest.mark.django_db
class TestGetImportReport:
    def setup_method(self):
        self.client = Client()

    def test_get_report_with_errors(self):
        year = make_year()
        report = ImportReport.objects.create(
            source=ImportSource.PEGASE, academic_year=year
        )
        report.record_error("INE123", "INE introuvable")
        report.finalize()

        response = self.client.get(f"/api/v1/imports/{report.id}/")

        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] == 1
        assert data["errors"][0]["external_id"] == "INE123"
        assert data["academic_year_label"] == year.label

    def test_returns_404_for_unknown_report(self):
        response = self.client.get("/api/v1/imports/99999/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestForceOverwriteConflict:
    def setup_method(self):
        self.client = Client()

    def make_conflict(self, entity: str, payload: dict | None = None) -> RawImport:
        return RawImport.objects.create(
            source="test",
            entity=entity,
            external_id="ext-1",
            payload=payload or {},
            status=RawImportStatus.CONFLICT,
        )

    def test_returns_404_for_unknown_raw_import(self):
        response = self.client.post("/api/v1/imports/raw/99999/force-overwrite/")
        assert response.status_code == 404

    def test_returns_404_when_status_is_not_conflict(self):
        raw = RawImport.objects.create(
            source="test",
            entity=RawImportEntity.AGREEMENT,
            external_id="ext-1",
            payload={},
            status=RawImportStatus.FAILED,
        )
        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")
        assert response.status_code == 404

    @patch("app.mobility.services.sync_moveon.upsert_agreement")
    def test_force_overwrite_agreement(self, mock_upsert):
        raw = self.make_conflict(RawImportEntity.AGREEMENT)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 200
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED

    @patch("app.mobility.services.sync_moveon.upsert_mobility_category")
    def test_force_overwrite_agreement_category(self, mock_upsert):
        raw = self.make_conflict(RawImportEntity.AGREEMENT_CATEGORY)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 200
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)

    @patch("app.reference.services.sync_pegase.upsert_department")
    def test_force_overwrite_department(self, mock_upsert):
        raw = self.make_conflict(RawImportEntity.DEPARTMENT)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 200
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)

    @patch("app.reference.services.sync_pegase_levels.upsert_level")
    def test_force_overwrite_level(self, mock_upsert):
        raw = self.make_conflict(RawImportEntity.LEVEL)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 200
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)

    @patch("app.institutions.services.sync_moveon.upsert_partner_university")
    def test_force_overwrite_partner_university(self, mock_upsert):
        raw = self.make_conflict(RawImportEntity.PARTNER_UNIVERSITY)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 200
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)

    def test_force_overwrite_unsupported_entity_returns_400(self):
        raw = self.make_conflict(RawImportEntity.STUDENT)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 400
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.CONFLICT

    @patch("app.mobility.services.sync_moveon.upsert_agreement")
    def test_force_overwrite_propagates_upsert_error_as_400(self, mock_upsert):
        mock_upsert.side_effect = ValueError("Données invalides")
        raw = self.make_conflict(RawImportEntity.AGREEMENT)

        response = self.client.post(f"/api/v1/imports/raw/{raw.id}/force-overwrite/")

        assert response.status_code == 400
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.CONFLICT
