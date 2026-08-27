"""
Adaptateur Excel -> StudentRow.

Colonnes attendues (insensible a la casse, ordre libre) :
  INE | Nom | Prenom | Email | Genre | Departement | Niveau | Parcours |
  GPA / Moyenne | Boursier | FISE/FISA
"""

import logging
from io import BytesIO

import openpyxl

from app.shared.cleaning import normalize_gender

from ..student_importer import StudentRow

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
    "boursier": "is_scholarship",
    "fise/fisa": "is_alternant",
    "fisefisa": "is_alternant",
    "alternant": "is_alternant",
}

_TRUE_VALUES = {"oui", "yes", "true", "vrai", "1", "fisa", "x"}
_FALSE_VALUES = {"non", "no", "false", "faux", "0", "fise"}


def _parse_bool(value) -> bool | None:
    """Parse a Oui/Non (or FISA/FISE) cell — returns None when blank/unrecognized
    so the importer leaves the existing value untouched rather than guessing."""
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return None


def parse(file_bytes: bytes) -> list[StudentRow]:
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    raw_headers = next(rows_iter, None)
    if raw_headers is None:
        return []

    headers = [_COLUMN_MAP.get(_normalize(h), None) for h in raw_headers]

    result: list[StudentRow] = []
    for row_idx, raw_row in enumerate(rows_iter, start=2):
        if not any(cell is not None and str(cell).strip() for cell in raw_row):
            continue  # ligne entièrement vide (ex. fin de feuille) — pas une erreur

        data: dict = {}
        for field_name, value in zip(headers, raw_row, strict=False):
            if field_name and value is not None:
                data[field_name] = value

        # Une ligne sans INE mais avec d'autres données n'est PAS ignorée : elle
        # doit atteindre import_students() pour que validate_student() la
        # rejette proprement et qu'elle apparaisse dans le panneau d'erreurs
        # (sinon elle disparaît sans laisser de trace — perte d'information).
        ine = str(data.get("ine", "")).strip()

        gender = normalize_gender(str(data.get("gender", "")))

        # Parsé séparément (plutôt que dans le constructeur StudentRow ci-dessous)
        # pour qu'une valeur invalide (ex. "quinze") ne fasse pas planter toute
        # la ligne et la fasse disparaître silencieusement — elle est plutôt
        # transmise avec parse_error pour finir en échec explicite et visible
        # dans le panneau d'erreurs (import_students la rejette proprement).
        gpa: float | None = None
        parse_error: str | None = None
        if "gpa" in data and data["gpa"] is not None:
            try:
                gpa = float(data["gpa"])
            except (ValueError, TypeError):
                parse_error = f"GPA invalide : '{data['gpa']}'"

        try:
            result.append(
                StudentRow(
                    ine=ine,
                    row_number=row_idx,
                    first_name=str(data.get("first_name", "")).strip(),
                    last_name=str(data.get("last_name", "")).strip(),
                    email=str(data.get("email", "")).strip(),
                    gender=gender,
                    department_code=str(data.get("department_code", "")).strip(),
                    level_code=str(data.get("level_code", "")).strip(),
                    parcours_code=str(data["parcours_code"]).strip() or None
                    if "parcours_code" in data
                    else None,
                    gpa=gpa,
                    parse_error=parse_error,
                    nationality_iso2=str(data["nationality_iso2"]).strip() or None
                    if "nationality_iso2" in data and data["nationality_iso2"]
                    else None,
                    is_scholarship=_parse_bool(data["is_scholarship"])
                    if "is_scholarship" in data
                    else None,
                    is_alternant=_parse_bool(data["is_alternant"])
                    if "is_alternant" in data
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
