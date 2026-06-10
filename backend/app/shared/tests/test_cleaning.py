from app.shared.cleaning import (
    deduplicate_by_key,
    normalize_country_code,
    normalize_date,
    normalize_for_comparison,
    normalize_ine,
    normalize_string,
    strip_accents,
)


class TestStripAccents:
    def test_removes_french_accents(self):
        assert strip_accents("éàüîôç") == "eauioc"

    def test_leaves_ascii_unchanged(self):
        assert strip_accents("hello") == "hello"

    def test_empty_string(self):
        assert strip_accents("") == ""


class TestNormalizeString:
    def test_strips_surrounding_whitespace(self):
        assert normalize_string("  hello  ") == "hello"

    def test_collapses_internal_spaces(self):
        assert normalize_string("hello   world") == "hello world"

    def test_none_returns_empty(self):
        assert normalize_string(None) == ""

    def test_empty_returns_empty(self):
        assert normalize_string("") == ""


class TestNormalizeForComparison:
    def test_lowercases(self):
        assert normalize_for_comparison("HELLO") == "hello"

    def test_strips_accents(self):
        assert normalize_for_comparison("Étudiants") == "etudiants"

    def test_strips_whitespace(self):
        assert normalize_for_comparison("  SN  ") == "sn"

    def test_none_returns_empty(self):
        assert normalize_for_comparison(None) == ""


class TestNormalizeCountryCode:
    def test_iso2_uppercase(self):
        assert normalize_country_code("FR") == "FR"

    def test_iso2_lowercase(self):
        assert normalize_country_code("fr") == "FR"

    def test_iso3_code(self):
        assert normalize_country_code("FRA") == "FR"

    def test_french_name(self):
        assert normalize_country_code("France") == "FR"

    def test_french_name_with_accent(self):
        assert normalize_country_code("Sénégal") == "SN"

    def test_english_name(self):
        assert normalize_country_code("Germany") == "DE"

    def test_unknown_returns_none(self):
        assert normalize_country_code("Atlantis") is None

    def test_empty_returns_none(self):
        assert normalize_country_code("") is None

    def test_none_returns_none(self):
        assert normalize_country_code(None) is None

    def test_uk_alias(self):
        assert normalize_country_code("UK") == "GB"

    def test_morocco(self):
        assert normalize_country_code("Maroc") == "MA"


class TestNormalizeDate:
    def test_iso_8601(self):
        from datetime import date

        assert normalize_date("2026-09-01") == date(2026, 9, 1)

    def test_dd_mm_yyyy_slash(self):
        from datetime import date

        assert normalize_date("01/09/2026") == date(2026, 9, 1)

    def test_dd_mm_yyyy_dash(self):
        from datetime import date

        assert normalize_date("01-09-2026") == date(2026, 9, 1)

    def test_empty_returns_none(self):
        assert normalize_date("") is None

    def test_none_returns_none(self):
        assert normalize_date(None) is None

    def test_invalid_returns_none(self):
        assert normalize_date("not-a-date") is None


class TestNormalizeIne:
    def test_uppercases(self):
        assert normalize_ine("abc123") == "ABC123"

    def test_strips_spaces(self):
        assert normalize_ine("  AB C 123  ") == "ABC123"

    def test_none_returns_empty(self):
        assert normalize_ine(None) == ""

    def test_empty_returns_empty(self):
        assert normalize_ine("") == ""


class TestDeduplicateByKey:
    def test_removes_exact_duplicates(self):
        records = [
            {"ine": "A", "year": 2026},
            {"ine": "B", "year": 2026},
            {"ine": "A", "year": 2026},
        ]
        result = deduplicate_by_key(records, "ine", "year")
        assert len(result) == 2

    def test_keeps_first_occurrence(self):
        records = [
            {"ine": "A", "year": 2026, "name": "Alice"},
            {"ine": "A", "year": 2026, "name": "Alice2"},
        ]
        result = deduplicate_by_key(records, "ine", "year")
        assert result[0]["name"] == "Alice"

    def test_no_duplicates_returns_all(self):
        records = [{"ine": "A"}, {"ine": "B"}, {"ine": "C"}]
        result = deduplicate_by_key(records, "ine")
        assert len(result) == 3

    def test_empty_list(self):
        assert deduplicate_by_key([], "ine") == []
