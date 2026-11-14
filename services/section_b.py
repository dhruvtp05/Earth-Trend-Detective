"""
Section B adapter: aggregation, trend and uncertainty.

PLACEHOLDER. Section B owns the statistical method. Until their analysis
lands, this module provides a simple stand-in so the interface can be
built and checked against real data. The UI marks every number from it
as provisional (see IS_PLACEHOLDER).

To integrate Section B: replace the body of `estimate_trend`, keep the
signature and the TrendResult shape, and set IS_PLACEHOLDER = False.

Stand-in method:
  1. Keep only calendar years with all 12 months present.
  2. Average the 12 monthly values of each year (removes the seasonal cycle).
  3. Fit ordinary least squares of annual mean on year.
  4. 95% confidence interval for the slope from the t distribution
     with n - 2 degrees of freedom.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from .contracts import SeriesPoint, TrendResult

IS_PLACEHOLDER = True

# Stand-in rule, not Section B's: fewer annual values than this and no
# trend is reported.
MIN_YEARS = 10

METHOD = "Ordinary least squares on annual means (placeholder, not Section B's method)"
AGGREGATION = "Annual mean of the 12 monthly values (months not weighted by length)"

# Two-sided 95% critical values of Student's t, degrees of freedom 1..30.
_T_975 = [
    12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
    2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
    2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042,
]


def _t_critical_95(dof: int) -> float:
    if dof <= 30:
        return _T_975[dof - 1]
    # Slightly conservative steps beyond the table.
    if dof <= 40:
        return 2.042
    if dof <= 60:
        return 2.021
    if dof <= 120:
        return 2.000
    return 1.980


def _not_ok(
    status: str,
    period_start: date,
    period_end: date,
    unit: str,
    confidence_level: float,
    valid: int,
    excluded: int,
    warning: str,
) -> TrendResult:
    return TrendResult(
        status=status,  # type: ignore[arg-type]
        period_start=period_start,
        period_end=period_end,
        aggregation=AGGREGATION,
        trend_per_decade=None,
        trend_unit=f"{unit}/decade",
        confidence_level=confidence_level,
        ci_lower=None,
        ci_upper=None,
        valid_count=valid,
        excluded_count=excluded,
        method=METHOD,
        warnings=[warning],
    )


def estimate_trend(
    points: list[SeriesPoint],
    period_start: date,
    period_end: date,
    confidence_level: float = 0.95,
    unit: str = "",
) -> TrendResult:
    """Estimate a linear trend per decade from monthly points."""
    if abs(confidence_level - 0.95) > 1e-9:
        return _not_ok(
            "analysis_failed", period_start, period_end, unit, confidence_level,
            0, len(points), "The placeholder method only supports a 95% confidence level.",
        )
    if period_start > period_end:
        return _not_ok(
            "invalid_selection", period_start, period_end, unit, confidence_level,
            0, len(points), "The start of the period is after its end.",
        )

    by_year: dict[int, list[float]] = defaultdict(list)
    for point in points:
        if period_start <= point.date <= period_end:
            by_year[point.date.year].append(point.value)

    complete = {year: values for year, values in by_year.items() if len(values) == 12}
    valid = 12 * len(complete)
    excluded = sum(len(values) for values in by_year.values()) - valid
    incomplete_years = sorted(set(by_year) - set(complete))

    if len(complete) < MIN_YEARS:
        return _not_ok(
            "insufficient_data", period_start, period_end, unit, confidence_level,
            valid, excluded,
            f"Only {len(complete)} complete years are available in this period; "
            f"the placeholder method needs at least {MIN_YEARS}.",
        )

    years = sorted(complete)
    means = [sum(complete[year]) / 12 for year in years]
    n = len(years)

    x_mean = sum(years) / n
    y_mean = sum(means) / n
    sxx = sum((x - x_mean) ** 2 for x in years)
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(years, means))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    fitted = [intercept + slope * x for x in years]

    sse = sum((y - f) ** 2 for y, f in zip(means, fitted))
    se_slope = math.sqrt(sse / (n - 2)) / math.sqrt(sxx)
    half_width = _t_critical_95(n - 2) * se_slope

    warnings = [
        "Placeholder statistical method. It will be replaced by Section B's analysis.",
    ]
    if incomplete_years:
        warnings.append(
            f"{len(incomplete_years)} incomplete year(s) were left out: "
            + ", ".join(str(year) for year in incomplete_years)
            + "."
        )

    mid_year = [date(year, 7, 1) for year in years]
    return TrendResult(
        status="ok",
        period_start=date(years[0], 1, 1),
        period_end=date(years[-1], 12, 31),
        aggregation=AGGREGATION,
        trend_per_decade=slope * 10,
        trend_unit=f"{unit}/decade",
        confidence_level=confidence_level,
        ci_lower=(slope - half_width) * 10,
        ci_upper=(slope + half_width) * 10,
        valid_count=valid,
        excluded_count=excluded,
        method=METHOD,
        assumptions=[
            "The long-term change is summarised by a straight line.",
            "Year-to-year departures from the line are independent, with similar spread throughout.",
            "Those departures are roughly normally distributed.",
        ],
        warnings=warnings,
        aggregated_dates=mid_year,
        aggregated_values=means,
        fitted_dates=mid_year,
        fitted_values=fitted,
    )
