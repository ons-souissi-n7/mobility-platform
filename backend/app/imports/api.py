from ninja import Router
from ninja.errors import HttpError

from .models import ImportReport
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
    Retourne la liste des sessions d'import triées de la plus récente à la plus ancienne.
    Filtres optionnels : source (ex. moveon_accords) et academic_year_id.
    """
    qs = ImportReport.objects.select_related("academic_year").order_by("-created_at")

    if source:
        qs = qs.filter(source=source)
    if academic_year_id:
        qs = qs.filter(academic_year_id=academic_year_id)

    return qs


@router.get(
    "/{report_id}/",
    response=ImportReportOut,
    summary="Détail d'un rapport d'import (avec les erreurs)",
)
def get_import_report(request, report_id: int):
    """
    Retourne un rapport d'import complet avec le détail de toutes les erreurs
    et le motif de rejet pour chaque enregistrement.
    """
    return _get_report_or_404(report_id)


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

    # Un rapport par source (le plus récent)
    seen: set[str] = set()
    result = []
    for report in qs:
        if report.source not in seen:
            seen.add(report.source)
            result.append(report)

    return result
