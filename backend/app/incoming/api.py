from __future__ import annotations

from django.db.models import Count, Max, Q
from django.http import HttpResponse
from django.utils import timezone
from ninja import File, Query, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile

from app.academic.models import AcademicYear
from app.audit.logger import log_action
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.shared.api_helpers import (
    PagedResponse,
    PaginationQuery,
    get_or_404,
    paginate,
    save_validated,
)

from .models import IncomingStudent
from .schemas import IncomingImportErrorOut, IncomingStudentIn, IncomingStudentOut
from .services.date_utils import _parse_date
from .tasks import enqueue_import_excel_incoming

router = Router()

ACADEMIC_YEAR_NOT_FOUND = "Année introuvable."
IMPORT_ERROR_NOT_FOUND = "Erreur d'import introuvable."


# ──────────────────────────────────────────────  # NOSONAR (S125) — séparateur de section, pas du code
# List / CRUD
# ──────────────────────────────────────────────


@router.get(
    "/",
    response=PagedResponse[IncomingStudentOut],
    summary="Liste des étudiants entrants",
)
def list_incoming_students(
    request,
    year_id: int | None = None,
    country_id: int | None = None,
    department_id: int | None = None,
    level_id: int | None = None,
    parcours_id: int | None = None,
    mobility_category_id: int | None = None,
    university_id: int | None = None,
    search: str | None = None,
    pagination: PaginationQuery = Query(),
):
    qs = IncomingStudent.objects.select_related(
        "academic_year",
        "department",
        "country",
        "origin_university",
        "mobility_category",
        "level",
        "parcours",
    ).order_by("-academic_year__start_date", "last_name", "first_name")

    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    if country_id:
        qs = qs.filter(country_id=country_id)
    if department_id:
        qs = qs.filter(department_id=department_id)
    if level_id:
        qs = qs.filter(level_id=level_id)
    if parcours_id:
        qs = qs.filter(parcours_id=parcours_id)
    if mobility_category_id:
        qs = qs.filter(mobility_category_id=mobility_category_id)
    if university_id:
        qs = qs.filter(origin_university_id=university_id)
    if search:
        qs = qs.filter(
            Q(last_name__icontains=search)
            | Q(first_name__icontains=search)
            | Q(origin_university_name__icontains=search)
            | Q(n7_email__icontains=search)
            | Q(personal_email__icontains=search)
        )

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        results=items,
    )


@router.post(
    "/", response={201: IncomingStudentOut}, summary="Créer un étudiant entrant"
)
def create_incoming_student(request, payload: IncomingStudentIn):
    student = IncomingStudent(**payload.model_dump())
    saved = save_validated(student)
    return 201, IncomingStudent.objects.select_related(
        "academic_year",
        "department",
        "country",
        "origin_university",
        "mobility_category",
        "level",
        "parcours",
    ).get(pk=saved.pk)


# ──────────────────────────────────────────────
# Import Excel
# ──────────────────────────────────────────────


@router.post("/import/", response={202: dict}, summary="Importer depuis Excel")
def import_incoming_excel(request, year_id: int, file: UploadedFile = File(...)):
    if not (file.name or "").lower().endswith((".xlsx", ".xls")):
        raise HttpError(400, "Seuls les fichiers .xlsx et .xls sont acceptés.")
    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HttpError(400, "Fichier trop volumineux (max 5 Mo).")
    academic_year = get_or_404(AcademicYear, year_id, ACADEMIC_YEAR_NOT_FOUND)
    task_id = enqueue_import_excel_incoming(
        academic_year.pk, file_bytes, file.name or "upload.xlsx"
    )
    log_action(
        request,
        action="import_excel_incoming",
        detail=f"Fichier {file.name} — Tâche {task_id} lancée",
    )
    return 202, {"task_id": task_id, "message": "Import Excel lancé en arrière-plan."}


# ──────────────────────────────────────────────  # NOSONAR (S125) — séparateur de section, pas du code
# Template & Export
# ──────────────────────────────────────────────


@router.get("/template/", summary="Télécharger le gabarit Excel")
def download_incoming_template(request, year_id: int):
    from .services.excel_template import generate_incoming_template

    academic_year = get_or_404(AcademicYear, year_id, ACADEMIC_YEAR_NOT_FOUND)
    file_bytes = generate_incoming_template()
    label_slug = academic_year.label.replace("/", "-")
    response = HttpResponse(
        file_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="template_entrants_{label_slug}.xlsx"'
    )
    return response


@router.get("/export/", summary="Exporter les étudiants entrants en Excel")
def export_incoming_excel(
    request,
    year_id: int | None = None,
    country_id: int | None = None,
    department_id: int | None = None,
):
    import openpyxl

    from app.shared.excel_utils import (
        build_filename,
        workbook_response,
        write_header_row,
    )

    qs = IncomingStudent.objects.select_related(
        "academic_year",
        "department",
        "country",
        "origin_university",
        "mobility_category",
        "level",
        "parcours",
    ).order_by("-academic_year__start_date", "last_name", "first_name")
    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    if country_id:
        qs = qs.filter(country_id=country_id)
    if department_id:
        qs = qs.filter(department_id=department_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Etudiants entrants"

    headers = [
        "Département N7",
        "Civilité",
        "Nom",
        "Prénom",
        "Pays",
        "Université d'origine",
        "Date naissance",
        "Cadre",
        "Email personnel",
        "Email ENSEEIHT",
        "Durée",
        "Niveau",
        "Parcours",
        "Remarques",
        "Stage",
        "Diplôme",
        "Poursuite doctorat",
    ]
    widths = [14, 8, 22, 22, 20, 40, 14, 22, 35, 35, 12, 14, 18, 28, 28, 28, 16]
    write_header_row(ws, headers, widths)

    for s in qs:
        ws.append(
            [
                s.department.code if s.department_id else "",
                s.civility,
                s.last_name,
                s.first_name,
                s.country.name_fr if s.country_id else "",
                s.origin_university_name,
                s.birth_date.isoformat() if s.birth_date else "",
                s.mobility_category.name if s.mobility_category_id else "",
                s.personal_email,
                s.n7_email,
                s.duration,
                s.level.code if s.level_id else "",
                s.parcours.code if s.parcours_id else "",
                s.remarks,
                s.internship_info,
                s.diploma_info,
                "Oui" if s.doctoral_continuation else "Non",
            ]
        )

    year_obj = AcademicYear.objects.filter(pk=year_id).first() if year_id else None
    year_slug = year_obj.label.replace("/", "-") if year_obj else ""
    filename = build_filename("entrants", year_slug)
    return workbook_response(wb, filename)


# ──────────────────────────────────────────────  # NOSONAR (S125) — séparateur de section, pas du code
# Statistics
# ──────────────────────────────────────────────


@router.get(
    "/stats/univ/",
    response=list[dict],
    summary="Stats : université × département × année",
)
def stats_by_university(request, year_id: int | None = None):
    qs = IncomingStudent.objects.select_related("academic_year", "department")
    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    rows = (
        qs.values(
            "origin_university_name",
            "department__code",
            "department__name",
            "academic_year__label",
        )
        .annotate(count=Count("id"))
        .order_by("origin_university_name", "department__code", "academic_year__label")
    )
    return [
        {
            "university": r["origin_university_name"] or "—",
            "department_code": r["department__code"],
            "department_name": r["department__name"],
            "academic_year_label": r["academic_year__label"],
            "count": r["count"],
        }
        for r in rows
    ]


@router.get(
    "/stats/country/", response=list[dict], summary="Stats : pays × département × année"
)
def stats_by_country(request, year_id: int | None = None):
    qs = IncomingStudent.objects.select_related(
        "academic_year", "department", "country"
    )
    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    rows = (
        qs.values(
            "country__name_fr",
            "department__code",
            "department__name",
            "academic_year__label",
        )
        .annotate(count=Count("id"))
        .order_by("country__name_fr", "department__code", "academic_year__label")
    )
    return [
        {
            "country": r["country__name_fr"] or "—",
            "department_code": r["department__code"],
            "department_name": r["department__name"],
            "academic_year_label": r["academic_year__label"],
            "count": r["count"],
        }
        for r in rows
    ]


# ──────────────────────────────────────────────
# Import errors
# ──────────────────────────────────────────────


@router.get(
    "/import-errors/",
    response=PagedResponse[IncomingImportErrorOut],
    summary="Liste des erreurs d'import",
)
def list_incoming_import_errors(
    request,
    year_id: int | None = None,
    pagination: PaginationQuery = Query(),
):
    base = RawImport.objects.filter(entity=RawImportEntity.INCOMING_STUDENT)
    if year_id is not None:
        base = base.filter(academic_year_id=year_id)
    latest_ids = (
        base.values("external_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    qs = RawImport.objects.filter(
        id__in=latest_ids,
        status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
    ).order_by("-created_at")

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        results=items,
    )


@router.post(
    "/import-errors/{raw_import_id}/ignore/",
    response=IncomingImportErrorOut,
    summary="Ignorer une erreur d'import",
)
def ignore_incoming_import_error(request, raw_import_id: int):
    raw = get_or_404(RawImport, raw_import_id, IMPORT_ERROR_NOT_FOUND)
    now = timezone.now()
    RawImport.objects.filter(
        source=raw.source,
        external_id=raw.external_id,
    ).exclude(status=RawImportStatus.IGNORED).update(
        status=RawImportStatus.IGNORED,
        updated_at=now,
    )
    raw.refresh_from_db()
    return raw


class IncomingForcePayload(Schema):
    payload: dict


@router.post(
    "/import-errors/{raw_import_id}/force/",
    response=IncomingImportErrorOut,
    summary="Forcer l'import d'un enregistrement avec payload corrigé",
)
def force_incoming_import_error(
    request, raw_import_id: int, body: IncomingForcePayload
):
    from app.institutions.models import PartnerUniversity
    from app.mobility.models import MobilityCategory
    from app.reference.models import Country, Department, Level, Parcours

    raw = get_or_404(RawImport, raw_import_id, IMPORT_ERROR_NOT_FOUND)
    academic_year = get_or_404(
        AcademicYear, raw.academic_year_id, ACADEMIC_YEAR_NOT_FOUND
    )

    p = body.payload

    def _str(k):
        return str(p.get(k) or "").strip()

    last_name = _str("NOM")
    first_name = _str("PRENOM")
    if not last_name or not first_name:
        raise HttpError(400, "Nom et prénom sont obligatoires.")

    country_name = _str("PAYS")
    dept_code = _str("DEPARTEMENT")
    univ_name = _str("UNIV ORIGINE")
    cat_name = _str("CADRE")
    level_code = _str("ANNEE")
    parcours_code = _str("PARCOURS")
    doctoral_raw = _str("POURSUITE DOCTORAT").lower()

    country = (
        Country.objects.filter(name_fr__iexact=country_name).first()
        if country_name
        else None
    )
    department = (
        Department.objects.filter(code__iexact=dept_code).first() if dept_code else None
    )
    origin_university = (
        PartnerUniversity.objects.filter(name__iexact=univ_name).first()
        or PartnerUniversity.objects.filter(short_name__iexact=univ_name).first()
        if univ_name
        else None
    )
    mobility_category = (
        MobilityCategory.objects.filter(name__iexact=cat_name).first()
        if cat_name
        else None
    )
    level = (
        Level.objects.filter(code__iexact=level_code).first() if level_code else None
    )
    parcours = (
        Parcours.objects.filter(code__iexact=parcours_code).first()
        if parcours_code
        else None
    )

    birth_date = _parse_date(_str("DATE NAISSANCE"))
    doctoral_continuation = doctoral_raw in ("o", "oui", "yes", "1", "true", "vrai")
    defaults = {
        "department": department,
        "civility": _str("CIVILITE"),
        "country": country,
        "origin_university": origin_university,
        "origin_university_name": univ_name,
        "mobility_category": mobility_category,
        "personal_email": _str("MAIL"),
        "n7_email": _str("MAIL ENSEEIHT"),
        "duration": _str("DUREE"),
        "level": level,
        "parcours": parcours,
        "remarks": _str("REMARQUES"),
        "internship_info": _str("STAGE"),
        "diploma_info": _str("DIPLOME"),
        "doctoral_continuation": doctoral_continuation,
    }
    try:
        IncomingStudent.objects.update_or_create(
            academic_year=academic_year,
            last_name=last_name,
            first_name=first_name,
            birth_date=birth_date,
            defaults=defaults,
        )
    except Exception as exc:
        raise HttpError(400, str(exc)) from exc

    raw.payload = p
    raw.status = RawImportStatus.IMPORTED
    raw.error_message = ""
    raw.save(update_fields=["payload", "status", "error_message", "updated_at"])
    return raw


# ──────────────────────────────────────────────
# Detail CRUD — must be last: /{student_id}/ catches all paths not matched above
# ──────────────────────────────────────────────


@router.put(
    "/{student_id}/",
    response=IncomingStudentOut,
    summary="Modifier un étudiant entrant",
)
def update_incoming_student(request, student_id: int, payload: IncomingStudentIn):
    student = get_or_404(IncomingStudent, student_id, "Étudiant entrant introuvable.")
    for field, value in payload.model_dump().items():
        setattr(student, field, value)
    save_validated(student)
    return IncomingStudent.objects.select_related(
        "academic_year",
        "department",
        "country",
        "origin_university",
        "mobility_category",
        "level",
        "parcours",
    ).get(pk=student.pk)


@router.delete(
    "/{student_id}/", response={204: None}, summary="Supprimer un étudiant entrant"
)
def delete_incoming_student(request, student_id: int):
    student = get_or_404(IncomingStudent, student_id, "Étudiant entrant introuvable.")
    student.delete()
    return 204, None
