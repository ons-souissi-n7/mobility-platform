from datetime import date

from ninja import Schema


class MobilityDurationOut(Schema):
    ine: str
    exchange_weeks: float
    internship_weeks: float
    complementary_weeks: float
    total_weeks: float


# ---------------------------------------------------------------------------
# History (admin)
# ---------------------------------------------------------------------------


class MobilityTotalsOut(Schema):
    exchange_weeks: float
    internship_weeks: float
    complementary_weeks: float
    total_weeks: float


class ExchangeHistoryItem(Schema):
    academic_year: str
    institution_name: str
    country_name: str
    duration_weeks: int | None


class InternshipHistoryItem(Schema):
    academic_year: str | None
    company_name: str
    country_name: str | None
    start_date: date | None
    end_date: date | None
    weeks_in_company: int | None
    is_international: bool


class ComplementaryHistoryItem(Schema):
    id: int
    academic_year: str
    experience_type: str
    destination_country: str
    destination_institution: str | None
    start_date: date
    end_date: date
    duration_weeks: float
    status: str


class MobilityHistoryOut(Schema):
    ine: str
    totals: MobilityTotalsOut
    exchanges: list[ExchangeHistoryItem]
    internships: list[InternshipHistoryItem]
    complementary_mobilities: list[ComplementaryHistoryItem]


# ---------------------------------------------------------------------------
# Statistiques VII.D3 (admin)
# ---------------------------------------------------------------------------


class CtiMobilityRow(Schema):
    """Une ligne H / F / Total pour les tableaux échanges."""

    label: str
    lt_fise: int
    lt_fisa: int
    eq_fise: int
    eq_fisa: int
    gt_fise: int
    gt_fisa: int


class CtiInternshipRow(Schema):
    """Une ligne H / F / Total pour le tableau stages."""

    label: str
    lt_fise: int
    lt_fisa: int
    mid_fise: int
    mid_fisa: int
    gt_fise: int
    gt_fisa: int


class CtiIncomingRow(Schema):
    """Une ligne H / F / Total pour le tableau entrants."""

    label: str
    lt: int
    eq: int
    gt: int


class CtiRegionRow(Schema):
    region: str
    hommes: int
    femmes: int
    total: int


class CtiStatsOut(Schema):
    academic_year_label: str
    enrolled_fise: int
    enrolled_fisa: int
    exchanges: list[CtiMobilityRow]
    internships: list[CtiInternshipRow]
    pct_fise: float
    pct_fisa: float
    avg_months_fise: float
    avg_months_fisa: float
    incoming: list[CtiIncomingRow]
    dd_outgoing: list[CtiRegionRow]
    dd_incoming: list[CtiRegionRow]
