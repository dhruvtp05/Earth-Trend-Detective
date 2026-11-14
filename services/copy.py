"""
Scientific-communication copy.

Every public-facing sentence that describes a scientific result is
generated here, so this is the one file to audit against project brief §7:

  - Distinguish estimated direction from strength of evidence.
  - Distinguish statistical significance from practical importance.
  - Distinguish historical trend from future prediction.
  - Distinguish evidence of change from evidence of its cause.
  - Do not invent confidence percentages.
  - Do not say "no change" merely because the result is not significant.
  - Do not label model estimates as local measurements.

Decisions (for example whether the interval includes zero) use the raw
values, never the rounded ones shown on screen.
"""

from __future__ import annotations

import math

from .contracts import DatasetMetadata, TrendResult

PROVISIONAL_NOTICE = (
    "Provisional trend. These numbers come from a placeholder method while "
    "the team's statistical analysis is being finalised. Please do not cite them."
)

SAVED_DATA_NOTICE = "Saved NASA dataset stored with this app, not a live request."


def base_unit(trend_unit: str) -> str:
    """'mm/day/decade' -> 'mm/day'."""
    return trend_unit.removesuffix("/decade")


def trend_decimals(trend: TrendResult) -> int:
    """Decimal places that keep the interval readable (between 2 and 6)."""
    if trend.ci_lower is None or trend.ci_upper is None:
        return 2
    half_width = abs(trend.ci_upper - trend.ci_lower) / 2
    if half_width <= 0:
        return 2
    return min(6, max(2, 1 - math.floor(math.log10(half_width))))


def format_value(value: float) -> str:
    """A data value to three significant figures, e.g. '2.37' or '0.00643'."""
    return f"{value:.3g}"


def format_signed(value: float, decimals: int) -> str:
    """Signed, fixed-decimal string, e.g. '+0.31' or '-0.08'."""
    return f"{value:+.{decimals}f}"


def period_label(trend: TrendResult) -> str:
    return f"{trend.period_start.year}–{trend.period_end.year}"


def title_sentence(location_label: str, variable_label: str, trend: TrendResult) -> str:
    return f"{variable_label} in the {location_label}, {period_label(trend)}"


def result_sentence(location_coverage: str, variable_label: str, trend: TrendResult) -> str:
    """'For [location coverage], [variable] has an estimated trend of
    [signed value] [unit] per decade during [start–end].'"""
    if trend.status != "ok" or trend.trend_per_decade is None:
        return conclusion_sentence(trend)

    value = format_signed(trend.trend_per_decade, trend_decimals(trend))
    return (
        f"For {location_coverage}, {variable_label.lower()} has an estimated "
        f"trend of {value} {base_unit(trend.trend_unit)} per decade during "
        f"{period_label(trend)}."
    )


def uncertainty_sentence(trend: TrendResult) -> str:
    """'The 95% confidence interval for the trend is [lower] to [upper]
    [unit] per decade, under the analysis assumptions.'"""
    if trend.status != "ok" or trend.ci_lower is None or trend.ci_upper is None:
        return ""

    decimals = trend_decimals(trend)
    percent = round(trend.confidence_level * 100)
    return (
        f"The {percent}% confidence interval for the trend is "
        f"{format_signed(trend.ci_lower, decimals)} to "
        f"{format_signed(trend.ci_upper, decimals)} "
        f"{base_unit(trend.trend_unit)} per decade, under the analysis assumptions."
    )


def interval_includes_zero(trend: TrendResult) -> bool:
    return (
        trend.ci_lower is not None
        and trend.ci_upper is not None
        and trend.ci_lower <= 0.0 <= trend.ci_upper
    )


def conclusion_sentence(trend: TrendResult) -> str:
    """Interpretation that respects the status and the interval."""
    if trend.status == "insufficient_data":
        return (
            "There is not enough usable data to estimate a reliable trend "
            "for this selection."
        )
    if trend.status == "invalid_selection":
        return (
            "This selection cannot be analysed with the available data. "
            "Choose a different region, variable or time period."
        )
    if trend.status == "analysis_failed":
        return (
            "The analysis could not be completed for this selection. "
            "Choose a different time period, or try again."
        )
    if trend.trend_per_decade is None or trend.ci_lower is None or trend.ci_upper is None:
        return ""

    if interval_includes_zero(trend):
        return (
            "This analysis does not clearly distinguish an upward or downward "
            "long-term trend from variability over this period."
        )

    direction = "an upward" if trend.trend_per_decade > 0 else "a downward"
    return (
        f"Under the analysis assumptions, the data are consistent with "
        f"{direction} long-term trend over this period. This describes the "
        f"historical record. It is not a prediction, and it does not show "
        f"what caused the change."
    )


def coverage_sentence(metadata: DatasetMetadata) -> str:
    """One-line reminder of what the values represent."""
    phrases = {
        "reanalysis": (
            "These values are area averages from a reanalysis (a weather model "
            "constrained by observations), not measurements at a single place."
        ),
        "model": (
            "These values are area averages from a land-surface model driven "
            "by observations, not measurements at a single place."
        ),
        "satellite": (
            "These values are area averages of satellite-derived estimates, "
            "not ground measurements at a single place."
        ),
        "station": "These values come from ground station measurements.",
    }
    return phrases.get(metadata.data_kind, "")
