"""Checks on data loading, the placeholder trend and the result sentences."""

from __future__ import annotations

from datetime import date

import pytest

from services import catalog, copy, investigate, section_a, section_b
from services.contracts import SeriesPoint, TrendResult


def _trend(status="ok", slope=0.5, low=0.1, high=0.9) -> TrendResult:
    ok = status == "ok"
    return TrendResult(
        status=status,
        period_start=date(2005, 1, 1),
        period_end=date(2025, 12, 31),
        aggregation="Annual mean",
        trend_per_decade=slope if ok else None,
        trend_unit="mm/day/decade",
        confidence_level=0.95,
        ci_lower=low if ok else None,
        ci_upper=high if ok else None,
        valid_count=252,
        excluded_count=0,
        method="test",
    )


# --- Section A: saved files -------------------------------------------------


def test_all_delivered_files_are_discovered():
    found = catalog.discover()
    for region in ("midwest", "southwest"):
        for variable in ("precip", "soilmoisture"):
            assert (region, variable) in found


@pytest.mark.parametrize(
    "region, variable, years, months",
    [
        ("midwest", "precip", (2005, 2025), 252),
        ("southwest", "precip", (2005, 2025), 252),
        ("midwest", "soilmoisture", (2000, 2025), 312),
        ("southwest", "soilmoisture", (2000, 2025), 312),
        ("midwest", "runoff", (2000, 2025), 312),
        ("southwest", "runoff", (2000, 2025), 312),
        ("midwest", "evap", (2005, 2025), 252),
        ("southwest", "evap", (2005, 2025), 252),
    ],
)
def test_series_matches_the_file(region, variable, years, months):
    assert section_a.available_years(region, variable) == years
    points, metadata = section_a.get_series(
        region, variable, date(years[0], 1, 1), date(years[1], 12, 31)
    )
    assert len(points) == months
    assert metadata.source_url.startswith("https://giovanni.gsfc.nasa.gov/")
    assert "0 of" in metadata.missing_value_rules


def test_first_value_and_bounds_are_read_exactly():
    points, metadata = section_a.get_series(
        "midwest", "precip", date(2005, 1, 1), date(2005, 12, 31)
    )
    assert points[0] == SeriesPoint(date(2005, 1, 1), 2.36955619)
    assert metadata.coordinates_or_bounds == "Area average over 40°N–49°N, 92.5°W–76.25°W"
    assert metadata.unit == "mm/day"
    assert metadata.data_kind == "reanalysis"


def test_evaporation_is_converted_from_kg_m2_s_to_mm_per_day():
    points, metadata = section_a.get_series(
        "midwest", "evap", date(2005, 1, 1), date(2005, 12, 31)
    )
    assert points[0].value == pytest.approx(5.02223611e-06 * 86400)
    assert metadata.unit == "mm/day"
    assert "86,400" in metadata.unit_note


def test_unit_is_only_read_for_the_files_own_variable():
    url = "https://x/#data=A_PRECIP(units%3Dmm%2Fday)%2CB_EVLAND&format=json"
    assert section_a._unit_from_url(url, "mean_A_PRECIP") == "mm/day"
    assert section_a._unit_from_url(url, "B_EVLAND") is None


def test_fill_values_are_treated_as_missing(tmp_path, monkeypatch):
    (tmp_path / "testland_precip_regionZ.csv").write_text(
        'Title:,"Demo"\n'
        'Data Bounding Box:,"-10,-5,10,5"\n'
        "Fill Value (mean_X):, -9999\n"
        "\n"
        "time, mean_X\n"
        "2001-01-01 00:00:00,1.0\n"
        "2001-02-01 00:00:00,-9999\n"
        "2001-03-01 00:00:00,3.0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(catalog, "DATA_DIR", tmp_path)
    points, metadata = section_a.get_series(
        "testland", "precip", date(2001, 1, 1), date(2001, 12, 31)
    )
    assert [point.value for point in points] == [1.0, 3.0]
    assert "1 of 3 months" in metadata.missing_value_rules
    assert metadata.coordinates_or_bounds == "Area average over 5°S–5°N, 10°W–10°E"


def test_unknown_selection_raises():
    with pytest.raises(section_a.DataUnavailableError):
        section_a.get_series("atlantis", "precip", date(2005, 1, 1), date(2025, 12, 31))


# --- Section B placeholder ---------------------------------------------------


def _monthly(years, value_for_year):
    return [
        SeriesPoint(date(year, month, 1), value_for_year(year) + (month - 6.5))
        for year in years
        for month in range(1, 13)
    ]


def test_exact_line_is_recovered():
    points = _monthly(range(2000, 2020), lambda year: 10 + 0.2 * (year - 2000))
    trend = section_b.estimate_trend(points, date(2000, 1, 1), date(2019, 12, 31), unit="mm")
    assert trend.status == "ok"
    assert trend.trend_per_decade == pytest.approx(2.0)
    assert trend.ci_lower == pytest.approx(2.0)
    assert trend.ci_upper == pytest.approx(2.0)
    assert trend.trend_unit == "mm/decade"
    assert trend.valid_count == 240


def test_interval_matches_textbook_ols():
    # Annual means 1, 3, 2, 5, 4, 6, 8, 7, 9, 11 on years 0..9:
    # Sxx = 82.5, Sxy = 84, Syy = 92.4, so slope = Sxy/Sxx and
    # SSE = Syy - Sxy^2/Sxx; se = sqrt(SSE/8/Sxx); t(8) = 2.306.
    means = [1, 3, 2, 5, 4, 6, 8, 7, 9, 11]
    points = [
        SeriesPoint(date(2000 + index, month, 1), float(mean))
        for index, mean in enumerate(means)
        for month in range(1, 13)
    ]
    trend = section_b.estimate_trend(points, date(2000, 1, 1), date(2009, 12, 31))
    slope = 84 / 82.5
    half = 2.306 * ((92.4 - 84**2 / 82.5) / 8 / 82.5) ** 0.5
    assert trend.trend_per_decade == pytest.approx(slope * 10, rel=1e-6)
    assert trend.ci_lower == pytest.approx((slope - half) * 10, rel=1e-5)
    assert trend.ci_upper == pytest.approx((slope + half) * 10, rel=1e-5)


def test_confidence_band_matches_textbook_ols():
    # Same data as above. The band for the fitted mean at year x is
    # fitted ± t * s * sqrt(1/n + (x - mean)^2 / Sxx), with s^2 = SSE / (n - 2).
    means = [1, 3, 2, 5, 4, 6, 8, 7, 9, 11]
    points = [
        SeriesPoint(date(2000 + index, month, 1), float(mean))
        for index, mean in enumerate(means)
        for month in range(1, 13)
    ]
    trend = section_b.estimate_trend(points, date(2000, 1, 1), date(2009, 12, 31))
    residual_sd = ((92.4 - 84**2 / 82.5) / 8) ** 0.5
    assert len(trend.band_lower) == len(trend.band_upper) == len(trend.fitted_values) == 10
    for index, fitted in enumerate(trend.fitted_values):
        half = 2.306 * residual_sd * (1 / 10 + (index - 4.5) ** 2 / 82.5) ** 0.5
        assert trend.band_lower[index] == pytest.approx(fitted - half, rel=1e-4)
        assert trend.band_upper[index] == pytest.approx(fitted + half, rel=1e-4)
    # Narrowest in the middle of the record, widest at the ends.
    widths = [high - low for low, high in zip(trend.band_lower, trend.band_upper)]
    assert widths[0] == pytest.approx(widths[-1])
    assert min(widths) == pytest.approx(widths[4]) and widths[4] < widths[0]


def test_too_few_years_gives_no_numbers():
    points = _monthly(range(2000, 2005), lambda year: float(year))
    trend = section_b.estimate_trend(points, date(2000, 1, 1), date(2004, 12, 31))
    assert trend.status == "insufficient_data"
    assert trend.trend_per_decade is None and trend.ci_lower is None
    assert trend.fitted_values is None
    assert trend.band_lower is None and trend.band_upper is None


def test_incomplete_years_are_left_out_and_reported():
    points = _monthly(range(2000, 2012), lambda year: float(year))
    points = [p for p in points if not (p.date.year == 2005 and p.date.month == 3)]
    trend = section_b.estimate_trend(points, date(2000, 1, 1), date(2011, 12, 31))
    assert trend.status == "ok"
    assert trend.valid_count == 11 * 12
    assert trend.excluded_count == 11
    assert any("2005" in warning for warning in trend.warnings)


# --- Scientific-communication sentences --------------------------------------


def test_result_and_uncertainty_templates():
    trend = _trend(slope=0.5, low=0.1, high=0.9)
    assert copy.result_sentence("the Test region", "Precipitation", trend) == (
        "For the Test region, precipitation has an estimated trend of "
        "+0.50 mm/day per decade during 2005–2025."
    )
    assert copy.uncertainty_sentence(trend) == (
        "The 95% confidence interval for the trend is +0.10 to +0.90 "
        "mm/day per decade, under the analysis assumptions."
    )


def test_interval_including_zero_never_says_no_change():
    sentence = copy.conclusion_sentence(_trend(slope=0.2, low=-0.1, high=0.5))
    assert sentence == (
        "This analysis does not clearly distinguish an upward or downward "
        "long-term trend from variability over this period."
    )
    assert "no change" not in sentence.lower()


def test_zero_check_uses_raw_values_not_rounded_ones():
    # Rounds to "+0.00" at two decimals but is above zero.
    trend = _trend(slope=0.5, low=0.0004, high=1.0)
    assert not copy.interval_includes_zero(trend)
    assert "upward" in copy.conclusion_sentence(trend)


def test_direction_wording():
    assert "a downward" in copy.conclusion_sentence(_trend(slope=-0.5, low=-0.9, high=-0.1))
    upward = copy.conclusion_sentence(_trend())
    assert "an upward" in upward
    assert "not a prediction" in upward and "caused" in upward


@pytest.mark.parametrize("status", ["insufficient_data", "invalid_selection", "analysis_failed"])
def test_non_ok_statuses_show_no_numbers(status):
    trend = _trend(status=status)
    assert copy.uncertainty_sentence(trend) == ""
    sentence = copy.result_sentence("the Test region", "Precipitation", trend)
    assert sentence == copy.conclusion_sentence(trend)
    assert not any(character.isdigit() for character in sentence)


def test_insufficient_data_template():
    assert copy.conclusion_sentence(_trend(status="insufficient_data")) == (
        "There is not enough usable data to estimate a reliable trend for this selection."
    )


def test_globe_direction_is_only_given_when_the_interval_excludes_zero():
    rising = _trend(slope=0.5, low=0.1, high=0.9)
    falling = _trend(slope=-0.5, low=-0.9, high=-0.1)
    unclear_up = _trend(slope=0.5, low=-0.1, high=1.1)
    unclear_down = _trend(slope=-0.5, low=-1.1, high=0.1)
    assert copy.trend_direction(rising) == "increase"
    assert copy.trend_direction(falling) == "decrease"
    # A large slope is still not coloured when its interval includes zero.
    assert copy.trend_direction(unclear_up) == "inconclusive"
    assert copy.trend_direction(unclear_down) == "inconclusive"
    assert copy.trend_direction(_trend(slope=0.5, low=0.0, high=1.0)) == "inconclusive"

    assert copy.significance_badge(rising) == copy.significance_badge(falling) == "Significant"
    assert copy.significance_badge(unclear_up) == "Inconclusive"
    assert copy.significance_note(unclear_up) == (
        "Inconclusive: the 95% confidence interval includes zero, so no direction is shown."
    )
    assert "does not say how large or important" in copy.significance_note(rising)

    assert copy.trend_headline(rising) == "Upward trend"
    assert copy.trend_headline(falling) == "Downward trend"
    assert copy.trend_headline(unclear_up) == copy.trend_headline(unclear_down) == "No clear trend"
    assert "no change" not in " ".join(copy.HEADLINE_LABELS.values()).lower()


@pytest.mark.parametrize("status", ["insufficient_data", "invalid_selection", "analysis_failed"])
def test_globe_labels_show_no_numbers_without_a_trend(status):
    trend = _trend(status=status)
    assert copy.trend_direction(trend) == "none"
    assert copy.significance_badge(trend) == "No trend estimated"
    assert copy.trend_headline(trend) == "No trend estimated"
    assert copy.significance_note(trend) == ""
    assert copy.trend_value_text(trend) == "" and copy.interval_text(trend) == ""


def test_globe_value_and_interval_labels():
    trend = _trend(slope=-0.05, low=-0.146, high=0.046)
    assert copy.trend_value_text(trend) == "-0.050"
    assert copy.interval_text(trend) == "-0.146 to +0.046"
    assert copy.trend_unit_label(trend) == "mm/day per decade"
    assert copy.band_label(trend) == "95% confidence band for the fitted trend"


def test_tour_visits_the_southwest_then_the_midwest():
    assert catalog.tour_region_ids() == ["southwest", "midwest"]
    assert catalog.region_info("southwest").letter == "A"
    assert catalog.region_info("midwest").letter == "B"
    assert catalog.region_info("midwest").label == "Midwest"
    assert catalog.variable_short_label("soilmoisture") == "Soil moisture"


def test_small_intervals_get_more_decimals():
    assert copy.trend_decimals(_trend(low=-0.146, high=0.046)) == 3
    assert copy.trend_decimals(_trend(low=-1.2, high=-0.1)) == 2


def test_every_delivered_dataset_has_readable_labels_and_numbers():
    for (region, variable) in catalog.discover():
        assert variable in catalog.VARIABLES, f"{variable} needs a catalog entry"
        low, high = section_a.available_years(region, variable)
        inv = investigate.load(region, variable, low, high)
        assert inv.trend.status == "ok"
        decimals = copy.trend_decimals(inv.trend)
        # The displayed interval must not collapse to a single rounded value.
        assert copy.format_signed(inv.trend.ci_lower, decimals) != copy.format_signed(
            inv.trend.ci_upper, decimals
        )


# --- End to end ---------------------------------------------------------------


def test_investigation_bundle():
    inv = investigate.load("southwest", "soilmoisture", 2000, 2025)
    assert inv.location_label == "Southwest"
    assert inv.location_coverage.startswith("the Southwest region (area average over ")
    assert inv.trend.status == "ok"
    assert inv.trend.trend_unit == "kg/m²/decade"
    assert len(inv.trend.aggregated_values) == 26
    assert inv.trend_is_placeholder is section_b.IS_PLACEHOLDER
