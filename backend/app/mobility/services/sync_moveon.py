from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.institutions.models import PartnerUniversity
from app.integrations.moveon import MoveOnClient
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    MobilityCategory,
    NomenclatureMapping,
)
from app.reference.models import Department, Level
from app.shared.cleaning import normalize_for_comparison
from app.shared.sync import (
    SyncConflictError,
    SyncResult,
    already_up_to_date,
    detect_sync_conflict,
    mark_raw_import,
)

from .moveon_transformer import (
    TransformedAgreement,
    TransformedAgreementQuota,
    TransformedMobilityCategory,
    transform_agreement,
    transform_agreement_quota,
    transform_mobility_category,
)
from .moveon_validator import (
    validate_agreement,
    validate_agreement_quota,
    validate_mobility_category,
)

_N7_TOKENS = frozenset({"n7", "enseeiht", "inp toulouse n7", "inp n7"})


def _n7_is_present(inp_institutions: str) -> bool:
    normalized = inp_institutions.strip().casefold()
    return any(token in normalized for token in _N7_TOKENS)


@dataclass
class MobilitySyncResult:
    frameworks: SyncResult
    agreements: SyncResult
    quotas: SyncResult


def sync_moveon_mobility(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> MobilitySyncResult:
    """Sync complet : cadres + accords + quotas."""
    client = client or MoveOnClient()
    frameworks = sync_moveon_mobility_categories(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    agreements = sync_moveon_agreements(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    quotas = sync_moveon_agreement_inp_quotas(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    return MobilitySyncResult(
        frameworks=frameworks, agreements=agreements, quotas=quotas
    )


def sync_moveon_agreements_only(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> MobilitySyncResult:
    """Sync accords + quotas uniquement, sans toucher aux cadres."""
    client = client or MoveOnClient()
    dummy = SyncResult()
    agreements = sync_moveon_agreements(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    quotas = sync_moveon_agreement_inp_quotas(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    return MobilitySyncResult(frameworks=dummy, agreements=agreements, quotas=quotas)


def sync_moveon_mobility_categories(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_CATEGORIES,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    # Pré-chargement des IGNORED — évite une requête par enregistrement dans la boucle
    ignored_external_ids = set(
        RawImport.objects.filter(
            entity=RawImportEntity.AGREEMENT_CATEGORY,
            status=RawImportStatus.IGNORED,
        ).values_list("external_id", flat=True)
    )

    for category in client.fetch_agreement_frameworks():
        payload = category.payload
        external_id = _extract_external_id(payload, RawImportEntity.AGREEMENT_CATEGORY)

        if external_id in ignored_external_ids:
            continue

        raw_import = _create_raw_import(
            payload,
            RawImportEntity.AGREEMENT_CATEGORY,
            import_report=report,
            academic_year=academic_year,
        )

        try:
            transformed = transform_mobility_category(payload)
            validate_mobility_category(transformed)
            created = upsert_mobility_category(transformed)
        except SyncConflictError as exc:
            result.conflicted += 1
            moveon_id = str(
                payload.get("moveon_id") or payload.get("moveon_framework_id") or ""
            )
            if moveon_id:
                existing_cat = MobilityCategory.objects.filter(
                    moveon_id=moveon_id
                ).first()
                if existing_cat:
                    raw_import.payload = {
                        **raw_import.payload,
                        "_existing": {
                            "moveon_id": str(existing_cat.moveon_id or ""),
                            "name": existing_cat.name,
                        },
                    }
                    raw_import.save(update_fields=["payload"])
            mark_raw_import(raw_import, RawImportStatus.CONFLICT, str(exc))
            report.record_conflict(raw_import.external_id, str(exc), raw_import.id)
            continue
        except (
            IntegrityError,
            DjangoValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1
        report.record_success()
        mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    result.total = result.created + result.updated + result.failed + result.conflicted
    report.finalize()
    return result


def sync_moveon_agreements(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_ACCORDS,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    # Pré-chargement des IGNORED — évite une requête par enregistrement dans la boucle
    ignored_external_ids = set(
        RawImport.objects.filter(
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.IGNORED,
        ).values_list("external_id", flat=True)
    )

    for agreement in client.fetch_agreements():
        payload = agreement.payload
        external_id = _extract_external_id(payload, RawImportEntity.AGREEMENT)

        if external_id in ignored_external_ids:
            continue

        raw_import = _create_raw_import(
            payload,
            RawImportEntity.AGREEMENT,
            import_report=report,
            academic_year=academic_year,
        )

        try:
            transformed = transform_agreement(payload)
            validate_agreement(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if not _n7_is_present(transformed.inp_institutions):
            result.ignored += 1
            mark_raw_import(
                raw_import,
                RawImportStatus.IGNORED,
                "N7/ENSEEIHT absent des établissements INP de cet accord",
            )
            continue

        try:
            created = upsert_agreement(transformed)
        except SyncConflictError as exc:
            result.conflicted += 1
            moveon_id = str(payload.get("moveon_id") or "")
            if moveon_id:
                existing_agr = (
                    Agreement.objects.filter(moveon_id=moveon_id)
                    .select_related("partner_university", "category")
                    .first()
                )
                if existing_agr:
                    raw_import.payload = {
                        **raw_import.payload,
                        "_existing": {
                            "moveon_id": str(existing_agr.moveon_id or ""),
                            "name": existing_agr.name or "",
                            "partner_university_name": (
                                existing_agr.partner_university.name
                                if existing_agr.partner_university
                                else ""
                            ),
                            "direction": existing_agr.direction or "",
                            "valid_from": str(existing_agr.valid_from)
                            if existing_agr.valid_from
                            else None,
                            "valid_until": str(existing_agr.valid_until)
                            if existing_agr.valid_until
                            else None,
                            "inp_institutions": existing_agr.inp_institutions or "",
                        },
                    }
                    raw_import.save(update_fields=["payload"])
            mark_raw_import(raw_import, RawImportStatus.CONFLICT, str(exc))
            report.record_conflict(raw_import.external_id, str(exc), raw_import.id)
            continue
        except (
            IntegrityError,
            DjangoValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1
        report.record_success()
        mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    result.total = (
        result.created
        + result.updated
        + result.failed
        + result.ignored
        + result.conflicted
    )
    report.finalize()
    return result


def sync_moveon_agreement_inp_quotas(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    """Syncs INP quotas from MoveOn and updates agreement.inp_total_places."""
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_QUOTAS,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    for quota in client.fetch_agreement_quotas():
        payload = quota.payload
        external_id = str(
            payload.get("moveon_id") or payload.get("agreement_id") or "quota-unknown"
        )

        try:
            transformed = transform_agreement_quota(payload)
            validate_agreement_quota(transformed)
            _update_agreement_inp_quota(transformed)
        except (
            Agreement.DoesNotExist,
            IntegrityError,
            DjangoValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            report.record_error(external_id, str(exc))
            continue

        result.updated += 1
        report.record_success()

    result.total = result.updated + result.failed
    report.finalize()
    return result


@transaction.atomic
def upsert_agreement(
    transformed_data: TransformedAgreement | dict[str, Any],
    force_overwrite: bool = False,
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_agreement(transformed_data)
        validate_agreement(transformed_data)

    try:
        partner_university = _resolve_partner_university(transformed_data)
    except (PartnerUniversity.DoesNotExist, ValueError) as exc:
        raise ValueError(
            "Université partenaire introuvable dans le référentiel. "
            "Cliquez sur « Corriger » pour sélectionner l'université correspondante."
        ) from exc

    category = _resolve_mobility_category(transformed_data.category_name)

    # ── Résolution en 4 étapes ────────────────────────────────────────────────
    # 1. Par moveon_id (lien stable vers la source)
    agreement = Agreement.objects.filter(moveon_id=transformed_data.moveon_id).first()

    # 2. Par nom exact pour la même université (accord créé manuellement)
    if agreement is None:
        agreement = Agreement.objects.filter(
            name__iexact=transformed_data.name,
            partner_university=partner_university,
        ).first()

    # 3. Par nomenclature structurelle : (université + cadre + date_début + date_fin)
    #    Clé naturelle externe déterministe — auto-remplie par le sync accords.
    if agreement is None and transformed_data.start_date and transformed_data.end_date:
        mapping = (
            NomenclatureMapping.objects.filter(
                partner_university=partner_university,
                category=category,
                date_debut=transformed_data.start_date,
                date_fin=transformed_data.end_date,
            )
            .select_related("agreement")
            .first()
        )
        if mapping is not None:
            agreement = mapping.agreement

    # 4. Création si aucun match
    created = agreement is None
    if created:
        agreement = Agreement()
    elif not force_overwrite:
        if already_up_to_date(
            agreement,
            "last_sync_moveon",
            transformed_data.source_updated_at,
            name=transformed_data.name,
            direction=transformed_data.direction,
            valid_from=transformed_data.start_date,
            valid_until=transformed_data.end_date,
            inp_institutions=transformed_data.inp_institutions,
            remarks=transformed_data.remarks,
        ):
            return False
        if conflict := detect_sync_conflict(
            agreement, "last_sync_moveon", transformed_data.source_updated_at
        ):
            raise conflict

    # Auto-renseigne moveon_id si l'accord existait sans lui
    if not agreement.moveon_id:
        agreement.moveon_id = transformed_data.moveon_id

    agreement.name = transformed_data.name
    agreement.partner_university = partner_university
    agreement.category = category
    agreement.direction = transformed_data.direction
    agreement.valid_from = transformed_data.start_date
    agreement.valid_until = transformed_data.end_date
    agreement.inp_institutions = transformed_data.inp_institutions
    agreement.remarks = transformed_data.remarks
    agreement.full_clean()
    agreement.save()
    agreement.last_sync_moveon = agreement.updated_at
    agreement.save(update_fields=["last_sync_moveon"])
    _sync_departments(agreement, transformed_data.department_tokens)
    _sync_levels(agreement, transformed_data.level_tokens)
    _upsert_nomenclature(agreement, partner_university, category, transformed_data)
    return created


def _update_agreement_inp_quota(transformed_data: TransformedAgreementQuota) -> None:
    if transformed_data.agreement_id:
        agreement = Agreement.objects.get(pk=transformed_data.agreement_id)
    elif transformed_data.moveon_id:
        agreement = Agreement.objects.get(moveon_id=transformed_data.moveon_id)
    else:
        return

    if transformed_data.total_places > 0:
        agreement.inp_total_places = transformed_data.total_places
        agreement.save(update_fields=["inp_total_places", "updated_at"])


@transaction.atomic
def upsert_mobility_category(
    transformed_data: TransformedMobilityCategory | dict[str, Any],
    force_overwrite: bool = False,
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_mobility_category(transformed_data)
        validate_mobility_category(transformed_data)

    # Résolution : moveon_id → nom (cadre créé manuellement sans moveon_id)
    # Quand trouvé par nom, on renseigne le moveon_id pour accélérer les recherches futures.
    category = MobilityCategory.objects.filter(
        moveon_id=transformed_data.moveon_id
    ).first()

    if category is None:
        category = MobilityCategory.objects.filter(
            name__iexact=transformed_data.name.strip(),
            moveon_id__isnull=True,
        ).first()

    created = category is None
    if created:
        category = MobilityCategory()
    elif not force_overwrite:
        if already_up_to_date(
            category,
            "last_sync_moveon",
            transformed_data.source_updated_at,
            name=transformed_data.name,
        ):
            return False
        if conflict := detect_sync_conflict(
            category, "last_sync_moveon", transformed_data.source_updated_at
        ):
            raise conflict

    category.moveon_id = transformed_data.moveon_id
    category.name = transformed_data.name
    category.full_clean()
    category.save()
    category.last_sync_moveon = category.updated_at
    category.save(update_fields=["last_sync_moveon"])
    return created


# ── private helpers ────────────────────────────────────────────────────────────


def _extract_external_id(payload: dict[str, Any], entity: RawImportEntity) -> str:
    return str(
        payload.get("moveon_id")
        or payload.get("relation_id")
        or payload.get("moveon_framework_id")
        or f"raw-{entity.value}"
    )


def _create_raw_import(
    payload: dict[str, Any],
    entity: RawImportEntity,
    import_report: ImportReport | None = None,
    academic_year: AcademicYear | None = None,
) -> RawImport:
    external_id = _extract_external_id(payload, entity)
    return RawImport.objects.create(
        source=f"moveon_{entity.value}",
        source_file="",
        entity=entity,
        external_id=external_id,
        payload=payload,
        import_report=import_report,
        academic_year=academic_year,
    )


def _upsert_nomenclature(
    agreement: Agreement,
    partner_university: PartnerUniversity,
    category: MobilityCategory | None,
    transformed_data: TransformedAgreement,
) -> None:
    """Crée ou met à jour l'entrée de nomenclature liée à cet accord."""
    NomenclatureMapping.objects.update_or_create(
        agreement=agreement,
        defaults={
            "partner_university": partner_university,
            "category": category,
            "date_debut": transformed_data.start_date,
            "date_fin": transformed_data.end_date,
            "moveon_offer_name": transformed_data.name,
        },
    )


def _resolve_partner_university(
    transformed_data: TransformedAgreement,
) -> PartnerUniversity:
    # 1. By internal PK
    if transformed_data.partner_university_id:
        try:
            return PartnerUniversity.objects.get(
                pk=transformed_data.partner_university_id
            )
        except PartnerUniversity.DoesNotExist:
            pass

    # 2. By MoveON ID (most reliable external key)
    if transformed_data.partner_university_moveon_id:
        try:
            return PartnerUniversity.objects.get(
                moveon_id=transformed_data.partner_university_moveon_id
            )
        except PartnerUniversity.DoesNotExist:
            pass

    # 3. By Erasmus code — DB case-insensitive first, then whitespace-normalized fallback
    #    (handles legacy records stored with extra internal spaces, e.g. "I  TRENTO01")
    if transformed_data.partner_university_erasmus_code:
        code = transformed_data.partner_university_erasmus_code.strip()
        university = (
            PartnerUniversity.objects.exclude(erasmus_code="")
            .filter(erasmus_code__iexact=code)
            .first()
        )
        if university is None:
            code_norm = normalize_for_comparison(code)
            university = next(
                (
                    u
                    for u in PartnerUniversity.objects.exclude(erasmus_code="").only(
                        "id", "erasmus_code", "moveon_id"
                    )
                    if normalize_for_comparison(u.erasmus_code) == code_norm
                ),
                None,
            )
        if university is not None:
            _backfill_university_moveon_id(
                university, transformed_data.partner_university_moveon_id
            )
            return university

    # 4. By name across all name fields — DB case-insensitive first, then accent/whitespace fallback
    if transformed_data.partner_university_name:
        name = transformed_data.partner_university_name.strip()
        university = PartnerUniversity.objects.filter(
            Q(name__iexact=name)
            | Q(short_name__iexact=name)
            | Q(translated_name__iexact=name)
        ).first()
        if university is None:
            name_norm = normalize_for_comparison(name)
            university = next(
                (
                    u
                    for u in PartnerUniversity.objects.only(
                        "id", "name", "short_name", "translated_name", "moveon_id"
                    )
                    if any(
                        normalize_for_comparison(v) == name_norm
                        for v in [u.name, u.short_name, u.translated_name]
                        if v
                    )
                ),
                None,
            )
        if university is not None:
            _backfill_university_moveon_id(
                university, transformed_data.partner_university_moveon_id
            )
            return university

    # 5. Reuse the university of an already-corrected agreement with the same moveon_id
    if transformed_data.moveon_id:
        try:
            return Agreement.objects.get(
                moveon_id=transformed_data.moveon_id
            ).partner_university
        except Agreement.DoesNotExist:
            pass

    raise ValueError(
        "Université partenaire introuvable dans le référentiel. "
        "Cliquez sur « Corriger » pour sélectionner l'université correspondante."
    )


def _backfill_university_moveon_id(
    university: PartnerUniversity, moveon_id: int | None
) -> None:
    if moveon_id and not university.moveon_id:
        university.moveon_id = moveon_id
        university.save(update_fields=["moveon_id", "updated_at"])


def _resolve_mobility_category(category_name: str) -> MobilityCategory | None:
    name = (category_name or "").strip()
    if not name:
        return None
    return MobilityCategory.objects.filter(name__iexact=name).first()


def _sync_departments(agreement: Agreement, tokens: tuple[str, ...]) -> None:
    if not tokens:
        return
    departments: list[Department] = []
    seen: set[int] = set()
    for token in tokens:
        dept = _resolve_department(token)
        if dept and dept.id not in seen:
            departments.append(dept)
            seen.add(dept.id)
            continue
        if dept is None:
            RawImport.objects.create(
                source="moveon_agreement",
                source_file="",
                entity=RawImportEntity.AGREEMENT,
                external_id=f"{agreement.moveon_id or agreement.id}:{token}",
                payload={"agreement_id": agreement.id, "value": token},
                status=RawImportStatus.FAILED,
                error_message=(
                    f"Département « {token} » introuvable dans le référentiel. "
                    "Ajoutez ce code département dans Référentiels > Départements, "
                    "puis relancez la synchronisation."
                ),
            )
    for dept in departments:
        AgreementDepartment.objects.get_or_create(agreement=agreement, department=dept)


def _sync_levels(agreement: Agreement, tokens: tuple[str, ...]) -> None:
    if not tokens:
        return
    levels = [_get_or_create_level(t) for t in tokens]
    agreement.levels.set(levels)


def _resolve_department(token: str) -> Department | None:
    key = token.strip()
    if not key:
        return None
    return (
        Department.objects.filter(code__iexact=key).first()
        or Department.objects.filter(name__iexact=key).first()
    )


def _get_or_create_level(token: str) -> Level:
    code = "-".join(token.strip().upper().split())[:50]
    level, _ = Level.objects.update_or_create(
        code=code, defaults={"name": token.strip()}
    )
    return level
