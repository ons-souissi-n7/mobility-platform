from dataclasses import dataclass
from datetime import date
from typing import Any

from .moveon_schema import validate_raw_payload


@dataclass(frozen=True)
class TransformedMobilityCategory:
    moveon_framework_id: str
    external_id: str
    name: str
    relation_types: str
    is_active: bool


@dataclass(frozen=True)
class TransformedAgreementAvailability:
    academic_year_label: str
    is_available: bool
    remarks: str = ""


@dataclass(frozen=True)
class TransformedAgreement:
    moveon_relation_id: str
    reference: str
    name: str
    partner_university_moveon_id: int | None
    partner_university_id: int | None
    partner_university_erasmus_code: str
    partner_university_name: str
    relation_type: str
    framework: str
    direction: str
    status: str
    is_active: bool
    start_date: date | None
    end_date: date | None
    start_academic_year: str
    end_academic_year: str
    discipline: str
    isced: str
    level: str
    formation: str
    url: str
    restrictions: str
    remarks: str
    department_tokens: tuple[str, ...]
    level_tokens: tuple[str, ...]
    availabilities: tuple[TransformedAgreementAvailability, ...]


@dataclass(frozen=True)
class TransformedAgreementQuota:
    moveon_relation_id: str
    agreement_id: int | None
    academic_year_id: int | None
    academic_year_label: str
    period: str
    places_id: str | None
    total_places: int
    remaining_places: int
    total_duration: int | None
    duration_unit: str
    is_effective: bool
    remarks: str


def transform_mobility_category(payload: dict[str, Any]) -> TransformedMobilityCategory:
    raw = validate_raw_payload(payload)
    framework_id = first_value(raw, "moveon_framework_id", "Cadre ID", "framework_id")
    if framework_id in (None, ""):
        raise ValueError("moveon_framework_id is required")

    return TransformedMobilityCategory(
        moveon_framework_id=str(framework_id).strip(),
        external_id=text(first_value(raw, "external_id", "ID externe")),
        name=text(first_value(raw, "name", "Nom")),
        relation_types=text(first_value(raw, "relation_types", "Types de relations")),
        is_active=bool_value(first_value(raw, "is_active", "Actif"), default=True),
    )


def transform_agreement(payload: dict[str, Any]) -> TransformedAgreement:
    raw = validate_raw_payload(payload)
    relation_id = first_value(
        raw,
        "moveon_relation_id",
        "relation_id",
        "Identifiant relation",
        "Relation: Identifiant relation",
    )

    if relation_id in (None, ""):
        raise ValueError("moveon_relation_id is required")

    relation_type = text(first_value(raw, "relation_type", "Type de relation"))
    framework = text(first_value(raw, "framework", "Cadres", "Relation: Cadres"))
    direction = text(
        first_value(raw, "direction", "Direction", "Relation: Direction") or "unknown"
    )
    level = text(first_value(raw, "level", "Niveau", "Relation: Niveau"))

    return TransformedAgreement(
        moveon_relation_id=str(relation_id).strip(),
        reference=text(first_value(raw, "reference", "Reference")),
        name=text(first_value(raw, "name", "Nom", "Relation: Nom")),
        partner_university_moveon_id=optional_int(
            first_value(
                raw,
                "partner_university_moveon_id",
                "partner_moveon_id",
                "Etablissement: ID",
            )
        ),
        partner_university_id=optional_int(raw.get("partner_university_id")),
        partner_university_erasmus_code=text(
            first_value(raw, "erasmus_code", "Code Erasmus")
        ),
        partner_university_name=text(
            first_value(
                raw,
                "partner_university_name",
                "Etablissements externes",
                "Etablissements externes : arborescence",
                "Etablissement: Nom",
            )
        ),
        relation_type=relation_type,
        framework=framework,
        direction=direction,
        status=text(
            first_value(raw, "status", "Statut", "Relation: Statut") or "draft"
        ),
        is_active=bool_value(first_value(raw, "is_active", "Actif"), default=True),
        start_date=optional_date(
            first_value(raw, "start_date", "Date de debut", "Relation: Date de debut")
        ),
        end_date=optional_date(
            first_value(raw, "end_date", "Date de fin", "Relation: Date de fin")
        ),
        start_academic_year=text(
            first_value(
                raw,
                "start_academic_year",
                "Debut (annee acad.)",
                "Relation: Debut (annee acad.)",
            )
        ),
        end_academic_year=text(
            first_value(
                raw,
                "end_academic_year",
                "Fin (annee acad.)",
                "Relation: Fin (annee acad.)",
            )
        ),
        discipline=text(
            first_value(raw, "discipline", "Discipline", "Relation: Discipline")
        ),
        isced=text(first_value(raw, "isced", "ISCED", "Relation: ISCED")),
        level=level,
        formation=text(
            first_value(raw, "formation", "Formation", "Relation: Formation")
        ),
        url=text(first_value(raw, "url", "URL", "Relation: Site Internet")),
        restrictions=text(
            first_value(
                raw,
                "restrictions",
                "Restrictions",
                "Restrictions de recrutement",
                "Relation: Restrictions",
            )
        ),
        remarks=text(
            first_value(
                raw,
                "remarks",
                "Remarques",
                "Relation: Remarques",
                "Etablissements internes",
            )
        ),
        department_tokens=split_values(
            first_value(
                raw,
                "department_codes",
                "departments",
                "departements",
                "departements_concernes",
                "Departements concernes",
                "Etablissements internes",
            )
        ),
        level_tokens=split_values(first_value(raw, "levels")) or split_values(level),
        availabilities=transform_agreement_availabilities(raw),
    )


def transform_agreement_quota(payload: dict[str, Any]) -> TransformedAgreementQuota:
    raw = validate_raw_payload(payload)
    relation_id = first_value(
        raw,
        "moveon_relation_id",
        "relation_id",
        "Relation: Identifiant relation",
        "Identifiant relation",
    )

    return TransformedAgreementQuota(
        moveon_relation_id=text(relation_id),
        agreement_id=optional_int(raw.get("agreement_id")),
        academic_year_id=optional_int(raw.get("academic_year_id")),
        academic_year_label=normalize_academic_year_label(
            text(first_value(raw, "academic_year_label", "Annee academique"))
        ),
        period=text(first_value(raw, "period", "Periode academique")),
        places_id=optional_text(first_value(raw, "places_id", "Places: ID")),
        total_places=required_int(
            first_value(raw, "total_places", "Nombre"),
            "total_places",
        ),
        remaining_places=required_int(
            first_value(raw, "remaining_places", "Places restantes"),
            "remaining_places",
        ),
        total_duration=optional_int(first_value(raw, "total_duration", "Duree totale")),
        duration_unit=text(first_value(raw, "duration_unit", "Unite de temps")),
        is_effective=bool_value(
            first_value(raw, "is_effective", "Effectif"), default=True
        ),
        remarks=text(first_value(raw, "remarks", "Remarques")),
    )


def transform_agreement_availabilities(
    raw: dict[str, Any],
) -> tuple[TransformedAgreementAvailability, ...]:
    availabilities: list[TransformedAgreementAvailability] = []

    for label in split_values(
        first_value(
            raw,
            "available_academic_years",
            "available_years",
            "annees_disponibles",
            "Annees disponibles",
        )
    ):
        availabilities.append(
            TransformedAgreementAvailability(
                academic_year_label=normalize_academic_year_label(label),
                is_available=True,
                remarks="Disponibilite importee depuis MoveON.",
            )
        )

    for label in split_values(
        first_value(
            raw,
            "unavailable_academic_years",
            "unavailable_years",
            "annees_indisponibles",
            "Annees indisponibles",
        )
    ):
        availabilities.append(
            TransformedAgreementAvailability(
                academic_year_label=normalize_academic_year_label(label),
                is_available=False,
                remarks="Indisponibilite importee depuis MoveON.",
            )
        )

    year_label = text(first_value(raw, "academic_year_label", "Annee academique"))
    availability = first_value(
        raw,
        "is_available_for_year",
        "available_for_year",
        "disponible_pour_annee",
        "Disponible pour annee",
    )
    if year_label and availability not in (None, ""):
        availabilities.append(
            TransformedAgreementAvailability(
                academic_year_label=normalize_academic_year_label(year_label),
                is_available=bool_value(availability, default=True),
                remarks="Disponibilite annuelle importee depuis MoveON.",
            )
        )

    deduplicated = {
        availability.academic_year_label: availability
        for availability in availabilities
    }
    return tuple(deduplicated.values())


def first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_academic_year_label(value: str) -> str:
    if "/" in value and len(value.split("/")[-1]) == 2:
        start, end = value.split("/", 1)
        return f"{start}-20{end}"
    return value.replace("/", "-")


def split_values(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, list | tuple | set):
        raw_values = [str(item) for item in value]
    else:
        normalized = str(value)
        for separator in ["|", ";", "\n", "\t"]:
            normalized = normalized.replace(separator, ",")
        raw_values = normalized.split(",")

    cleaned: list[str] = []
    for raw_value in raw_values:
        value = raw_value.strip()
        if value and value not in cleaned:
            cleaned.append(value)
    return tuple(cleaned)


def text(value: Any) -> str:
    return str(value or "").strip()


def optional_text(value: Any) -> str | None:
    cleaned = text(value)
    return cleaned or None


def required_int(value: Any, field_name: str) -> int:
    if value in (None, ""):
        raise ValueError(f"{field_name} is required")
    return int(value)


def optional_int(value: Any) -> int | None:
    return int(value) if value not in (None, "") else None


def optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def bool_value(value: Any, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "oui"}
