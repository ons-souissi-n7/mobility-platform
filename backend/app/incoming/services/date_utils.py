from __future__ import annotations

from datetime import date, datetime


def _parse_date(val) -> date | None:
    """Parse a date value from various formats.

    Accepts datetime/date objects (as returned by openpyxl for date-formatted
    cells) as well as strings in common date formats.  Returns None for empty
    or unparseable inputs.
    """
    if val is None:
        return None

    # openpyxl returns datetime or date objects for date-formatted cells
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val

    s = str(val).strip()
    if not s or s.lower() in ("none", ""):
        return None

    # Strip timezone suffix if present (e.g. "2001-03-14 00:00:00+00:00")
    if len(s) > 10 and "+" in s[10:]:
        s = s[: s.index("+", 10)]
    if s.endswith("Z"):
        s = s[:-1]

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None
