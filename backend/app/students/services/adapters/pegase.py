"""
Adaptateur Pegase -> StudentRow.

En production : appel API Pegase (endpoint /inscriptions?annee=<label>).
En dev / fallback : lecture du fichier fixtures/pegase_students.json.
"""

import json
import logging
from pathlib import Path

from ..etl import StudentRow

logger = logging.getLogger(__name__)

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "pegase_students.json"
)

_GENDER_MAP = {
    "h": "M",
    "homme": "M",
    "m": "M",
    "masculin": "M",
    "f": "F",
    "femme": "F",
    "féminin": "F",
    "feminin": "F",
}


def fetch_enrollments(academic_year_label: str) -> list[StudentRow]:
    """Retourne les inscriptions pour l'annee donnee depuis Pegase (ou la fixture dev)."""
    # TODO: integrer l'API Pegase reelle (endpoint /inscriptions?annee=<label>)
    logger.info(
        "Pegase sync pour l'annee %s — lecture de la fixture locale",
        academic_year_label,
    )
    return _load_fixture()


def _load_fixture() -> list[StudentRow]:
    if not _FIXTURE_PATH.exists():
        logger.warning("Fixture Pegase introuvable : %s", _FIXTURE_PATH)
        return []

    try:
        data = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Impossible de lire la fixture Pegase : %s", exc)
        return []

    rows: list[StudentRow] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ine = str(item.get("ine", "")).strip()
        if not ine:
            continue

        raw_gender = str(item.get("sexe", item.get("genre", ""))).strip().lower()
        gender = _GENDER_MAP.get(raw_gender, "")

        raw_gpa = item.get("gpa")
        gpa: float | None = None
        if raw_gpa is not None:
            try:
                gpa = float(raw_gpa)
            except (ValueError, TypeError):
                pass

        parcours_raw = item.get("parcours")
        parcours_code = str(parcours_raw).strip() or None if parcours_raw else None

        rows.append(
            StudentRow(
                ine=ine,
                first_name=str(item.get("prenom", "")).strip(),
                last_name=str(item.get("nom", "")).strip(),
                email=str(item.get("email", "")).strip(),
                gender=gender,
                department_code=str(item.get("departement", "")).strip(),
                level_code=str(item.get("niveau", "")).strip(),
                parcours_code=parcours_code,
                gpa=gpa,
            )
        )

    return rows
