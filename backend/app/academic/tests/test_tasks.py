from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from app.academic.models import AcademicYear
from app.academic.tasks import (
    auto_advance_consolidation_to_pre_assignment,
    auto_advance_recommendation_to_consolidation,
)


def _make_year(label, status, **date_kwargs):
    today = timezone.now().date()
    year = AcademicYear.objects.create(
        label=label,
        start_date=today - timedelta(days=60),
        end_date=today + timedelta(days=305),
        **date_kwargs,
    )
    AcademicYear.objects.filter(pk=year.pk).update(status=status)
    return AcademicYear.objects.get(pk=year.pk)


@pytest.mark.django_db
class TestAutoAdvanceRecommendationToConsolidation:
    def test_advances_when_wishes_open_date_reached(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "recommendation",
            wishes_open_date=today,
            wishes_close_date=today + timedelta(days=30),
        )

        auto_advance_recommendation_to_consolidation()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.CONSOLIDATION

    def test_does_not_advance_when_wishes_open_date_in_future(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "recommendation",
            wishes_open_date=today + timedelta(days=1),
            wishes_close_date=today + timedelta(days=30),
        )

        auto_advance_recommendation_to_consolidation()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.RECOMMENDATION

    def test_skips_years_not_in_recommendation(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "initialization",
            wishes_open_date=today - timedelta(days=1),
            wishes_close_date=today + timedelta(days=30),
        )

        auto_advance_recommendation_to_consolidation()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.INITIALIZATION


@pytest.mark.django_db
class TestAutoAdvanceConsolidationToPreAssignment:
    def test_advances_and_enqueues_gale_shapley_when_wishes_closed(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "consolidation",
            wishes_open_date=today - timedelta(days=30),
            wishes_close_date=today,
        )

        with patch("app.academic.tasks.enqueue_gale_shapley") as mock_enqueue:
            auto_advance_consolidation_to_pre_assignment()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.PRE_ASSIGNMENT
        mock_enqueue.assert_called_once_with(year.pk, triggered_by="auto")

    def test_does_not_advance_when_wishes_close_date_in_future(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "consolidation",
            wishes_open_date=today - timedelta(days=30),
            wishes_close_date=today + timedelta(days=1),
        )

        with patch("app.academic.tasks.enqueue_gale_shapley") as mock_enqueue:
            auto_advance_consolidation_to_pre_assignment()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.CONSOLIDATION
        mock_enqueue.assert_not_called()
