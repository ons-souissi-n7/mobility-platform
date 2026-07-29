from datetime import timedelta

import pytest
from django.utils import timezone

from app.academic.models import AcademicYear
from app.academic.tasks import (
    auto_advance_recommendation_to_candidature,
    auto_close_academic_year,
    auto_close_wishes,
    auto_create_next_academic_year,
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
class TestAutoAdvanceRecommendationToCandidature:
    def test_advances_when_wishes_open_date_reached(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "recommendation",
            wishes_open_date=today,
            wishes_close_date=today + timedelta(days=30),
        )

        auto_advance_recommendation_to_candidature()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.CANDIDATURE

    def test_does_not_advance_when_wishes_open_date_in_future(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "recommendation",
            wishes_open_date=today + timedelta(days=1),
            wishes_close_date=today + timedelta(days=30),
        )

        auto_advance_recommendation_to_candidature()

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

        auto_advance_recommendation_to_candidature()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.INITIALIZATION


@pytest.mark.django_db
class TestAutoCloseWishes:
    def test_advances_when_wishes_close_date_reached(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "candidature",
            wishes_open_date=today - timedelta(days=30),
            wishes_close_date=today,
        )

        auto_close_wishes()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.IMPORT

    def test_does_not_advance_when_wishes_close_date_in_future(self):
        today = timezone.now().date()
        year = _make_year(
            "2024-2025",
            "candidature",
            wishes_open_date=today - timedelta(days=30),
            wishes_close_date=today + timedelta(days=1),
        )

        auto_close_wishes()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.CANDIDATURE


@pytest.mark.django_db
class TestAutoCloseAcademicYear:
    def test_closes_finalization_year_when_end_date_reached(self):
        today = timezone.now().date()
        year = _make_year("TEST-CLOSE", "finalization")
        AcademicYear.objects.filter(pk=year.pk).update(end_date=today)

        auto_close_academic_year()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.CLOSED
        assert year.closed_at is not None

    def test_does_not_close_when_end_date_in_future(self):
        today = timezone.now().date()
        year = _make_year("TEST-FUTURE", "finalization")
        AcademicYear.objects.filter(pk=year.pk).update(
            end_date=today + timedelta(days=1)
        )

        auto_close_academic_year()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.FINALIZATION

    def test_does_not_close_published_year_without_cti_finalization(self):
        today = timezone.now().date()
        year = _make_year("TEST-PUB", "published")
        AcademicYear.objects.filter(pk=year.pk).update(end_date=today)

        auto_close_academic_year()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.PUBLISHED

    def test_does_not_close_year_not_in_finalization(self):
        today = timezone.now().date()
        year = _make_year("TEST-PRE", "pre_assignment")
        AcademicYear.objects.filter(pk=year.pk).update(end_date=today)

        auto_close_academic_year()

        year = AcademicYear.objects.get(pk=year.pk)
        assert year.status == AcademicYear.CampaignStatus.PRE_ASSIGNMENT


@pytest.mark.django_db
class TestAutoCreateNextAcademicYear:
    def _make_closed_year_yesterday(self, label, **kwargs):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        year = AcademicYear.objects.create(
            label=label,
            start_date=yesterday - timedelta(days=364),
            end_date=yesterday,
            **kwargs,
        )
        AcademicYear.objects.filter(pk=year.pk).update(status="closed")
        return AcademicYear.objects.get(pk=year.pk)

    def test_creates_next_year_after_closure(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        source = self._make_closed_year_yesterday("TEST-SOURCE-A")

        auto_create_next_academic_year()

        new_start = source.start_date.replace(year=source.start_date.year + 1)
        new_end = yesterday.replace(year=yesterday.year + 1)
        expected_label = f"{new_start.year}-{new_end.year}"
        new_year = AcademicYear.objects.filter(label=expected_label).first()
        assert new_year is not None
        assert new_year.status == AcademicYear.CampaignStatus.INITIALIZATION

    def test_new_year_dates_shifted_by_one_year(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        wishes_open = yesterday - timedelta(days=300)
        wishes_close = yesterday - timedelta(days=270)
        source = self._make_closed_year_yesterday(
            "TEST-SOURCE-B",
            wishes_open_date=wishes_open,
            wishes_close_date=wishes_close,
        )

        auto_create_next_academic_year()

        new_start = source.start_date.replace(year=source.start_date.year + 1)
        new_end = yesterday.replace(year=yesterday.year + 1)
        expected_label = f"{new_start.year}-{new_end.year}"
        new_year = AcademicYear.objects.get(label=expected_label)
        assert new_year.start_date == new_start
        assert new_year.end_date == new_end
        assert new_year.wishes_open_date == wishes_open.replace(
            year=wishes_open.year + 1
        )
        assert new_year.wishes_close_date == wishes_close.replace(
            year=wishes_close.year + 1
        )

    def test_does_not_create_if_already_exists(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        source = self._make_closed_year_yesterday("TEST-SOURCE-C")
        new_start = source.start_date.replace(year=source.start_date.year + 1)
        new_end = yesterday.replace(year=yesterday.year + 1)
        expected_label = f"{new_start.year}-{new_end.year}"
        AcademicYear.objects.create(
            label=expected_label,
            start_date=new_start,
            end_date=new_end,
        )

        auto_create_next_academic_year()

        assert AcademicYear.objects.filter(label=expected_label).count() == 1

    def test_does_not_create_for_non_closed_year(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        year = AcademicYear.objects.create(
            label="TEST-SOURCE-D",
            start_date=yesterday - timedelta(days=364),
            end_date=yesterday,
        )
        AcademicYear.objects.filter(pk=year.pk).update(status="validation")
        initial_count = AcademicYear.objects.count()

        auto_create_next_academic_year()

        assert AcademicYear.objects.count() == initial_count

    def test_does_not_create_for_year_closed_before_yesterday(self):
        today = timezone.now().date()
        two_days_ago = today - timedelta(days=2)
        year = AcademicYear.objects.create(
            label="TEST-SOURCE-E",
            start_date=two_days_ago - timedelta(days=364),
            end_date=two_days_ago,
        )
        AcademicYear.objects.filter(pk=year.pk).update(status="closed")
        initial_count = AcademicYear.objects.count()

        auto_create_next_academic_year()

        assert AcademicYear.objects.count() == initial_count
