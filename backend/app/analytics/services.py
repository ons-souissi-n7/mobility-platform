from django.db.models import Count, OuterRef, Subquery

from app.academic.models import AcademicYear
from app.complementary.models import ComplementaryMobility, MobilityStatus
from app.incoming.models import IncomingStudent
from app.internships.models import Internship
from app.outgoing.models import Assignment, AssignmentResult
from app.students.models import AnnualEnrollment

# ── Helpers ───────────────────────────────────────────────────────────────────


def _years_context(n_years: int) -> tuple[list[int], dict[int, str]]:
    years = list(AcademicYear.objects.order_by("-start_date")[:n_years])
    years.reverse()
    year_ids = [y.id for y in years]
    year_labels = {y.id: y.label for y in years}
    return year_ids, year_labels


def _accumulate(
    mapping: dict[str, dict[int, int]], label: str, year_id: int, count: int
) -> None:
    if label not in mapping:
        mapping[label] = {}
    mapping[label][year_id] = mapping[label].get(year_id, 0) + count


def _breakdown_result(
    year_ids: list[int],
    year_labels: dict[int, str],
    label_year_map: dict[str, dict[int, int]],
    top_n: int | None = None,
) -> dict:
    if top_n:
        sorted_labels = sorted(
            label_year_map,
            key=lambda k: sum(label_year_map[k].values()),
            reverse=True,
        )[:top_n]
    else:
        sorted_labels = sorted(label_year_map)
    return {
        "years": [year_labels[yid] for yid in year_ids],
        "series": [
            {
                "label": lbl,
                "values": [label_year_map[lbl].get(yid, 0) for yid in year_ids],
            }
            for lbl in sorted_labels
        ],
    }


def _empty_breakdown(year_ids: list[int], year_labels: dict[int, str]) -> dict:
    return {"years": [year_labels[yid] for yid in year_ids], "series": []}


# ── Flux globaux ──────────────────────────────────────────────────────────────


def get_mobility_trends(n_years: int = 5) -> list[dict]:
    """Comptages globaux sur les n dernières années académiques."""
    year_ids, _ = _years_context(n_years)
    years = list(AcademicYear.objects.filter(id__in=year_ids).order_by("start_date"))

    assignments = {
        a.academic_year_id: a
        for a in Assignment.objects.filter(
            academic_year_id__in=year_ids, status="published"
        )
    }
    incoming_counts = dict(
        IncomingStudent.objects.filter(academic_year_id__in=year_ids)
        .values("academic_year_id")
        .annotate(n=Count("id"))
        .values_list("academic_year_id", "n")
    )
    internship_counts = dict(
        Internship.objects.filter(academic_year_id__in=year_ids)
        .values("academic_year_id")
        .annotate(n=Count("id"))
        .values_list("academic_year_id", "n")
    )
    complementary_counts = dict(
        ComplementaryMobility.objects.filter(
            academic_year_id__in=year_ids,
            status=MobilityStatus.VALIDATED,
        )
        .values("academic_year_id")
        .annotate(n=Count("id"))
        .values_list("academic_year_id", "n")
    )

    return [
        {
            "label": year.label,
            "outgoing": assignments[year.id].assigned_count
            if year.id in assignments
            else 0,
            "incoming": incoming_counts.get(year.id, 0),
            "internships": internship_counts.get(year.id, 0),
            "complementary": complementary_counts.get(year.id, 0),
        }
        for year in years
    ]


# ── Par département ───────────────────────────────────────────────────────────


def get_department_breakdown(
    n_years: int = 5, dept_ids: list[int] | None = None
) -> dict:
    """Retourne {outgoing, incoming, internships} ventilés par département."""
    year_ids, year_labels = _years_context(n_years)
    top_n = None  # tous les départements (peu nombreux)

    # Sortantes
    out_qs = AssignmentResult.objects.filter(
        assignment__status="published",
        assignment__academic_year_id__in=year_ids,
        agreement_year__isnull=False,
    )
    if dept_ids:
        out_qs = out_qs.filter(annual_enrollment__department_id__in=dept_ids)
    out_rows = out_qs.values(
        "assignment__academic_year_id", "annual_enrollment__department__code"
    ).annotate(n=Count("id"))

    # Entrantes
    in_qs = IncomingStudent.objects.filter(
        academic_year_id__in=year_ids, department__isnull=False
    )
    if dept_ids:
        in_qs = in_qs.filter(department_id__in=dept_ids)
    in_rows = in_qs.values("academic_year_id", "department__code").annotate(
        n=Count("id")
    )

    # Stages — lien via AnnualEnrollment (même étudiant, même année)
    dept_code_sq = Subquery(
        AnnualEnrollment.objects.filter(
            student_id=OuterRef("student_id"),
            academic_year_id=OuterRef("academic_year_id"),
        ).values("department__code")[:1]
    )
    int_qs = (
        Internship.objects.filter(academic_year_id__in=year_ids)
        .annotate(dept_code=dept_code_sq)
        .filter(dept_code__isnull=False)
    )
    if dept_ids:
        from app.reference.models import Department

        allowed = list(
            Department.objects.filter(id__in=dept_ids).values_list("code", flat=True)
        )
        int_qs = int_qs.filter(dept_code__in=allowed)
    int_rows = int_qs.values("academic_year_id", "dept_code").annotate(n=Count("id"))

    out_map: dict[str, dict[int, int]] = {}
    for row in out_rows:
        _accumulate(
            out_map,
            row["annual_enrollment__department__code"] or "N/A",
            row["assignment__academic_year_id"],
            row["n"],
        )

    in_map: dict[str, dict[int, int]] = {}
    for row in in_rows:
        _accumulate(
            in_map, row["department__code"] or "N/A", row["academic_year_id"], row["n"]
        )

    int_map: dict[str, dict[int, int]] = {}
    for row in int_rows:
        _accumulate(int_map, row["dept_code"], row["academic_year_id"], row["n"])

    return {
        "outgoing": _breakdown_result(year_ids, year_labels, out_map, top_n),
        "incoming": _breakdown_result(year_ids, year_labels, in_map, top_n),
        "internships": _breakdown_result(year_ids, year_labels, int_map, top_n),
    }


# ── Par pays ──────────────────────────────────────────────────────────────────


def get_country_breakdown(
    n_years: int = 5, country_ids: list[int] | None = None
) -> dict:
    """Retourne {outgoing, incoming, internships} ventilés par pays."""
    year_ids, year_labels = _years_context(n_years)
    top_n = None if country_ids else 10

    # Sortantes
    out_qs = AssignmentResult.objects.filter(
        assignment__status="published",
        assignment__academic_year_id__in=year_ids,
        agreement_year__isnull=False,
        agreement_year__agreement__partner_university__country__isnull=False,
    )
    if country_ids:
        out_qs = out_qs.filter(
            agreement_year__agreement__partner_university__country_id__in=country_ids
        )
    out_rows = out_qs.values(
        "assignment__academic_year_id",
        "agreement_year__agreement__partner_university__country__name_fr",
    ).annotate(n=Count("id"))

    # Entrantes
    in_qs = IncomingStudent.objects.filter(
        academic_year_id__in=year_ids, country__isnull=False
    )
    if country_ids:
        in_qs = in_qs.filter(country_id__in=country_ids)
    in_rows = in_qs.values("academic_year_id", "country__name_fr").annotate(
        n=Count("id")
    )

    # Stages
    int_qs = Internship.objects.filter(
        academic_year_id__in=year_ids, country__isnull=False
    )
    if country_ids:
        int_qs = int_qs.filter(country_id__in=country_ids)
    int_rows = int_qs.values("academic_year_id", "country__name_fr").annotate(
        n=Count("id")
    )

    out_map: dict[str, dict[int, int]] = {}
    for row in out_rows:
        _accumulate(
            out_map,
            row["agreement_year__agreement__partner_university__country__name_fr"],
            row["assignment__academic_year_id"],
            row["n"],
        )

    in_map: dict[str, dict[int, int]] = {}
    for row in in_rows:
        _accumulate(in_map, row["country__name_fr"], row["academic_year_id"], row["n"])

    int_map: dict[str, dict[int, int]] = {}
    for row in int_rows:
        _accumulate(int_map, row["country__name_fr"], row["academic_year_id"], row["n"])

    return {
        "outgoing": _breakdown_result(year_ids, year_labels, out_map, top_n),
        "incoming": _breakdown_result(year_ids, year_labels, in_map, top_n),
        "internships": _breakdown_result(year_ids, year_labels, int_map, top_n),
    }


# ── Par université ────────────────────────────────────────────────────────────


def get_university_breakdown(
    n_years: int = 5, univ_ids: list[int] | None = None
) -> dict:
    """Retourne {outgoing, incoming, internships} ventilés par université partenaire."""
    year_ids, year_labels = _years_context(n_years)
    top_n = None if univ_ids else 10

    # Sortantes
    out_qs = AssignmentResult.objects.filter(
        assignment__status="published",
        assignment__academic_year_id__in=year_ids,
        agreement_year__isnull=False,
    )
    if univ_ids:
        out_qs = out_qs.filter(
            agreement_year__agreement__partner_university_id__in=univ_ids
        )
    out_rows = out_qs.values(
        "assignment__academic_year_id",
        "agreement_year__agreement__partner_university__name",
    ).annotate(n=Count("id"))

    # Entrantes (via origin_university → PartnerUniversity)
    in_qs = IncomingStudent.objects.filter(
        academic_year_id__in=year_ids, origin_university__isnull=False
    )
    if univ_ids:
        in_qs = in_qs.filter(origin_university_id__in=univ_ids)
    in_rows = in_qs.values("academic_year_id", "origin_university__name").annotate(
        n=Count("id")
    )

    out_map: dict[str, dict[int, int]] = {}
    for row in out_rows:
        univ = row["agreement_year__agreement__partner_university__name"] or "N/A"
        _accumulate(out_map, univ, row["assignment__academic_year_id"], row["n"])

    in_map: dict[str, dict[int, int]] = {}
    for row in in_rows:
        univ = row["origin_university__name"] or "N/A"
        _accumulate(in_map, univ, row["academic_year_id"], row["n"])

    return {
        "outgoing": _breakdown_result(year_ids, year_labels, out_map, top_n),
        "incoming": _breakdown_result(year_ids, year_labels, in_map, top_n),
        "internships": _empty_breakdown(year_ids, year_labels),
    }
