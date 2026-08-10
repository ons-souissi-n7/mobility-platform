from django.http import HttpResponse
from ninja import Router, Schema

router = Router()


class MobilityTrendPoint(Schema):
    label: str
    outgoing: int
    incoming: int
    internships: int
    complementary: int


class MobilityTrendsOut(Schema):
    data: list[MobilityTrendPoint]


class BreakdownSeries(Schema):
    label: str
    values: list[int]


class BreakdownOut(Schema):
    years: list[str]
    series: list[BreakdownSeries]


class BreakdownResponse(Schema):
    outgoing: BreakdownOut
    incoming: BreakdownOut
    internships: BreakdownOut


def _to_breakdown_out(data: dict) -> BreakdownOut:
    return BreakdownOut(
        years=data["years"],
        series=[BreakdownSeries(**s) for s in data["series"]],
    )


@router.get(
    "/trends/",
    response=MobilityTrendsOut,
    summary="Évolution des mobilités sur les n dernières années",
)
def get_trends(request, years: int = 5):
    from .services import get_mobility_trends

    points = [MobilityTrendPoint(**p) for p in get_mobility_trends(years)]
    return MobilityTrendsOut(data=points)


@router.get(
    "/by-department/",
    response=BreakdownResponse,
    summary="Sortantes, entrantes et stages par département sur n années",
)
def get_by_department(request, years: int = 5, dept_ids: str | None = None):
    from .services import get_department_breakdown

    ids = [int(x) for x in dept_ids.split(",")] if dept_ids else None
    data = get_department_breakdown(years, dept_ids=ids)
    return BreakdownResponse(
        outgoing=_to_breakdown_out(data["outgoing"]),
        incoming=_to_breakdown_out(data["incoming"]),
        internships=_to_breakdown_out(data["internships"]),
    )


@router.get(
    "/by-country/",
    response=BreakdownResponse,
    summary="Sortantes, entrantes et stages par pays sur n années",
)
def get_by_country(request, years: int = 5, country_ids: str | None = None):
    from .services import get_country_breakdown

    ids = [int(x) for x in country_ids.split(",")] if country_ids else None
    data = get_country_breakdown(years, country_ids=ids)
    return BreakdownResponse(
        outgoing=_to_breakdown_out(data["outgoing"]),
        incoming=_to_breakdown_out(data["incoming"]),
        internships=_to_breakdown_out(data["internships"]),
    )


@router.get(
    "/by-university/",
    response=BreakdownResponse,
    summary="Sortantes et entrantes par université partenaire sur n années",
)
def get_by_university(request, years: int = 5, univ_ids: str | None = None):
    from .services import get_university_breakdown

    ids = [int(x) for x in univ_ids.split(",")] if univ_ids else None
    data = get_university_breakdown(years, univ_ids=ids)
    return BreakdownResponse(
        outgoing=_to_breakdown_out(data["outgoing"]),
        incoming=_to_breakdown_out(data["incoming"]),
        internships=_to_breakdown_out(data["internships"]),
    )


@router.get("/export/", summary="Export Excel des statistiques de mobilité")
def export_analytics(request, years: int = 5) -> HttpResponse:
    from .services_export import generate_analytics_excel

    content = generate_analytics_excel(years)
    filename = f"statistiques_mobilite_{years}ans.xlsx"
    return HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
