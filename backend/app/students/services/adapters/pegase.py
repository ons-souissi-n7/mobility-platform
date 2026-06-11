"""
Adaptateur Pegase -> StudentRow.

En développement : PEGASE_API_URL pointe vers fake-pegase-api (GET /api/inscriptions).
En production    : PEGASE_API_URL pointe vers l'API Pégase réelle.
Si PEGASE_API_URL n'est pas configuré, la sync retourne une liste vide.
"""

import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from ..student_importer import StudentRow

logger = logging.getLogger(__name__)

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
    """Appelle l'API Pégase pour récupérer les inscriptions de l'année donnée."""
    api_url = getattr(settings, "PEGASE_API_URL", "").rstrip("/")
    if not api_url:
        logger.warning("PEGASE_API_URL n'est pas configuré — sync étudiants ignorée")
        return []

    logger.info("Pégase sync %s — %s/api/inscriptions", academic_year_label, api_url)
    params = urlencode({"annee": academic_year_label})
    request = Request(
        f"{api_url}/api/inscriptions?{params}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError) as exc:
        logger.error("Pégase API indisponible : %s", exc)
        return []

    if not isinstance(data, list):
        logger.error("Pégase /api/inscriptions doit retourner une liste")
        return []

    return _parse_rows(data)


def _parse_rows(data: list) -> list[StudentRow]:
    """Convertit une liste de dicts Pégase en StudentRow.  Exporté pour les tests unitaires."""
    rows: list[StudentRow] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ine = str(item.get("ine", "")).strip()
        if not ine:
            continue

        raw_gender = str(item.get("sexe", item.get("genre", ""))).strip().lower()
        gender = _GENDER_MAP.get(raw_gender, "")

        raw_gpa = item.get("moyenne", item.get("gpa"))
        gpa: float | None = None
        if raw_gpa is not None:
            try:
                gpa = float(raw_gpa)
            except (ValueError, TypeError):
                pass

        parcours_raw = item.get("parcours")
        parcours_code = str(parcours_raw).strip() or None if parcours_raw else None

        # Nationalité : texte libre ("France", "Maroc"…) ou code ISO2 ("FR")
        nationality_raw = (
            str(
                item.get("nationalite")
                or item.get("pays_iso2")
                or item.get("nationalite_iso2")
                or ""
            ).strip()
            or None
        )

        # Identifiant Pégase (champ explicite ou INE par défaut)
        source_id = str(item.get("pegase_id", ine)).strip() or ine

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
                nationality_iso2=nationality_raw,
                source_id=source_id,
            )
        )

    return rows
