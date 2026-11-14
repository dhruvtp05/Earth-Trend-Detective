"""
Explicitly-labeled demonstration fixture for Earth Trend Detective.

This module exists so Section C can build and test the entire user
interface before Sections A (data) and B (statistics) deliver their
real outputs.

Rules (from project brief §7 and §9):
  - Every value produced here is SYNTHETIC.
  - The DatasetMetadata.data_kind is always "synthetic".
  - Every UI surface that displays this data MUST show the badge
    "Synthetic demo data — not NASA findings".
  - When real Section A + B integrations land, the default demo
    path switches away from this module; this module remains as a
    deterministic development fallback only.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np

from .contracts import (
    DatasetMetadata,
    Investigation,
    SeriesPoint,
    TrendResult,
)

SYNTHETIC_BADGE = "Synthetic demo data — not NASA findings"

# Reproducible synthetic series: annual mean 2 m air temperature
# vaguely resembling what a reanalysis product would give for a
# Chicago-area grid cell, 1980 through 2024. Not a measurement,
# not a forecast, not to be cited.
_RNG_SEED = 20261114
_BASELINE_DEG_C = 10.6           # plausible Chicago annual mean (°C)
_SYNTHETIC_TREND_PER_YEAR = 0.03  # 0.3 °C per decade, mild upward
_NOISE_STD = 0.55                 # interannual variability


def _generate_annual_series(
    start_year: int = 1980,
    end_year: int = 2024,
) -> list[SeriesPoint]:
    rng = np.random.default_rng(_RNG_SEED)
    years = np.arange(start_year, end_year + 1)
    trend_component = (years - start_year) * _SYNTHETIC_TREND_PER_YEAR
    noise = rng.normal(0.0, _NOISE_STD, size=len(years))
    values = _BASELINE_DEG_C + trend_component + noise
    return [
        SeriesPoint(date=date(int(y), 7, 1), value=float(v))
        for y, v in zip(years, values)
    ]


def _demo_metadata() -> DatasetMetadata:
    return DatasetMetadata(
        dataset_name="SYNTHETIC — placeholder for MERRA-2 M2T1NXSLV (T2M)",
        dataset_version="demo-0.1",
        source_url="https://giovanni.gsfc.nasa.gov/giovanni/",
        retrieved_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
        coordinates_or_bounds="Nearest reanalysis grid cell to 41.88°N, 87.63°W",
        spatial_resolution="~0.5° latitude × 0.625° longitude (MERRA-2 native)",
        data_kind="synthetic",
        missing_value_rules="No missing values in this synthetic fixture.",
        unit="degC",
        variable_label="Near-surface air temperature (annual mean)",
        variable_definition=(
            "Mean of the model-reanalyzed 2-metre air temperature over "
            "each calendar year, in degrees Celsius."
        ),
    )


# ---------------------------------------------------------------------------
# Honest OLS on the synthetic series.
#
# The trend and 95% CI returned here are computed from the synthetic
# data with ordinary least squares, so the UI's uncertainty logic can
# be validated against real numbers rather than invented ones.
# ---------------------------------------------------------------------------

def _ols_trend_per_decade(
    points: list[SeriesPoint],
    confidence_level: float = 0.95,
) -> tuple[float, float, float, list[float]]:
    """Return (slope_per_decade, ci_lower_per_decade, ci_upper_per_decade,
    fitted_values_at_each_point)."""
    years = np.array([p.date.year + (p.date.month - 1) / 12 for p in points])
    values = np.array([p.value for p in points])

    n = len(points)
    x_mean = years.mean()
    y_mean = values.mean()
    dx = years - x_mean
    dy = values - y_mean

    slope_per_year = float((dx * dy).sum() / (dx * dx).sum())
    intercept = y_mean - slope_per_year * x_mean
    fitted = intercept + slope_per_year * years

    residuals = values - fitted
    # Residual standard error (unbiased, two parameters fit).
    rse = float(np.sqrt((residuals ** 2).sum() / (n - 2)))
    se_slope = rse / float(np.sqrt((dx ** 2).sum()))

    # Normal-approximation CI. (Section B's real analysis may use t.)
    z = 1.959963984540054 if abs(confidence_level - 0.95) < 1e-9 else 1.96
    half_width_per_year = z * se_slope

    slope_per_decade = slope_per_year * 10.0
    ci_half_per_decade = half_width_per_year * 10.0

    return (
        slope_per_decade,
        slope_per_decade - ci_half_per_decade,
        slope_per_decade + ci_half_per_decade,
        fitted.tolist(),
    )


def get_investigation(
    period_start: date = date(1980, 1, 1),
    period_end: date = date(2024, 12, 31),
    confidence_level: float = 0.95,
) -> Investigation:
    """Return a complete, display-ready investigation bundle."""
    points = _generate_annual_series(
        start_year=period_start.year,
        end_year=period_end.year,
    )
    metadata = _demo_metadata()

    slope, lo, hi, fitted = _ols_trend_per_decade(points, confidence_level)

    trend = TrendResult(
        status="ok",
        period_start=points[0].date,
        period_end=points[-1].date,
        aggregation="Annual mean",
        trend_per_decade=slope,
        trend_unit="degC/decade",
        confidence_level=confidence_level,
        ci_lower=lo,
        ci_upper=hi,
        valid_count=len(points),
        excluded_count=0,
        method="Ordinary least squares on annual means (synthetic demo)",
        assumptions=[
            "Residuals are approximately independent and identically distributed.",
            "A linear trend is a reasonable summary over the selected period.",
        ],
        warnings=[
            "This result is computed from synthetic data for interface "
            "development only. Do not cite as a NASA finding."
        ],
        fitted_dates=[p.date for p in points],
        fitted_values=fitted,
        band_lower=None,   # Section B will supply a proper band if available.
        band_upper=None,
    )

    return Investigation(
        location_label="Chicago area",
        location_coverage=metadata.coordinates_or_bounds,
        points=points,
        metadata=metadata,
        trend=trend,
        is_demo=True,
    )


def get_insufficient_data_investigation() -> Investigation:
    """Scenario fixture for §9 'insufficient usable observations' state."""
    full = get_investigation()
    full.trend = TrendResult(
        status="insufficient_data",
        period_start=full.trend.period_start,
        period_end=full.trend.period_end,
        aggregation="Annual mean",
        trend_per_decade=None,
        trend_unit="degC/decade",
        confidence_level=0.95,
        ci_lower=None,
        ci_upper=None,
        valid_count=2,
        excluded_count=43,
        method="Ordinary least squares on annual means (not run — too few points)",
        assumptions=[],
        warnings=["Fewer than the minimum usable observations for this method."],
    )
    full.points = full.points[:2]
    return full
