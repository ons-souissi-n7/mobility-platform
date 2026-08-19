"""
Adaptateur Pegase -> StudentRow.

En développement : PEGASE_API_URL pointe vers fake-pegase-api (GET /api/inscriptions).
En production    : PEGASE_API_URL pointe vers l'API Pégase réelle.
Si PEGASE_API_URL n'est pas configuré, la sync retourne une liste vide.
"""

import json
import logging
from datetime import date
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

from app.shared.cleaning import normalize_gender

from ..student_importer import StudentRow

logger = logging.getLogger(__name__)


def fetch_enrollments(start_date: date, end_date: date) -> list[StudentRow]:
    """Récupère toutes les inscriptions Pégase et filtre celles dont la date de création
    ou de modification appartient à la plage [start_date, end_date]."""
    api_url = getattr(settings, "PEGASE_API_URL", "").rstrip("/")
    if not api_url:
        logger.warning("PEGASE_API_URL n'est pas configuré — sync étudiants ignorée")
        return []

    logger.info(
        "Pégase sync %s → %s — %s/api/inscriptions", start_date, end_date, api_url
    )
    request = Request(
        f"{api_url}/api/inscriptions",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError):
        logger.exception("Pégase API indisponible")
        return []

    if not isinstance(data, list):
        logger.error("Pégase /api/inscriptions doit retourner une liste")
        return []

    matching = [
        row
        for row in data
        if isinstance(row, dict) and _in_range(row, start_date, end_date)
    ]
    logger.info(
        "Pégase : %d inscriptions totales, %d dans la plage %s → %s",
        len(data),
        len(matching),
        start_date,
        end_date,
    )
    return _parse_rows(matching)


def _in_range(row: dict, start_date: date, end_date: date) -> bool:
    """Retourne True si date_creation ou date_modification est dans [start_date, end_date]."""
    for field in ("date_creation", "date_modification"):
        raw = row.get(field)
        if not raw:
            continue
        try:
            d = date.fromisoformat(str(raw)[:10])
            if start_date <= d <= end_date:
                return True
        except ValueError:
            continue
    return False


def _parse_rows(data: list) -> list[StudentRow]:
    """Convertit une liste de dicts Pégase en StudentRow.  Exporté pour les tests unitaires."""
    rows: list[StudentRow] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ine = str(item.get("ine", "")).strip()
        if not ine:
            continue

        gender = normalize_gender(str(item.get("sexe", item.get("genre", ""))))

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
