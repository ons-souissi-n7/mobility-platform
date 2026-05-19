from difflib import get_close_matches
from typing import Any
from unicodedata import category, normalize

from django.db.models import Q

from app.reference.models import Country

COUNTRY_ALIASES = {
    "paysbas": "NL",
    "hollande": "NL",
    "royaumeuni": "GB",
    "grandebretagne": "GB",
    "etatsunis": "US",
    "usa": "US",
}


def normalize_text(value: str) -> str:
    normalized = normalize("NFKD", value.casefold().strip())
    without_accents = "".join(char for char in normalized if category(char) != "Mn")
    return "".join(char for char in without_accents if char.isalnum())


def resolve_country_alias(country_name: str) -> Country | None:
    iso2 = COUNTRY_ALIASES.get(normalize_text(country_name))
    if not iso2:
        return None

    try:
        return Country.objects.get(iso2=iso2)
    except Country.DoesNotExist as exc:
        raise ValueError(f"Unknown country iso2: {iso2}") from exc


def find_fuzzy_country_match(
    normalized_name: str,
    countries: list[Country],
) -> Country | None:
    lookup = {normalize_text(country.name_fr): country for country in countries} | {
        normalize_text(country.name_en): country for country in countries
    }
    matches = get_close_matches(
        normalized_name,
        lookup.keys(),
        n=2,
        cutoff=0.88,
    )

    if len(matches) == 1:
        return lookup[matches[0]]

    return None


def get_country_name(payload: dict[str, Any]) -> str:
    for key in ("name_fr", "name_en", "name", "Pays"):
        value = payload.get(key)
        if value:
            return str(value).strip()

    return ""


def resolve_country(payload: dict[str, Any]) -> Country:
    if not payload:
        raise ValueError("Missing country payload")

    iso2 = str(payload.get("iso2") or "").strip().upper()
    if iso2:
        try:
            return Country.objects.get(iso2=iso2)
        except Country.DoesNotExist as exc:
            raise ValueError(f"Unknown country iso2: {iso2}") from exc

    country_name = get_country_name(payload)
    if not country_name:
        raise ValueError("Missing country name")

    aliased_country = resolve_country_alias(country_name)
    if aliased_country:
        return aliased_country

    exact_matches = Country.objects.filter(
        Q(name_fr__iexact=country_name) | Q(name_en__iexact=country_name)
    )

    if exact_matches.count() == 1:
        return exact_matches.get()

    normalized_name = normalize_text(country_name)
    countries = list(Country.objects.all())
    normalized_matches = [
        country
        for country in countries
        if normalized_name
        in {normalize_text(country.name_fr), normalize_text(country.name_en)}
    ]

    if len(normalized_matches) == 1:
        return normalized_matches[0]

    if len(normalized_matches) > 1 or exact_matches.count() > 1:
        raise ValueError(f"Ambiguous country name: {country_name}")

    fuzzy_match = find_fuzzy_country_match(normalized_name, countries)
    if fuzzy_match:
        return fuzzy_match

    raise ValueError(f"Unknown country name: {country_name}")
