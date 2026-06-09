"""
Adaptateur Excel -> StudentRow.

Colonnes attendues (insensible a la casse, ordre libre) :
  INE | Nom | Prenom | Email | Genre | Departement | Niveau | Parcours | GPA / Moyenne
"""

import logging
from io import BytesIO

import openpyxl

from ..etl import StudentRow

logger = logging.getLogger(__name__)

_COLUMN_MAP = {
    "ine": "ine",
    "nom": "last_name",
    "prenom": "first_name",
    "prénom": "first_name",
    "email": "email",
    "courriel": "email",
    "genre": "gender",
    "sexe": "gender",
    "departement": "department_code",
    "département": "department_code",
    "dept": "department_code",
    "niveau": "level_code",
    "parcours": "parcours_code",
    "gpa": "gpa",
    "moyenne": "gpa",
    "note": "gpa",
    "nationalite": "nationality_iso2",
    "nationalité": "nationality_iso2",
    "pays": "nationality_iso2",
    "pays_iso2": "nationality_iso2",
    "nationalite_iso2": "nationality_iso2",
}

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


def parse(file_bytes: bytes) -> list[StudentRow]:
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    raw_headers = next(rows_iter, None)
    if raw_headers is None:
        return []

    headers = [_COLUMN_MAP.get(_normalize(h), None) for h in raw_headers]

    result: list[StudentRow] = []
    for raw_row in rows_iter:
        data: dict = {}
        for field_name, value in zip(headers, raw_row, strict=False):
            if field_name and value is not None:
                data[field_name] = value

        ine = str(data.get("ine", "")).strip()
        if not ine:
            continue

        raw_gender = str(data.get("gender", "")).strip().lower()
        gender = _GENDER_MAP.get(raw_gender, "")

        try:
            result.append(
                StudentRow(
                    ine=ine,
                    first_name=str(data.get("first_name", "")).strip(),
                    last_name=str(data.get("last_name", "")).strip(),
                    email=str(data.get("email", "")).strip(),
                    gender=gender,
                    department_code=str(data.get("department_code", "")).strip(),
                    level_code=str(data.get("level_code", "")).strip(),
                    parcours_code=str(data["parcours_code"]).strip() or None
                    if "parcours_code" in data
                    else None,
                    gpa=float(data["gpa"])
                    if "gpa" in data and data["gpa"] is not None
                    else None,
                    nationality_iso2=str(data["nationality_iso2"]).strip() or None
                    if "nationality_iso2" in data and data["nationality_iso2"]
                    else None,
                )
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Ligne ignoree (INE=%s) : %s", ine, exc)

    return result


def _normalize(header) -> str:
    return (
        str(header).strip().lower().replace(" ", "").replace("_", "") if header else ""
    )
