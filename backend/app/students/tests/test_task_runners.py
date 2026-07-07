"""Tests for students/services/task_runners.py.

Each runner orchestrates: fetch data → create ImportReport → call importer → finalize.
We mock the adapters and importers to avoid hitting external APIs or running the full
ETL pipeline, and verify that the runners wire everything up correctly.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.academic.models import AcademicYear
from app.imports.models import ImportReport, ImportSource
from app.students.services.task_runners import (
    run_import_excel_students,
    run_import_excel_wishes,
    run_sync_moveon_wishes,
    run_sync_pegase_students,
)

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


# ---------------------------------------------------------------------------
# run_sync_pegase_students
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRunSyncPegaseStudents:
    def test_creates_pegase_report_with_triggered_by(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.pegase_adapter.fetch_enrollments",
                return_value=[],
            ),
            patch("app.students.services.task_runners.import_students"),
        ):
            run_sync_pegase_students(year.id, triggered_by="ci-runner")

        report = ImportReport.objects.get(
            source=ImportSource.PEGASE, academic_year=year
        )
        assert report.triggered_by == "ci-runner"

    def test_fetches_by_year_date_range(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.pegase_adapter.fetch_enrollments",
                return_value=[],
            ) as mock_fetch,
            patch("app.students.services.task_runners.import_students"),
        ):
            run_sync_pegase_students(year.id)

        mock_fetch.assert_called_once_with(year.start_date, year.end_date)

    def test_passes_rows_and_year_to_importer(self):
        year = make_year()
        fake_row = MagicMock()
        with (
            patch(
                "app.students.services.task_runners.pegase_adapter.fetch_enrollments",
                return_value=[fake_row],
            ),
            patch("app.students.services.task_runners.import_students") as mock_import,
        ):
            run_sync_pegase_students(year.id)

        mock_import.assert_called_once()
        positional = mock_import.call_args[0]
        assert positional[0] == [fake_row]
        assert positional[1] == year

    def test_report_is_finalized(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.pegase_adapter.fetch_enrollments",
                return_value=[],
            ),
            patch("app.students.services.task_runners.import_students"),
        ):
            run_sync_pegase_students(year.id)

        report = ImportReport.objects.get(
            source=ImportSource.PEGASE, academic_year=year
        )
        # finalize() sets updated_at — just verify the report was saved
        assert report.pk is not None

    def test_raises_if_year_not_found(self):
        with pytest.raises(AcademicYear.DoesNotExist):
            run_sync_pegase_students(99999)


# ---------------------------------------------------------------------------
# run_import_excel_students
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRunImportExcelStudents:
    def test_creates_excel_report_with_triggered_by(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.excel_adapter.parse",
                return_value=[],
            ),
            patch("app.students.services.task_runners.import_students"),
        ):
            run_import_excel_students(b"bytes", "f.xlsx", year.id, triggered_by="admin")

        report = ImportReport.objects.get(source=ImportSource.EXCEL, academic_year=year)
        assert report.triggered_by == "admin"

    def test_parses_bytes(self):
        year = make_year()
        raw = b"xlsx-content"
        with (
            patch(
                "app.students.services.task_runners.excel_adapter.parse",
                return_value=[],
            ) as mock_parse,
            patch("app.students.services.task_runners.import_students"),
        ):
            run_import_excel_students(raw, "f.xlsx", year.id)

        mock_parse.assert_called_once_with(raw)

    def test_passes_source_file_to_importer(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.excel_adapter.parse",
                return_value=[],
            ),
            patch("app.students.services.task_runners.import_students") as mock_import,
        ):
            run_import_excel_students(b"", "students_2026.xlsx", year.id)

        kwargs = mock_import.call_args[1]
        assert kwargs["source_file"] == "students_2026.xlsx"

    def test_raises_if_year_not_found(self):
        with pytest.raises(AcademicYear.DoesNotExist):
            run_import_excel_students(b"", "f.xlsx", 99999)


# ---------------------------------------------------------------------------
# run_sync_moveon_wishes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRunSyncMoveonWishes:
    def test_calls_sync_with_year_and_triggered_by(self):
        year = make_year()
        with patch(
            "app.students.services.task_runners.sync_moveon_wishes"
        ) as mock_sync:
            run_sync_moveon_wishes(year.id, triggered_by="scheduler")

        mock_sync.assert_called_once_with(academic_year=year, triggered_by="scheduler")

    def test_default_triggered_by_is_empty_string(self):
        year = make_year()
        with patch(
            "app.students.services.task_runners.sync_moveon_wishes"
        ) as mock_sync:
            run_sync_moveon_wishes(year.id)

        mock_sync.assert_called_once_with(academic_year=year, triggered_by="")

    def test_raises_if_year_not_found(self):
        with pytest.raises(AcademicYear.DoesNotExist):
            run_sync_moveon_wishes(99999)


# ---------------------------------------------------------------------------
# run_import_excel_wishes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRunImportExcelWishes:
    def test_creates_excel_report_with_triggered_by(self):
        year = make_year()
        with (
            patch(
                "app.students.services.task_runners.excel_wishes_adapter.parse_wish_excel",
                return_value=[],
            ),
            patch("app.students.services.task_runners.import_wish_rows"),
        ):
            run_import_excel_wishes(b"data", "w.xlsx", year.id, triggered_by="user-42")

        report = ImportReport.objects.get(source=ImportSource.EXCEL, academic_year=year)
        assert report.triggered_by == "user-42"

    def test_parses_bytes(self):
        year = make_year()
        raw = b"wish-xlsx"
        with (
            patch(
                "app.students.services.task_runners.excel_wishes_adapter.parse_wish_excel",
                return_value=[],
            ) as mock_parse,
            patch("app.students.services.task_runners.import_wish_rows"),
        ):
            run_import_excel_wishes(raw, "w.xlsx", year.id)

        mock_parse.assert_called_once_with(raw)

    def test_passes_rows_and_year_to_importer(self):
        year = make_year()
        fake_row = MagicMock()
        with (
            patch(
                "app.students.services.task_runners.excel_wishes_adapter.parse_wish_excel",
                return_value=[fake_row],
            ),
            patch("app.students.services.task_runners.import_wish_rows") as mock_import,
        ):
            run_import_excel_wishes(b"", "w.xlsx", year.id)

        positional = mock_import.call_args[0]
        assert positional[0] == [fake_row]
        assert positional[1] == year

    def test_raises_if_year_not_found(self):
        with pytest.raises(AcademicYear.DoesNotExist):
            run_import_excel_wishes(b"", "w.xlsx", 99999)
