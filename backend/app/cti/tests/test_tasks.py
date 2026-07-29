"""Tests unitaires pour les tâches async CTI."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestEnqueueRefreshCtiDurations:
    def test_returns_task_id(self):
        with patch(
            "app.cti.tasks.async_task", return_value="task-id-123"
        ) as mock_async:
            from app.cti.tasks import enqueue_refresh_cti_durations

            result = enqueue_refresh_cti_durations(42, triggered_by="admin")

            assert result == "task-id-123"
            mock_async.assert_called_once_with(
                "app.cti.tasks.run_refresh_cti_durations",
                42,
                "admin",
                group="cti-duration-refresh",
                task_name="CTI duration refresh",
            )

    def test_triggered_by_defaults_to_empty_string(self):
        with patch("app.cti.tasks.async_task", return_value="x") as mock_async:
            from app.cti.tasks import enqueue_refresh_cti_durations

            enqueue_refresh_cti_durations(1)

            _, args, kwargs = mock_async.mock_calls[0]
            assert args[2] == ""


class TestRunRefreshCtiDurations:
    def test_logs_error_for_unknown_year(self, db):
        from app.cti.tasks import run_refresh_cti_durations

        # Should not raise; just logs error
        run_refresh_cti_durations(99999, triggered_by="system")

    @pytest.mark.django_db
    def test_processes_terminal_enrolled_students(self, db):
        from app.academic.models import AcademicYear
        from app.cti.tasks import run_refresh_cti_durations

        year = AcademicYear.objects.create(
            label="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 8, 31),
        )

        with (
            patch("app.cti.services.refresh_cti_duration") as mock_refresh,
            patch("app.cti.services_export._get_terminal_enrolled", return_value=[]),
        ):
            run_refresh_cti_durations(year.id, triggered_by="test")
            mock_refresh.assert_not_called()

    @pytest.mark.django_db
    def test_calls_refresh_for_each_enrolled_student(self, db):
        from app.academic.models import AcademicYear
        from app.cti.tasks import run_refresh_cti_durations

        year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
        )

        mock_enrollment = MagicMock()
        mock_enrollment.student = MagicMock()

        with (
            patch("app.cti.services.refresh_cti_duration") as mock_refresh,
            patch(
                "app.cti.services_export._get_terminal_enrolled",
                return_value=[mock_enrollment, mock_enrollment],
            ),
        ):
            run_refresh_cti_durations(year.id)
            assert mock_refresh.call_count == 2
