from ninja import Router
from ninja.errors import HttpError

from app.shared.sync import mark_raw_import

from .models import ImportReport, RawImport, RawImportEntity, RawImportStatus
from .schemas import ImportReportListOut, ImportReportOut

router = Router()


def _get_report_or_404(report_id: int) -> ImportReport:
    try:
        return ImportReport.objects.select_related("academic_year").get(pk=report_id)
    except ImportReport.DoesNotExist as exc:
        raise HttpError(404, "Rapport d'import introuvable.") from exc


@router.get(
    "/",
    response=list[ImportReportListOut],
    summary="Liste des rapports d'import",
)
def list_import_reports(
    request, source: str | None = None, academic_year_id: int | None = None
):
    """
    Retourne la liste des sessions d'import triees de la plus recente a la plus ancienne.
    Filtres optionnels : source (ex. moveon_accords) et academic_year_id.
    """
    qs = ImportReport.objects.select_related("academic_year").order_by("-created_at")

    if source:
        qs = qs.filter(source=source)
    if academic_year_id:
        qs = qs.filter(academic_year_id=academic_year_id)

    return qs


# Route litterale declaree AVANT /{report_id}/ pour eviter le conflit de routage
@router.get(
    "/latest/",
    response=list[ImportReportListOut],
    summary="Derniers rapports par source",
)
def latest_import_reports(request, academic_year_id: int | None = None):
    """
    Retourne le dernier rapport pour chaque source (utile pour le tableau de bord).
    """
    qs = ImportReport.objects.select_related("academic_year").order_by(
        "source", "-created_at"
    )

    if academic_year_id:
        qs = qs.filter(academic_year_id=academic_year_id)

    seen: set[str] = set()
    result = []
    for report in qs:
        if report.source not in seen:
            seen.add(report.source)
            result.append(report)

    return result


@router.get(
    "/{report_id}/",
    response=ImportReportOut,
    summary="Detail d'un rapport d'import (avec les erreurs)",
)
def get_import_report(request, report_id: int):
    """
    Retourne un rapport d'import complet avec le detail de toutes les erreurs
    et le motif de rejet pour chaque enregistrement.
    """
    return _get_report_or_404(report_id)


@router.post(
    "/raw/{raw_import_id}/force-overwrite/",
    response={200: dict},
    summary="Forcer la mise a jour d'un enregistrement en conflit",
)
def force_overwrite_conflict(request, raw_import_id: int):
    """
    Re-execute l'upsert d'un RawImport en statut CONFLICT en ignorant la
    detection de conflit. L'enregistrement local sera ecrase par les donnees
    de la source externe.
    """
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id, status=RawImportStatus.CONFLICT
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Enregistrement en conflit introuvable.") from exc

    entity = raw_import.entity
    payload = raw_import.payload

    try:
        if entity == RawImportEntity.AGREEMENT:
            from app.mobility.services.sync_moveon import upsert_agreement

            upsert_agreement(payload, force_overwrite=True)
        elif entity == RawImportEntity.AGREEMENT_CATEGORY:
            from app.mobility.services.sync_moveon import upsert_mobility_category

            upsert_mobility_category(payload, force_overwrite=True)
        elif entity == RawImportEntity.DEPARTMENT:
            from app.reference.services.sync_pegase import upsert_department

            upsert_department(payload, force_overwrite=True)
        elif entity == RawImportEntity.LEVEL:
            from app.reference.services.sync_pegase_levels import _upsert_level

            _upsert_level(payload, force_overwrite=True)
        else:
            raise HttpError(
                400, f"Force-overwrite non supporte pour l'entite {entity}."
            )
    except HttpError:
        raise
    except Exception as exc:
        raise HttpError(400, str(exc)) from exc

    mark_raw_import(raw_import, RawImportStatus.IMPORTED)
    return {"status": "ok", "message": "Mise a jour forcee avec succes."}
