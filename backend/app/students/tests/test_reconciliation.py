"""Tests unitaires pour le service de réconciliation sans INE."""

from __future__ import annotations

from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.reference.models import Department, Level
from app.students.models import AnnualEnrollment, Student
from app.students.services.reconciliation import find_reconciliation_candidates


@pytest.mark.django_db
class TestFindReconciliationCandidates:
    def test_empty_last_name_returns_empty(self):
        result = find_reconciliation_candidates(last_name="", first_name="Jean")
        assert result == []

    def test_no_student_in_db_returns_empty(self):
        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")
        assert result == []

    def test_exact_name_match_found(self):
        Student.objects.create(ine="12345678901", first_name="Jean", last_name="Martin")

        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")

        assert len(result) == 1
        assert result[0].ine == "12345678901"
        assert result[0].score >= 0.60

    def test_email_exact_match_boosts_score(self):
        s_with_email = Student.objects.create(
            ine="10000000001",
            first_name="Jean",
            last_name="Martin",
            email="jean.martin@n7.fr",
        )
        Student.objects.create(
            ine="10000000002",
            first_name="Jean",
            last_name="Martin",
            email="other@n7.fr",
        )

        result = find_reconciliation_candidates(
            last_name="Martin", first_name="Jean", email="jean.martin@n7.fr"
        )

        assert len(result) == 2
        assert result[0].ine == s_with_email.ine  # score le plus haut en premier

    def test_low_score_match_excluded_by_threshold(self):
        # "Jean" vs "Xxx" tire le score sous le seuil de 0.60
        Student.objects.create(ine="12345678901", first_name="Xxx", last_name="Martini")

        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")

        assert result == []

    def test_max_results_limits_output(self):
        for i in range(10):
            Student.objects.create(
                ine=f"1000000000{i}", first_name="Jean", last_name=f"Martin{i:02d}"
            )

        result = find_reconciliation_candidates(
            last_name="Martin", first_name="Jean", min_score=0.0, max_results=3
        )

        assert len(result) <= 3

    def test_results_sorted_by_score_descending(self):
        Student.objects.create(ine="10000000001", first_name="Jean", last_name="Martin")
        Student.objects.create(ine="10000000002", first_name="Zzz", last_name="Marti")

        result = find_reconciliation_candidates(
            last_name="Martin", first_name="Jean", min_score=0.0
        )

        scores = [c.score for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_confidence_high_for_exact_name_and_email(self):
        Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="jean.martin@n7.fr",
        )

        result = find_reconciliation_candidates(
            last_name="Martin", first_name="Jean", email="jean.martin@n7.fr"
        )

        assert result[0].confidence == "high"
        assert result[0].score >= 0.85

    def test_confidence_medium_for_good_name_match(self):
        Student.objects.create(ine="12345678901", first_name="Jean", last_name="Martin")

        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")

        # score = 0.50 * 1.0 (nom) + 0.30 * 1.0 (prénom) + 0.20 * 0 = 0.80 → medium
        assert result[0].confidence in ("high", "medium")
        assert result[0].score >= 0.70

    def test_department_code_included_when_year_given(self):
        year = AcademicYear.objects.create(
            label="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 8, 31)
        )
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        student = Student.objects.create(
            ine="12345678901", first_name="Jean", last_name="Martin"
        )
        AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level
        )

        result = find_reconciliation_candidates(
            last_name="Martin", first_name="Jean", year_id=year.id
        )

        assert len(result) == 1
        assert result[0].department_code == "SN"

    def test_department_code_none_without_year(self):
        Student.objects.create(ine="12345678901", first_name="Jean", last_name="Martin")

        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")

        assert result[0].department_code is None

    def test_accent_insensitive_matching(self):
        Student.objects.create(
            ine="12345678901", first_name="Élodie", last_name="Dupéré"
        )

        result = find_reconciliation_candidates(last_name="Dupere", first_name="Elodie")

        assert len(result) == 1
        assert result[0].ine == "12345678901"

    def test_returned_candidate_fields_complete(self):
        Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="j@n7.fr",
        )

        result = find_reconciliation_candidates(last_name="Martin", first_name="Jean")

        c = result[0]
        assert c.student_id > 0
        assert c.ine == "12345678901"
        assert c.first_name == "Jean"
        assert c.last_name == "Martin"
        assert c.email == "j@n7.fr"
        assert 0.0 <= c.score <= 1.0
        assert c.confidence in ("high", "medium", "low")
