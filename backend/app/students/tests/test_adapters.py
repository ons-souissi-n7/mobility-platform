"""
Tests unitaires pour les adaptateurs Excel et Pégase.
Aucune base de données n'est nécessaire — ces tests sont purement Python.
"""

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


class TestPegaseParseRows:
    """Tests unitaires de _parse_rows — la fonction pure de parsing Pégase.

    Ces tests passent directement des dicts en entrée, sans appel réseau
    ni fichier temporaire. Ils reflètent le vrai format de l'export Pégase.
    """

    def _parse(self, data):
        from app.students.services.adapters.pegase import _parse_rows

        return _parse_rows(data)

    def test_parses_valid_row(self):
        rows = self._parse(
            [
                {
                    "ine": "12345678901",
                    "prenom": "Jean",
                    "nom": "Martin",
                    "email": "jean@n7.fr",
                    "sexe": "h",
                    "departement": "SN",
                    "niveau": "3A",
                    "moyenne": 15.5,
                }
            ]
        )
        assert len(rows) == 1
        assert rows[0].ine == "12345678901"
        assert rows[0].first_name == "Jean"
        assert rows[0].last_name == "Martin"
        assert rows[0].email == "jean@n7.fr"
        assert rows[0].department_code == "SN"
        assert rows[0].level_code == "3A"
        assert rows[0].gpa == 15.5

    def test_skips_items_without_ine(self):
        rows = self._parse(
            [
                {
                    "ine": "",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                },
                {"prenom": "C", "nom": "D", "departement": "SN", "niveau": "3A"},
            ]
        )
        assert rows == []

    def test_gender_sexe_h_maps_to_m(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "sexe": "h",
                }
            ]
        )
        assert rows[0].gender == "M"

    def test_gender_femme_maps_to_f(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "sexe": "femme",
                }
            ]
        )
        assert rows[0].gender == "F"

    def test_gender_masculin_maps_to_m(self):
        rows = self._parse(
            [
                {
                    "ine": "002",
                    "prenom": "C",
                    "nom": "D",
                    "departement": "SN",
                    "niveau": "3A",
                    "sexe": "masculin",
                }
            ]
        )
        assert rows[0].gender == "M"

    def test_genre_field_used_as_fallback(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "genre": "f",
                }
            ]
        )
        assert rows[0].gender == "F"

    def test_parcours_field_parsed(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "parcours": "IPA",
                }
            ]
        )
        assert rows[0].parcours_code == "IPA"

    def test_gpa_none_when_absent(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                }
            ]
        )
        assert rows[0].gpa is None

    def test_moyenne_field_used_as_gpa(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "moyenne": 14.2,
                }
            ]
        )
        assert rows[0].gpa == 14.2

    def test_nationality_french_name(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "nationalite": "France",
                }
            ]
        )
        assert rows[0].nationality_iso2 == "France"

    def test_nationality_iso2(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "nationalite": "FR",
                }
            ]
        )
        assert rows[0].nationality_iso2 == "FR"

    def test_skips_non_dict_items(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                },
                "not a dict",
                42,
            ]
        )
        assert len(rows) == 1

    def test_source_id_defaults_to_ine(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                }
            ]
        )
        assert rows[0].source_id == "001"

    def test_source_id_uses_pegase_id_when_present(self):
        rows = self._parse(
            [
                {
                    "ine": "001",
                    "prenom": "A",
                    "nom": "B",
                    "departement": "SN",
                    "niveau": "3A",
                    "pegase_id": "PEG-999",
                }
            ]
        )
        assert rows[0].source_id == "PEG-999"
