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
