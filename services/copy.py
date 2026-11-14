"""
Scientific-communication copy.

Every public-facing sentence that describes a scientific result is
generated here. This file is the single place to audit for violations
of project brief §7:

  - Distinguish estimated direction from strength of evidence.
  - Distinguish statistical significance from practical importance.
  - Distinguish historical trend from future prediction.
  - Distinguish evidence of change from evidence of its cause.
  - Do not invent confidence percentages.
  - Do not describe a p-value as the probability the conclusion is true.
  - Do not say "no change" merely because the result is not significant.
  - Do not make health or neighborhood-risk claims from a broad grid.
  - Do not label model estimates as local weather-station measurements.
"""

from __future__ import annotations

from .contracts import DatasetMetadata, TrendResult

# Phrase used wherever synthetic fixture data is shown.
SYNTHETIC_BADGE = "Synthetic demo data — not NASA findings"


def _format_signed(value: float, decimals: int = 2) -> str:
    """Return a signed, fixed-decimal string (e.g. '+0.31', '-0.08')."""
    return f"{value:+.{decimals}f}"


def _period_label(trend: TrendResult) -> str:
    return f"{trend.period_start.year}–{trend.period_end.year}"


def result_sentence(
    location_coverage: str,
    variable_label: str,
    trend: TrendResult,
) -> str:
    """Primary result sentence (project brief §7 template).

    'For [location coverage], [variable] has an estimated trend of
     [signed value] [unit] per decade during [start–end].'
    """
    if trend.status != "ok" or trend.trend_per_decade is None:
        return insufficient_or_invalid_sentence(trend)

    value_str = _format_signed(trend.trend_per_decade)
    # trend_unit like "degC/decade" — split for readability.
    base_unit = trend.trend_unit.split("/")[0] if "/" in trend.trend_unit else trend.trend_unit
    return (
        f"For {location_coverage}, {variable_label.lower()} has an estimated "
        f"trend of {value_str} {base_unit} per decade during {_period_label(trend)}."
    )


def uncertainty_sentence(trend: TrendResult) -> str:
    """Uncertainty sentence (project brief §7 template).

    'The 95% confidence interval for the trend is [lower] to [upper]
     [unit] per decade, under the analysis assumptions.'
    """
    if trend.status != "ok" or trend.ci_lower is None or trend.ci_upper is None:
        return ""

    pct = int(round(trend.confidence_level * 100))
    lo = _format_signed(trend.ci_lower)
    hi = _format_signed(trend.ci_upper)
    base_unit = trend.trend_unit.split("/")[0] if "/" in trend.trend_unit else trend.trend_unit
    return (
        f"The {pct}% confidence interval for the trend is {lo} to {hi} "
        f"{base_unit} per decade, under the analysis assumptions."
    )


def conclusion_sentence(trend: TrendResult) -> str:
    """Interpretation that respects CI-around-zero and status rules."""
    if trend.status == "insufficient_data":
        return (
            "There is not enough usable data to estimate a reliable trend "
            "for this selection."
        )
    if trend.status == "invalid_selection":
        return (
            "This selection cannot be analyzed with the current data. "
            "Try a different location or time period."
        )
    if trend.status == "analysis_failed":
        return (
            "The analysis could not complete for this selection. "
            "Try a different time period or retry later."
        )
    if trend.trend_per_decade is None or trend.ci_lower is None or trend.ci_upper is None:
        return ""

    if trend.ci_lower <= 0.0 <= trend.ci_upper:
        return (
            "This analysis does not clearly distinguish an upward or downward "
            "long-term trend from variability over this period."
        )

    direction = "upward" if trend.trend_per_decade > 0 else "downward"
    return (
        f"Under the stated assumptions, the evidence is consistent with an "
        f"{direction} long-term trend over this period. This describes the "
        f"historical record and is not a prediction of future conditions."
    )


def insufficient_or_invalid_sentence(trend: TrendResult) -> str:
    """Fallback sentence for any non-ok status."""
    return conclusion_sentence(trend)


def coverage_sentence(metadata: DatasetMetadata) -> str:
    """One-line reminder of what the data actually represents.

    Protects against the §7 ban on labeling model estimates as
    station measurements.
    """
    kind_phrases = {
        "reanalysis": (
            "This value comes from a model reanalysis grid cell, not a "
            "nearby weather station."
        ),
        "satellite": (
            "This value comes from a satellite-derived estimate over a "
            "grid cell, not a ground measurement."
        ),
        "station": (
            "This value comes from a specific ground station measurement."
        ),
        "model": (
            "This value comes from a numerical model, not a measurement."
        ),
        "synthetic": (
            "This value is synthetic demonstration data generated for "
            "interface development and is not a NASA finding."
        ),
    }
    return kind_phrases.get(metadata.data_kind, "")


def title_sentence(location_label: str, variable_label: str, trend: TrendResult) -> str:
    return f"{variable_label} near {location_label}, {_period_label(trend)}"
