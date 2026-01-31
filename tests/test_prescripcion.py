"""Tests for es_prescribible() — prescription date logic."""

from datetime import datetime, timedelta

from freezegun import freeze_time

from app import es_prescribible


class TestEsPrescribible:
    """Boundary and edge-case tests for the 3-year prescription rule."""

    # --- Clear-cut cases ---

    @freeze_time("2026-01-31")
    def test_fine_four_years_ago_is_prescribible(self):
        assert es_prescribible("31-01-2022") is True

    @freeze_time("2026-01-31")
    def test_fine_one_year_ago_is_not_prescribible(self):
        assert es_prescribible("31-01-2025") is False

    @freeze_time("2026-01-31")
    def test_fine_ten_years_ago_is_prescribible(self):
        assert es_prescribible("15-06-2015") is True

    @freeze_time("2026-01-31")
    def test_fine_yesterday_is_not_prescribible(self):
        assert es_prescribible("30-01-2026") is False

    # --- Boundary cases (around 1095 days = 3 * 365) ---

    @freeze_time("2026-01-31")
    def test_fine_exactly_1095_days_ago_is_not_prescribible(self):
        """1095 days ago from 2026-01-31 = 2023-02-01. Boundary: NOT prescribible."""
        target = datetime(2026, 1, 31) - timedelta(days=1095)
        date_str = target.strftime("%d-%m-%Y")
        assert es_prescribible(date_str) is False

    @freeze_time("2026-01-31")
    def test_fine_1096_days_ago_is_prescribible(self):
        """1096 days ago is past the threshold."""
        target = datetime(2026, 1, 31) - timedelta(days=1096)
        date_str = target.strftime("%d-%m-%Y")
        assert es_prescribible(date_str) is True

    @freeze_time("2026-01-31")
    def test_fine_1094_days_ago_is_not_prescribible(self):
        """1094 days is within threshold."""
        target = datetime(2026, 1, 31) - timedelta(days=1094)
        date_str = target.strftime("%d-%m-%Y")
        assert es_prescribible(date_str) is False

    # --- Date format with trailing time component ---

    @freeze_time("2026-01-31")
    def test_date_with_time_suffix(self):
        """procesar_pdf passes dates like '15-03-2020 00:00:00'."""
        assert es_prescribible("15-03-2020 00:00:00") is True

    @freeze_time("2026-01-31")
    def test_date_with_time_suffix_recent(self):
        assert es_prescribible("01-12-2025 14:30:00") is False

    # --- Malformed / invalid input ---

    def test_empty_string_returns_false(self):
        assert es_prescribible("") is False

    def test_none_returns_false(self):
        assert es_prescribible(None) is False

    def test_garbage_string_returns_false(self):
        assert es_prescribible("not-a-date") is False

    def test_wrong_date_format_returns_false(self):
        """US format (MM-DD-YYYY) should fail since the function expects DD-MM-YYYY."""
        assert es_prescribible("2020-03-15") is False

    def test_impossible_date_returns_false(self):
        assert es_prescribible("32-13-2020") is False

    # --- Leap year awareness ---

    @freeze_time("2024-02-29")
    def test_leap_year_date_as_reference(self):
        """Running on Feb 29 of a leap year, with a fine >3 years old."""
        assert es_prescribible("28-02-2021") is True

    @freeze_time("2024-02-29")
    def test_leap_year_recent_fine(self):
        assert es_prescribible("01-03-2023") is False
