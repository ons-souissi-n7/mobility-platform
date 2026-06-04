"""
Tests unitaires pour les adaptateurs Excel et Pégase.
Aucune base de données n'est nécessaire — ces tests sont purement Python.
"""

import json
from io import BytesIO

import openpyxl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_xlsx(headers: list, rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Excel adapter
# ---------------------------------------------------------------------------


class TestExcelAdapterParse:
    def test_parse_valid_row(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            [
                "INE",
                "Nom",
                "Prenom",
                "Email",
                "Genre",
                "Departement",
                "Niveau",
                "Parcours",
                "GPA",
            ],
            [
                [
                    "12345678901",
                    "Martin",
                    "Jean",
                    "jean@n7.fr",
                    "M",
                    "SN",
                    "3A",
                    "IPA",
                    15.5,
                ]
            ],
        )

        rows = parse(data)

        assert len(rows) == 1
        assert rows[0].ine == "12345678901"
        assert rows[0].last_name == "Martin"
        assert rows[0].first_name == "Jean"
        assert rows[0].email == "jean@n7.fr"
        assert rows[0].gender == "M"
        assert rows[0].department_code == "SN"
        assert rows[0].level_code == "3A"
        assert rows[0].parcours_code == "IPA"
        assert rows[0].gpa == 15.5

    def test_parse_skips_rows_without_ine(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Departement", "Niveau"],
            [
                ["12345678901", "Martin", "Jean", "SN", "3A"],
                [None, "Vide", "Sans", "SN", "3A"],
                ["", "Vide2", "Sans2", "SN", "3A"],
            ],
        )

        rows = parse(data)

        assert len(rows) == 1
        assert rows[0].ine == "12345678901"

    def test_parse_empty_file_returns_empty_list(self):
        from app.students.services.adapters.excel import parse

        wb = openpyxl.Workbook()
        buf = BytesIO()
        wb.save(buf)

        rows = parse(buf.getvalue())

        assert rows == []

    def test_parse_gender_homme_normalizes_to_m(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Genre", "Departement", "Niveau"],
            [["12345678901", "M", "J", "homme", "SN", "3A"]],
        )

        rows = parse(data)

        assert rows[0].gender == "M"

    def test_parse_gender_femme_normalizes_to_f(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Genre", "Departement", "Niveau"],
            [["12345678901", "D", "M", "Femme", "SN", "3A"]],
        )

        rows = parse(data)

        assert rows[0].gender == "F"

    def test_parse_gender_masculin_normalizes_to_m(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Genre", "Departement", "Niveau"],
            [["12345678901", "D", "M", "masculin", "SN", "3A"]],
        )

        rows = parse(data)

        assert rows[0].gender == "M"

    def test_parse_unknown_gender_returns_empty_string(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Genre", "Departement", "Niveau"],
            [["12345678901", "D", "M", "inconnu", "SN", "3A"]],
        )

        rows = parse(data)

        assert rows[0].gender == ""

    def test_parse_column_names_case_insensitive(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "NOM", "PRÉNOM", "EMAIL", "GENRE", "DÉPARTEMENT", "NIVEAU"],
            [["12345678901", "Martin", "Jean", "j@n7.fr", "F", "SN", "3A"]],
        )

        rows = parse(data)

        assert len(rows) == 1
        assert rows[0].department_code == "SN"
        assert rows[0].gender == "F"

    def test_parse_moyenne_column_accepted_as_gpa(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Departement", "Niveau", "Moyenne"],
            [["12345678901", "M", "J", "SN", "3A", 14.75]],
        )

        rows = parse(data)

        assert rows[0].gpa == 14.75

    def test_parse_note_column_accepted_as_gpa(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Departement", "Niveau", "Note"],
            [["12345678901", "M", "J", "SN", "3A", 13.0]],
        )

        rows = parse(data)

        assert rows[0].gpa == 13.0

    def test_parse_parcours_none_when_cell_empty(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Departement", "Niveau", "Parcours"],
            [["12345678901", "M", "J", "SN", "3A", None]],
        )

        rows = parse(data)

        assert rows[0].parcours_code is None

    def test_parse_multiple_rows(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Departement", "Niveau"],
            [
                ["10000000001", "A", "B", "SN", "3A"],
                ["10000000002", "C", "D", "TC", "4A"],
            ],
        )

        rows = parse(data)

        assert len(rows) == 2
        assert rows[0].ine == "10000000001"
        assert rows[1].ine == "10000000002"

    def test_parse_courriel_column_accepted_as_email(self):
        from app.students.services.adapters.excel import parse

        data = make_xlsx(
            ["INE", "Nom", "Prenom", "Courriel", "Departement", "Niveau"],
            [["12345678901", "M", "J", "test@n7.fr", "SN", "3A"]],
        )

        rows = parse(data)

        assert rows[0].email == "test@n7.fr"


# ---------------------------------------------------------------------------
# Pégase adapter
# ---------------------------------------------------------------------------


class TestPegaseAdapterFetch:
    def test_load_valid_fixture(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "12345678901",
                "prenom": "Jean",
                "nom": "Martin",
                "email": "jean@n7.fr",
                "sexe": "h",
                "departement": "SN",
                "niveau": "3A",
                "gpa": 15.5,
            }
        ]
        fixture_file = tmp_path / "pegase_students.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert len(rows) == 1
        assert rows[0].ine == "12345678901"
        assert rows[0].first_name == "Jean"
        assert rows[0].last_name == "Martin"
        assert rows[0].email == "jean@n7.fr"
        assert rows[0].department_code == "SN"
        assert rows[0].level_code == "3A"
        assert rows[0].gpa == 15.5

    def test_returns_empty_when_fixture_missing(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", tmp_path / "nonexistent.json")

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows == []

    def test_returns_empty_on_invalid_json(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", bad_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows == []

    def test_skips_items_without_ine(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {"ine": "", "prenom": "A", "nom": "B", "departement": "SN", "niveau": "3A"},
            {"prenom": "C", "nom": "D", "departement": "SN", "niveau": "3A"},
        ]
        fixture_file = tmp_path / "pegase_students.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows == []

    def test_gender_sexe_h_maps_to_m(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
                "sexe": "h",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].gender == "M"

    def test_gender_femme_maps_to_f(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
                "sexe": "femme",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].gender == "F"

    def test_gender_masculin_maps_to_m(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000002",
                "prenom": "C",
                "nom": "D",
                "departement": "SN",
                "niveau": "3A",
                "sexe": "masculin",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].gender == "M"

    def test_genre_field_used_as_fallback(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
                "genre": "f",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].gender == "F"

    def test_parcours_field_parsed(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
                "parcours": "IPA",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].parcours_code == "IPA"

    def test_gpa_none_when_absent(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
            }
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert rows[0].gpa is None

    def test_skips_non_dict_items(self, tmp_path, monkeypatch):
        from app.students.services.adapters import pegase as pegase_mod

        fixture = [
            {
                "ine": "00000000001",
                "prenom": "A",
                "nom": "B",
                "departement": "SN",
                "niveau": "3A",
            },
            "not a dict",
            42,
        ]
        fixture_file = tmp_path / "p.json"
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        monkeypatch.setattr(pegase_mod, "_FIXTURE_PATH", fixture_file)

        rows = pegase_mod.fetch_enrollments("2026-2027")

        assert len(rows) == 1
