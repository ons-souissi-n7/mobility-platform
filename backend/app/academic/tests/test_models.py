from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_fsm import TransitionNotAllowed

from app.academic.models import AcademicYear


@pytest.mark.django_db
class TestAcademicYear:
    def test_create_academic_year(self):
        today = timezone.now().date()
        academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=today,
            end_date=today + timedelta(days=365),
        )

        assert str(academic_year) == "2026-2027"
        assert academic_year.status == AcademicYear.CampaignStatus.INITIALIZATION

    def test_start_date_must_be_before_end_date(self):
        today = timezone.now().date()
        academic_year = AcademicYear(
            label="2026-2027",
            start_date=today,
            end_date=today - timedelta(days=1),
        )

        with pytest.raises(ValidationError):
            academic_year.full_clean()

    def test_wishes_open_date_must_be_before_close_date(self):
        today = timezone.now().date()
        academic_year = AcademicYear(
            label="2026-2027",
            start_date=today,
            end_date=today + timedelta(days=365),
            wishes_open_date=today + timedelta(days=20),
            wishes_close_date=today + timedelta(days=10),
        )

        with pytest.raises(ValidationError):
            academic_year.full_clean()

    def test_campaign_workflow(self):
        today = timezone.now().date()
        academic_year = create_current_year(
            wishes_open_date=today,
            wishes_close_date=today + timedelta(days=30),
        )

        academic_year.open_recommendation()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.RECOMMENDATION

        academic_year.start_candidature()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.CANDIDATURE

        academic_year.close_wishes()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.IMPORT

        academic_year.launch_assignment()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.PRE_ASSIGNMENT

        academic_year.complete_assignment()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.VALIDATION

        academic_year.publish_results()
        academic_year.save()
        assert academic_year.status == AcademicYear.CampaignStatus.PUBLISHED

        academic_year.close()
        academic_year.save()
        assert academic_year.is_closed()

    def test_transition_order_is_enforced(self):
        academic_year = create_current_year()

        with pytest.raises(TransitionNotAllowed):
            academic_year.close()

    def test_is_active(self):
        assert create_current_year().is_active()

    def test_is_wishes_open(self):
        today = timezone.now().date()
        academic_year = create_current_year(
            wishes_open_date=today - timedelta(days=1),
            wishes_close_date=today + timedelta(days=1),
        )

        assert academic_year.is_wishes_open()

    def test_get_current(self):
        academic_year = create_current_year()

        assert AcademicYear.get_current() == academic_year

    def test_detect_by_date(self):
        today = timezone.now().date()
        academic_year = create_current_year()

        assert AcademicYear.detect_by_date(today) == academic_year


def create_current_year(**kwargs):
    today = timezone.now().date()
    defaults = {
        "label": "2026-2027",
        "start_date": today - timedelta(days=30),
        "end_date": today + timedelta(days=335),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)
