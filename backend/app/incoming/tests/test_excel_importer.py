from __future__ import annotations

from datetime import date, datetime
from io import BytesIO

import openpyxl
import pytest

from app.academic.models import AcademicYear
from app.imports.models import RawImportStatus
from app.incoming.models import IncomingStudent
from app.incoming.services.date_utils import _parse_date
from app.incoming.services.excel_importer import import_incoming_from_excel

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


_HEADER = [
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


def make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(_HEADER)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _empty_row() -> list:
    return [""] * len(_HEADER)


def _student_row(last_name: str, first_name: str, **overrides) -> list:
    row = _empty_row()
    row[_HEADER.index("NOM")] = last_name
    row[_HEADER.index("PRENOM")] = first_name
    for key, value in overrides.items():
        if key in _HEADER:
            row[_HEADER.index(key)] = value
    return row


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExcelImporter:
    def setup_method(self):
        self.year = make_year()

    def test_import_creates_students(self):
        file_bytes = make_xlsx(
            [
                _student_row("Martin", "Jean"),
                _student_row("Dupont", "Marie"),
            ]
        )
        result = import_incoming_from_excel(file_bytes, "test.xlsx", self.year)

        assert result.created == 2
        assert result.failed == 0
        assert IncomingStudent.objects.filter(academic_year=self.year).count() == 2

    def test_import_skips_empty_rows(self):
        file_bytes = make_xlsx(
            [
                _student_row("Martin", "Jean"),
                _empty_row(),
                _empty_row(),
            ]
        )
        result = import_incoming_from_excel(file_bytes, "test.xlsx", self.year)

        assert result.total == 1
        assert result.created == 1

    def test_import_creates_error_on_missing_name(self):
        file_bytes = make_xlsx(
            [
                _student_row("", "Jean"),  # missing last name
                _student_row("Martin", ""),  # missing first name
                _student_row("Dupont", "Marie"),  # valid
            ]
        )
        result = import_incoming_from_excel(file_bytes, "test.xlsx", self.year)

        assert result.failed == 2
        assert result.created == 1

    def test_import_detects_duplicates(self):
        # Pre-create a student so the second import attempt conflicts
        IncomingStudent.objects.create(
            academic_year=self.year,
            last_name="Martin",
            first_name="Jean",
            birth_date=None,
        )
        file_bytes = make_xlsx([_student_row("Martin", "Jean")])
        result = import_incoming_from_excel(file_bytes, "test.xlsx", self.year)

        assert result.duplicates == 1
        assert result.created == 0
        # Verify the raw import record has CONFLICT status
        from app.imports.models import RawImport, RawImportEntity

        raw = RawImport.objects.filter(
            entity=RawImportEntity.INCOMING_STUDENT,
            status=RawImportStatus.CONFLICT,
        ).first()
        assert raw is not None


# ---------------------------------------------------------------------------
# _parse_date unit tests (date_utils)
# ---------------------------------------------------------------------------


class TestParseDateUtils:
    def test_parse_date_from_datetime_object(self):
        dt = datetime(2001, 3, 14, 0, 0, 0)
        result = _parse_date(dt)
        assert result == date(2001, 3, 14)

    def test_parse_date_from_date_object(self):
        d = date(2001, 3, 14)
        result = _parse_date(d)
        assert result == date(2001, 3, 14)

    def test_parse_date_from_string_dmy(self):
        result = _parse_date("14/03/2001")
        assert result == date(2001, 3, 14)

    def test_parse_date_from_string_ymd(self):
        result = _parse_date("2001-03-14")
        assert result == date(2001, 3, 14)

    def test_parse_date_from_string(self):
        result = _parse_date("01/06/2002")
        assert result == date(2002, 6, 1)

    def test_parse_date_returns_none_for_invalid(self):
        assert _parse_date("not-a-date") is None

    def test_parse_date_returns_none_for_none(self):
        assert _parse_date(None) is None

    def test_parse_date_returns_none_for_empty_string(self):
        assert _parse_date("") is None

    def test_parse_date_strips_timezone_suffix(self):
        result = _parse_date("2001-03-14 00:00:00+00:00")
        assert result == date(2001, 3, 14)
