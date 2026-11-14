"""
Adapter for Section B (aggregation, trend, uncertainty).

While Section B is still landing, this module forwards to the
honest-OLS computation used in services.demo. Once Section B's
real `estimate_trend(...)` is available, wire it in here — the UI
should not change.

Expected real signature (agreed with Section B):

    def estimate_trend(
        points: list[SeriesPoint],
        period_start: date,
        period_end: date,
        confidence_level: float = 0.95,
    ) -> TrendResult: ...
"""

from __future__ import annotations

from datetime import date

from .contracts import SeriesPoint, TrendResult
from . import demo


def estimate_trend(
    points: list[SeriesPoint],
    period_start: date,
    period_end: date,
    confidence_level: float = 0.95,
) -> TrendResult:
    """TEMPORARY: computes an honest OLS slope + normal-approximation CI
    on the supplied points. Section B will replace this with its own
    aggregation + statistical method. Keep this function's signature
    stable.
    """
    if len(points) < 3:
        return TrendResult(
            status="insufficient_data",
            period_start=period_start,
            period_end=period_end,
            aggregation="Annual mean",
            trend_per_decade=None,
            trend_unit="degC/decade",
            confidence_level=confidence_level,
            ci_lower=None,
            ci_upper=None,
            valid_count=len(points),
            excluded_count=0,
            method="OLS on annual means (not run — too few points)",
            warnings=[
                "Fewer than the minimum usable observations for this method."
            ],
        )

    slope, lo, hi, fitted = demo._ols_trend_per_decade(points, confidence_level)
    return TrendResult(
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
        method="Ordinary least squares on annual means (Section C placeholder)",
        assumptions=[
            "Residuals are approximately independent and identically distributed.",
            "A linear trend is a reasonable summary over the selected period.",
        ],
        warnings=[
            "Placeholder statistical method. Will be replaced by Section B."
        ],
        fitted_dates=[p.date for p in points],
        fitted_values=fitted,
    )
