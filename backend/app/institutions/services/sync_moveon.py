from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any
from unicodedata import category, normalize

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from app.institutions.models import (
    PartnerUniversity,
    PartnerUniversityRawImport,
    PartnerUniversityRawImportStatus,
)
from app.reference.models import Country

from .moveon_client import MoveOnClient

COUNTRY_ALIASES = {
    "paysbas": "NL",
    "hollande": "NL",
    "royaumeuni": "GB",
    "grandebretagne": "GB",
    "etatsunis": "US",
    "usa": "US",
}


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    total: int = 0


def sync_moveon_institutions(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    for institution in client.fetch_institutions():
        result.total += 1
        payload = institution.payload
        raw_import = create_raw_import(payload)

        try:
            created = upsert_partner_university(payload)
        except (IntegrityError, ValidationError, ValueError, KeyError) as exc:
            result.failed += 1
            mark_raw_import(
                raw_import,
                PartnerUniversityRawImportStatus.FAILED,
                str(exc),
            )
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, PartnerUniversityRawImportStatus.IMPORTED)

    return result


def create_raw_import(payload: dict[str, Any]) -> PartnerUniversityRawImport:
    return PartnerUniversityRawImport.objects.create(
        source="moveon_fake_institutions",
        source_file="fake_institutions.json",
        external_id=str(payload.get("moveon_id") or ""),
        payload=payload,
    )


def mark_raw_import(
    raw_import: PartnerUniversityRawImport,
    status: PartnerUniversityRawImportStatus,
    error_message: str = "",
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == PartnerUniversityRawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )


@transaction.atomic
def upsert_partner_university(payload: dict[str, Any]) -> bool:
    moveon_id = payload.get("moveon_id")
    if moveon_id in (None, ""):
        raise ValueError("Missing moveon_id")

    country = resolve_country(payload.get("country", {}))
    defaults = {
        "name": payload["name"],
        "short_name": payload.get("short_name") or "",
        "translated_name": payload.get("translated_name") or "",
        "erasmus_code": payload.get("erasmus_code") or "",
        "city": payload.get("city") or "",
        "url": payload.get("url") or "",
        "email": payload.get("email") or "",
        "country": country,
        "last_sync_moveon": timezone.now(),
    }

    university, created = PartnerUniversity.objects.update_or_create(
        moveon_id=int(moveon_id),
        defaults=defaults,
    )
    university.full_clean()
    university.save()
    return created


def resolve_country(payload: dict[str, Any]) -> Country:
    if not payload:
        raise ValueError("Missing country payload")

    if isinstance(payload.get("country"), dict):
        payload = payload["country"]

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


def get_country_name(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("country"), dict):
        payload = payload["country"]

    for key in ("name_fr", "name_en", "name", "Pays"):
        value = payload.get(key)
        if value:
            return str(value).strip()

    return ""


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
