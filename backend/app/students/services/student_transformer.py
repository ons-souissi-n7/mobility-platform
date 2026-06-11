"""
Transform raw payloads (from Pégase, Excel, MoveON) into clean typed dataclasses.
All normalization is applied here via app.shared.cleaning so downstream code
works with clean data.
"""

from dataclasses import dataclass
from typing import Any

from app.shared.cleaning import (
    normalize_country_code,
    normalize_ine,
    normalize_string,
)


@dataclass(frozen=True)
class TransformedStudent:
    ine: str
    first_name: str
    last_name: str
    email: str
    gender: str
    department_code: str
    level_code: str
    parcours_code: str | None
    gpa: float | None
    nationality_iso2: str | None
    source_id: str | None


@dataclass(frozen=True)
class TransformedWish:
    ine: str
    individu: str
    offre_de_sejour: str
    rank: int


def transform_student(payload: dict[str, Any]) -> TransformedStudent:
    """Normalize a raw student payload into a typed dataclass."""
    ine = normalize_ine(str(payload.get("ine") or ""))
    if not ine:
        raise ValueError("ine est requis")

    raw_gpa = payload.get("gpa")
    gpa: float | None = None
    if raw_gpa not in (None, ""):
        try:
            gpa = float(raw_gpa)
        except (ValueError, TypeError):
            gpa = None

    nationality_raw = str(payload.get("nationality_iso2") or "").strip() or None
    nationality_iso2 = (
        normalize_country_code(nationality_raw) if nationality_raw else None
    )

    return TransformedStudent(
        ine=ine,
        first_name=normalize_string(str(payload.get("first_name") or "")),
        last_name=normalize_string(str(payload.get("last_name") or "")),
        email=(str(payload.get("email") or "")).strip().lower(),
        gender=normalize_string(str(payload.get("gender") or "")).upper(),
        department_code=normalize_string(
            str(payload.get("department_code") or "")
        ).upper(),
        level_code=normalize_string(str(payload.get("level_code") or "")).upper(),
        parcours_code=(
            normalize_string(str(payload["parcours_code"])).upper()
            if payload.get("parcours_code")
            else None
        ),
        gpa=gpa,
        nationality_iso2=nationality_iso2,
        source_id=str(payload["source_id"]) if payload.get("source_id") else None,
    )


def transform_wish(payload: dict[str, Any]) -> TransformedWish:
    """Normalize a raw wish payload (from MoveON or Excel) into a typed dataclass."""
    offre = normalize_string(str(payload.get("offre_de_sejour") or ""))
    if not offre:
        raise ValueError("offre_de_sejour est requise")

    rank = int(payload.get("rank") or 0)
    if rank < 1:
        raise ValueError("rank doit être >= 1")

    return TransformedWish(
        ine=normalize_ine(str(payload.get("ine") or "")),
        individu=normalize_string(str(payload.get("individu") or "")),
        offre_de_sejour=offre,
        rank=rank,
    )
