from io import BytesIO

import openpyxl
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from openpyxl.styles import Alignment, Font, PatternFill

from app.academic.api import get_academic_year
from app.audit.logger import log_action
from app.imports.models import (
    ImportReport as DbImportReport,
)
from app.imports.models import (
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Department, Level

from .models import AnnualEnrollment, Student, StudentWish
from .schemas import (
    AgreementWishOut,
    CrossStatOut,
    DepartmentStatOut,
    ImportReportOut,
    LevelStatOut,
    ParcoursStatOut,
    StudentDetailOut,
    StudentEnrollmentOut,
    StudentOut,
    StudentRawImportOut,
    StudentStatsOut,
    StudentWishesOut,
    WishSyncReportOut,
)
from .services.adapters import excel as excel_adapter
from .services.adapters import pegase as pegase_adapter
from .services.etl import import_students
from .services.sync_moveon_wishes import sync_moveon_wishes

router = Router()


@router.get("/students/", response=list[StudentOut], summary="Liste des etudiants")
def list_students(
    request,
    academic_year_id: int | None = None,
    department_id: int | None = None,
):
    qs = Student.objects.all()
    if academic_year_id:
        qs = qs.filter(enrollments__academic_year_id=academic_year_id)
    if department_id:
        qs = qs.filter(enrollments__department_id=department_id)
    return qs.distinct()


@router.get(
    "/students/stats/",
    response=StudentStatsOut,
    summary="Statistiques etudiants par annee",
)
def get_student_stats(request, academic_year_id: int):
    base = AnnualEnrollment.objects.filter(academic_year_id=academic_year_id)
    total = base.count()

    by_level = [
        LevelStatOut(
            level_id=item["level__id"],
            level_code=item["level__code"],
            level_name=item["level__name"],
            count=item["count"],
        )
        for item in base.values("level__id", "level__code", "level__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    ]

    by_department = [
        DepartmentStatOut(
            department_id=item["department__id"],
            department_code=item["department__code"],
            department_name=item["department__name"],
            count=item["count"],
        )
        for item in base.values(
            "department__id", "department__code", "department__name"
        )
        .annotate(count=Count("id"))
        .order_by("-count")
    ]

    by_parcours = [
        ParcoursStatOut(
            parcours_id=item["parcours__id"],
            parcours_code=item["parcours__code"],
            parcours_label=item["parcours__label"],
            count=item["count"],
        )
        for item in base.values("parcours__id", "parcours__code", "parcours__label")
        .annotate(count=Count("id"))
        .order_by("-count")
    ]

    cross = [
        CrossStatOut(
            level_id=item["level__id"],
            level_code=item["level__code"],
            level_name=item["level__name"],
            department_id=item["department__id"],
            department_code=item["department__code"],
            department_name=item["department__name"],
            parcours_id=item["parcours__id"],
            parcours_code=item["parcours__code"],
            parcours_label=item["parcours__label"],
            count=item["count"],
        )
        for item in base.values(
            "level__id",
            "level__code",
            "level__name",
            "department__id",
            "department__code",
            "department__name",
            "parcours__id",
            "parcours__code",
            "parcours__label",
        )
        .annotate(count=Count("id"))
        .order_by("level__code", "department__code", "parcours__code")
    ]

    return StudentStatsOut(
        total=total,
        by_level=by_level,
        by_department=by_department,
        by_parcours=by_parcours,
        cross=cross,
    )


@router.get("/students/template/", summary="Telecharger le template Excel etudiants")
def download_student_template(request):
    from app.reference.models import Parcours as ParcourModel

    dept_codes = list(
        Department.objects.filter(code__gt="")
        .values_list("code", flat=True)
        .order_by("code")
    )
    level_codes = list(
        Level.objects.filter(code__gt="")
        .values_list("code", flat=True)
        .order_by("code")
    )
    parcours_codes = list(
        ParcourModel.objects.values_list("code", flat=True).order_by("code").distinct()
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Etudiants"

    headers = [
        "INE",
        "Nom",
        "Prénom",
        "Email",
        "Genre",
        "Département",
        "Niveau",
        "Parcours",
        "GPA",
    ]
    header_fill = PatternFill(
        start_color="1E3A8A", end_color="1E3A8A", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center")

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align

    ws.row_dimensions[1].height = 30
    for col, width in zip(
        "ABCDEFGHI", [15, 20, 20, 35, 10, 15, 12, 20, 10], strict=False
    ):
        ws.column_dimensions[col].width = width

    # Genre dropdown (column E) — inline list (short enough)
    dv_genre = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"M,F"',
        allow_blank=True,
        showDropDown=False,
    )
    dv_genre.sqref = "E2:E10000"
    ws.add_data_validation(dv_genre)

    # Département dropdown (column F)
    if dept_codes:
        dept_ws = wb.create_sheet("_Departements")
        for i, code in enumerate(dept_codes, 1):
            dept_ws.cell(row=i, column=1, value=code)
        dept_ws.sheet_state = "hidden"
        dv_dept = openpyxl.worksheet.datavalidation.DataValidation(
            type="list",
            formula1=f"_Departements!$A$1:$A${len(dept_codes)}",
            allow_blank=True,
        )
        dv_dept.sqref = "F2:F10000"
        ws.add_data_validation(dv_dept)

    # Niveau dropdown (column G)
    if level_codes:
        level_ws = wb.create_sheet("_Niveaux")
        for i, code in enumerate(level_codes, 1):
            level_ws.cell(row=i, column=1, value=code)
        level_ws.sheet_state = "hidden"
        dv_level = openpyxl.worksheet.datavalidation.DataValidation(
            type="list",
            formula1=f"_Niveaux!$A$1:$A${len(level_codes)}",
            allow_blank=True,
        )
        dv_level.sqref = "G2:G10000"
        ws.add_data_validation(dv_level)

    # Parcours dropdown (column H)
    if parcours_codes:
        parcours_ws = wb.create_sheet("_Parcours")
        for i, code in enumerate(parcours_codes, 1):
            parcours_ws.cell(row=i, column=1, value=code)
        parcours_ws.sheet_state = "hidden"
        dv_parcours = openpyxl.worksheet.datavalidation.DataValidation(
            type="list",
            formula1=f"_Parcours!$A$1:$A${len(parcours_codes)}",
            allow_blank=True,
        )
        dv_parcours.sqref = "H2:H10000"
        ws.add_data_validation(dv_parcours)

    # Example rows
    ws.append(
        [
            "123456789AB",
            "MARTIN",
            "Jean",
            "jean.martin@etud.n7.fr",
            "M",
            dept_codes[0] if dept_codes else "INFO",
            level_codes[0] if level_codes else "3A",
            parcours_codes[0] if parcours_codes else "SESG",
            15.5,
        ]
    )
    ws.append(
        [
            "987654321CD",
            "DUPONT",
            "Marie",
            "marie.dupont@etud.n7.fr",
            "F",
            dept_codes[1]
            if len(dept_codes) > 1
            else (dept_codes[0] if dept_codes else "TC"),
            level_codes[1]
            if len(level_codes) > 1
            else (level_codes[0] if level_codes else "4A"),
            parcours_codes[1]
            if len(parcours_codes) > 1
            else (parcours_codes[0] if parcours_codes else "IPA"),
            16.0,
        ]
    )

    # Instructions sheet
    info_ws = wb.create_sheet("Instructions")
    info_ws.column_dimensions["A"].width = 80
    instructions = [
        "INSTRUCTIONS IMPORT ETUDIANTS",
        "",
        "- Remplissez les donnees a partir de la ligne 2 (la ligne 1 est l'en-tete).",
        "- INE : identifiant national etudiant, 11 caracteres.",
        "- Genre : choisissez M (Homme) ou F (Femme) dans la liste deroulante.",
        "- Departement : choisissez dans la liste deroulante (codes de la base de donnees).",
        "- Niveau : choisissez dans la liste deroulante.",
        "- Parcours : choisissez dans la liste deroulante, ou laissez vide (tronc commun).",
        "- GPA : note moyenne sur 20, format decimal (ex : 15.5). Facultatif.",
        "",
        "Les lignes sans INE sont ignorees.",
        "Les departements ou niveaux introuvables en base sont signales dans le rapport d'import.",
    ]
    for i, line in enumerate(instructions, 1):
        cell = info_ws.cell(row=i, column=1, value=line)
        if i == 1:
            cell.font = Font(bold=True, size=12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="template_etudiants.xlsx"'
    return response


@router.get(
    "/students/by-year/{year_id}/",
    response=list[StudentEnrollmentOut],
    summary="Etudiants inscrits pour une annee avec details d'inscription",
)
def list_students_by_year(request, year_id: int):
    enrollments = (
        AnnualEnrollment.objects.filter(academic_year_id=year_id)
        .select_related(
            "student", "student__nationality", "department", "level", "parcours"
        )
        .order_by("student__last_name", "student__first_name")
    )
    return [
        StudentEnrollmentOut(
            student_id=e.student.id,
            ine=e.student.ine,
            first_name=e.student.first_name,
            last_name=e.student.last_name,
            email=e.student.email,
            gender=e.student.gender,
            nationality_iso2=e.student.nationality.iso2
            if e.student.nationality_id
            else None,
            nationality_name_fr=e.student.nationality.name_fr
            if e.student.nationality_id
            else None,
            department_id=e.department.id,
            department_code=e.department.code,
            department_name=e.department.name,
            level_id=e.level.id,
            level_code=e.level.code,
            level_name=e.level.name,
            parcours_id=e.parcours.id if e.parcours else None,
            parcours_code=e.parcours.code if e.parcours else None,
            parcours_label=e.parcours.label if e.parcours else None,
            gpa=e.gpa,
        )
        for e in enrollments
    ]


@router.get(
    "/students/import-errors/",
    response=list[StudentRawImportOut],
    summary="Erreurs d'import étudiants (Pégase ou Excel)",
)
def list_student_import_errors(request):
    raw_imports = RawImport.objects.filter(entity=RawImportEntity.STUDENT).order_by(
        "-created_at"
    )
    latest: dict = {}
    for ri in raw_imports:
        key = ri.external_id or f"raw-{ri.id}"
        if key not in latest:
            latest[key] = ri
    return [ri for ri in latest.values() if ri.status == RawImportStatus.FAILED]


@router.put(
    "/students/import-errors/{raw_import_id}/ignore/",
    response=StudentRawImportOut,
    summary="Marquer une erreur d'import étudiant comme traitée",
)
def ignore_student_import_error(request, raw_import_id: int):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.STUDENT,
            status=RawImportStatus.FAILED,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import étudiant introuvable.") from exc

    raw_import.status = RawImportStatus.IGNORED
    raw_import.error_message = (
        f"{raw_import.error_message}\nTraité manuellement par l'administrateur."
    ).strip()
    raw_import.save(update_fields=["status", "error_message", "updated_at"])
    return raw_import


@router.get(
    "/students/{student_id}/",
    response=StudentDetailOut,
    summary="Detail d'un etudiant",
)
def get_student(request, student_id: int):
    try:
        return (
            Student.objects.prefetch_related(
                Prefetch(
                    "enrollments",
                    queryset=AnnualEnrollment.objects.select_related(
                        "academic_year", "department", "level", "parcours"
                    ).order_by("-academic_year__start_date"),
                )
            )
            .select_related("nationality")
            .get(pk=student_id)
        )
    except Student.DoesNotExist as exc:
        raise HttpError(404, "Etudiant introuvable.") from exc


@router.post(
    "/students/sync-pegase/{year_id}/",
    response=ImportReportOut,
    summary="Synchroniser les etudiants depuis Pegase",
)
def sync_from_pegase(request, year_id: int):
    academic_year = get_academic_year(year_id)
    rows = pegase_adapter.fetch_enrollments(academic_year.label)
    db_report = DbImportReport.objects.create(
        source=ImportSource.PEGASE,
        academic_year=academic_year,
        triggered_by=getattr(request.user, "username", ""),
    )
    report = import_students(rows, academic_year, db_report=db_report, source_file="")
    db_report.finalize()
    log_action(
        request,
        action="sync_pegase_students",
        detail=f"Année {academic_year.label} — {report.created} créés, {report.updated} mis à jour, {len(report.unresolved)} non résolus",
    )
    return report


@router.post(
    "/students/import-excel/{year_id}/",
    response=ImportReportOut,
    summary="Importer les etudiants depuis un fichier Excel",
)
def import_from_excel(request, year_id: int, file: UploadedFile = File(...)):  # noqa: B008
    academic_year = get_academic_year(year_id)
    rows = excel_adapter.parse(file.read())
    db_report = DbImportReport.objects.create(
        source=ImportSource.EXCEL,
        academic_year=academic_year,
        triggered_by=getattr(request.user, "username", ""),
    )
    report = import_students(
        rows, academic_year, db_report=db_report, source_file=file.name
    )
    db_report.finalize()
    log_action(
        request,
        action="import_excel_students",
        detail=f"Fichier {file.name} — Année {academic_year.label} — {report.created} créés, {report.updated} mis à jour, {len(report.unresolved)} non résolus",
    )
    return report


# ── Vœux étudiants ─────────────────────────────────────────────────────────


@router.post(
    "/students/wishes/sync-moveon/{year_id}/",
    response=WishSyncReportOut,
    summary="Synchroniser les vœux étudiants depuis MoveON",
)
def sync_wishes_from_moveon(request, year_id: int):
    academic_year = get_academic_year(year_id)
    report = sync_moveon_wishes(
        academic_year=academic_year,
        triggered_by=getattr(request.user, "username", ""),
    )
    log_action(
        request,
        action="sync_moveon_wishes",
        detail=(
            f"Année {academic_year.label} — "
            f"{report.created} créés, {report.updated} mis à jour, "
            f"{len(report.unresolved)} non résolus"
        ),
    )
    return report


@router.get(
    "/students/wishes/by-year/{year_id}/",
    response=list[StudentWishesOut],
    summary="Vœux ordonnés par étudiant pour une année",
)
def list_wishes_by_year(request, year_id: int):
    academic_year = get_academic_year(year_id)

    wishes = (
        StudentWish.objects.filter(annual_enrollment__academic_year=academic_year)
        .select_related(
            "annual_enrollment__student",
            "annual_enrollment__department",
            "annual_enrollment__parcours",
            "agreement__partner_university",
        )
        .order_by(
            "annual_enrollment__student__last_name",
            "annual_enrollment__student__first_name",
            "rank",
        )
    )

    grouped: dict[int, StudentWishesOut] = {}
    for w in wishes:
        enrollment = w.annual_enrollment
        student = enrollment.student
        sid = student.id
        if sid not in grouped:
            grouped[sid] = StudentWishesOut(
                student_id=sid,
                ine=student.ine,
                first_name=student.first_name,
                last_name=student.last_name,
                department_code=enrollment.department.code,
                parcours_code=enrollment.parcours.code
                if enrollment.parcours_id
                else None,
                gpa=enrollment.gpa,
                wishes=[],
            )
        grouped[sid].wishes.append(
            AgreementWishOut(
                rank=w.rank,
                agreement_id=w.agreement_id,
                moveon_id=w.agreement.moveon_id,
                agreement_name=w.agreement.name,
                university_name=w.agreement.partner_university.name,
                direction=w.agreement.direction,
            )
        )

    return list(grouped.values())


@router.get(
    "/students/{student_id}/wishes/{year_id}/",
    response=StudentWishesOut,
    summary="Vœux d'un étudiant pour une année",
)
def get_student_wishes(request, student_id: int, year_id: int):
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist as exc:
        raise HttpError(404, "Étudiant introuvable.") from exc

    academic_year = get_academic_year(year_id)

    enrollment = (
        AnnualEnrollment.objects.filter(student=student, academic_year=academic_year)
        .select_related("department", "parcours")
        .first()
    )

    wishes = (
        (
            StudentWish.objects.filter(annual_enrollment=enrollment)
            .select_related("agreement", "agreement__partner_university")
            .order_by("rank")
        )
        if enrollment
        else StudentWish.objects.none()
    )

    return StudentWishesOut(
        student_id=student.id,
        ine=student.ine,
        first_name=student.first_name,
        last_name=student.last_name,
        department_code=enrollment.department.code if enrollment else None,
        parcours_code=enrollment.parcours.code
        if enrollment and enrollment.parcours_id
        else None,
        gpa=enrollment.gpa if enrollment else None,
        wishes=[
            AgreementWishOut(
                rank=w.rank,
                agreement_id=w.agreement_id,
                moveon_id=w.agreement.moveon_id,
                agreement_name=w.agreement.name,
                university_name=w.agreement.partner_university.name,
                direction=w.agreement.direction,
            )
            for w in wishes
        ],
    )
