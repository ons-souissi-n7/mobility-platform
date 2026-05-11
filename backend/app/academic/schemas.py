from datetime import date, datetime

from ninja import Schema


class AcademicYearIn(Schema):
    label: str
    start_date: date
    end_date: date
    wishes_open_date: date | None = None
    wishes_close_date: date | None = None
    gpa_freeze_date: date | None = None
    results_publication_date: date | None = None


class AcademicYearOut(Schema):
    id: int
    label: str
    start_date: date
    end_date: date
    status: str
    wishes_open_date: date | None
    wishes_close_date: date | None
    gpa_freeze_date: date | None
    results_publication_date: date | None
    created_at: datetime
    updated_at: datetime
