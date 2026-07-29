from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router

from app.cti.schemas import CtiStatsOut, MobilityDurationOut, MobilityHistoryOut
from app.cti.services import (
    compute_cti_duration,
    get_student_mobility_history,
    refresh_cti_duration,
)
from app.students.models import Student

router = Router()


@router.get(
    "/students/{ine}/duration/",
    response=MobilityDurationOut,
    summary="Durée de mobilité d'un étudiant (calcul à la volée)",
)
def get_cti_duration(request, ine: str):
    student = get_object_or_404(Student, ine=ine)
    data = compute_cti_duration(student)
    return {"ine": ine, **data}


@router.post(
    "/students/{ine}/duration/refresh/",
    response=MobilityDurationOut,
    summary="Recalculer et persister la durée de mobilité",
)
def refresh_student_cti_duration(request, ine: str):
    student = get_object_or_404(Student, ine=ine)
    obj = refresh_cti_duration(student)
    return {
        "ine": ine,
        "exchange_weeks": float(obj.exchange_weeks),
        "internship_weeks": float(obj.internship_weeks),
        "complementary_weeks": float(obj.complementary_weeks),
        "total_weeks": float(obj.total_weeks),
    }


@router.get(
    "/students/{ine}/history/",
    response=MobilityHistoryOut,
    summary="Historique complet des mobilités d'un étudiant (admin)",
)
def get_student_history(request, ine: str):
    student = get_object_or_404(Student, ine=ine)
    return get_student_mobility_history(student)


@router.get("/stats/", response=CtiStatsOut, summary="Statistiques CTI VII.D3 (JSON)")
def get_cti_stats(request, academic_year_id: int):
    from app.academic.models import AcademicYear
    from app.cti.services_export import get_cti_stats_data

    year = get_object_or_404(AcademicYear, id=academic_year_id)
    return get_cti_stats_data(year)


@router.get("/export/", summary="Export rapport CTI (Excel VII.D3)")
def export_cti_report(request, academic_year_id: int) -> HttpResponse:
    from app.academic.models import AcademicYear
    from app.cti.services_export import generate_cti_excel

    year = get_object_or_404(AcademicYear, id=academic_year_id)
    content = generate_cti_excel(year)
    filename = f"rapport_cti_{year.label.replace('/', '-')}.xlsx"
    return HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
