from __future__ import annotations

import dataclasses
from difflib import SequenceMatcher

from django.db.models import Prefetch

from app.shared.cleaning import normalize_for_comparison
from app.students.models import AnnualEnrollment, Student


@dataclasses.dataclass
class ReconciliationCandidate:
    student_id: int
    ine: str
    first_name: str
    last_name: str
    email: str
    department_code: str | None
    score: float
    confidence: str


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(
        None, normalize_for_comparison(a), normalize_for_comparison(b)
    ).ratio()


def _confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium"
    return "low"


def find_reconciliation_candidates(
    *,
    last_name: str,
    first_name: str,
    email: str = "",
    year_id: int | None = None,
    min_score: float = 0.60,
    max_results: int = 5,
) -> list[ReconciliationCandidate]:
    """Fuzzy-match a failed import payload against existing Students.

    Pre-filters by the first 3 chars of last_name for performance, then scores
    each candidate on name (80 %) and email (20 %). Returns at most max_results
    candidates whose combined score >= min_score, sorted by score descending.
    """
    if not last_name:
        return []

    qs = Student.objects.filter(last_name__icontains=last_name[:3]).only(
        "id", "ine", "first_name", "last_name", "email"
    )

    if year_id is not None:
        qs = qs.prefetch_related(
            Prefetch(
                "enrollments",
                queryset=AnnualEnrollment.objects.filter(
                    academic_year_id=year_id
                ).select_related("department"),
                to_attr="_year_enrollments",
            )
        )

    candidates: list[ReconciliationCandidate] = []

    for student in qs[:200]:
        score = (
            0.50 * _sim(last_name, student.last_name)
            + 0.30 * _sim(first_name, student.first_name)
            + 0.20 * (1.0 if email and email.lower() == student.email.lower() else 0.0)
        )

        if score < min_score:
            continue

        dept_code: str | None = None
        if year_id is not None:
            enrollments = getattr(student, "_year_enrollments", [])
            if enrollments:
                dept_code = enrollments[0].department.code

        candidates.append(
            ReconciliationCandidate(
                student_id=student.id,
                ine=student.ine,
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,
                department_code=dept_code,
                score=round(score, 2),
                confidence=_confidence(score),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:max_results]
