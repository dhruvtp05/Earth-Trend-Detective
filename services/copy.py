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


# ---------------------------------------------------------------------------
# Globe view: short labels. The colour of a region on the globe follows
# `trend_direction`, so a trend whose interval includes zero is never shown
# as an increase or a decrease.
# ---------------------------------------------------------------------------

APP_TITLE = "Earth Trend Detective"

PROVISIONAL_TAG = "Provisional"

COLOR_KEY_TITLE = "Color key"

CHART_GUIDE = (
    "Monthly values show the swings from season to season. Annual means "
    "average each calendar year. The fitted trend is the straight line that "
    "best fits the annual means. The shaded band shows how uncertain that "
    "line is: a wider band means the data pin it down less well."
)

SHORT_RECORD_NOTE = (
    "The record is short for a climate trend, so the estimate is sensitive "
    "to the chosen period."
)

UNCERTAINTY_GUIDE = (
    "The confidence interval is a range of trend values that are compatible "
    "with the data under the analysis assumptions. A wide interval means the "
    "data do not pin the trend down well. If the interval includes zero, the "
    "data cannot tell a rising trend from a falling one; that is different "
    "from showing there was no change."
)

DIRECTION_LABELS = {
    "increase": "Increase",
    "decrease": "Decrease",
    "inconclusive": "Inconclusive",
    "none": "No trend estimated",
}

# Plain-language headline for each direction. "No clear trend" means the
# data cannot tell a rise from a fall; it must never become "no change".
HEADLINE_LABELS = {
    "increase": "Upward trend",
    "decrease": "Downward trend",
    "inconclusive": "No clear trend",
    "none": "No trend estimated",
}

CHART_SERIES_LABELS = {
    "monthly": "Monthly values",
    "annual": "Annual mean",
    "fitted": "Fitted trend",
}


def trend_direction(trend: TrendResult) -> str:
    """'increase', 'decrease', 'inconclusive' or 'none' (no trend estimated).

    Decided from the raw interval: a direction is reported only when the
    confidence interval excludes zero.
    """
    if (
        trend.status != "ok"
        or trend.trend_per_decade is None
        or trend.ci_lower is None
        or trend.ci_upper is None
    ):
        return "none"
    if interval_includes_zero(trend):
        return "inconclusive"
    return "increase" if trend.trend_per_decade > 0 else "decrease"


def trend_headline(trend: TrendResult) -> str:
    """Two or three plain words for the result, following `trend_direction`."""
    return HEADLINE_LABELS[trend_direction(trend)]


def significance_badge(trend: TrendResult) -> str:
    """Short badge shown beside a trend value."""
    direction = trend_direction(trend)
    if direction in ("increase", "decrease"):
        return "Significant"
    return DIRECTION_LABELS[direction]


def significance_note(trend: TrendResult) -> str:
    """One sentence saying what the badge means, and what it does not."""
    direction = trend_direction(trend)
    if direction == "none":
        return ""
    percent = round(trend.confidence_level * 100)
    if direction == "inconclusive":
        return (
            f"Inconclusive: the {percent}% confidence interval includes zero, "
            "so no direction is shown."
        )
    return (
        f"Statistically significant: the {percent}% confidence interval does "
        "not include zero. This does not say how large or important the "
        "change is."
    )


def trend_unit_label(trend: TrendResult) -> str:
    """'mm/day/decade' -> 'mm/day per decade'."""
    return f"{base_unit(trend.trend_unit)} per decade"


def trend_value_text(trend: TrendResult) -> str:
    """Signed trend with the decimals used everywhere else, or ''."""
    if trend.status != "ok" or trend.trend_per_decade is None:
        return ""
    return format_signed(trend.trend_per_decade, trend_decimals(trend))


def interval_text(trend: TrendResult) -> str:
    """'-0.17 to +0.12', or ''."""
    if trend.status != "ok" or trend.ci_lower is None or trend.ci_upper is None:
        return ""
    decimals = trend_decimals(trend)
    return f"{format_signed(trend.ci_lower, decimals)} to {format_signed(trend.ci_upper, decimals)}"


def band_label(trend: TrendResult) -> str:
    return f"{round(trend.confidence_level * 100)}% confidence band for the fitted trend"


def stripes_legend(first_year: int, last_year: int) -> str:
    """How yearly values are drawn inside each region on the globe."""
    return (
        f"Each stripe is one year, {first_year} to {last_year} from west to "
        "east. Within a row, darker means a lower yearly average and "
        "brighter means a higher one."
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


PREDICTION_TEXT = {
    "title": "Probabilistic prediction",
    "intro": "Experimental monthly projections for the selected region, using only the saved NASA record.",
    "origin_note": "The forecast starts from the last saved observation, not today's weather. Missing recent months increase the forecast lead.",
    "range_note": "The shaded area is a nominal 80% prediction range estimated from earlier forecast errors. Held-out coverage below shows how often that range actually contained later values; it is not a guarantee.",
    "hazard_title": "Floods, droughts and these factors",
    "hazard_note": "These monthly regional averages have no observed disaster labels. They cannot establish a probability of flooding, drought, property damage or other natural disasters. Flood and drought probabilities are unavailable from these files.",
    "dry_note": "A lower-soil-moisture month means topsoil water below the historical lower quartile for the same calendar month. It is a dryness indicator, not a drought diagnosis.",
    "wet_note": "A higher-runoff month means modeled surface runoff above the historical upper quartile for the same calendar month. It is a wetness indicator, not a flood prediction.",
    "tail_note": "Indicator probabilities are shown only when the matching-lead backtest has enough positive and negative cases, improves Brier score over the seasonal reference, and passes the interval and baseline checks. Otherwise they are unavailable.",
    "limited": "Limited backtest skill: treat the displayed values and range as exploratory model output.",
    "method": "A seasonal baseline and a damped seasonal-trend model are compared on 48 earlier monthly targets. Their log-scale forecast errors form an empirical distribution. The selected model is then tested on 24 later targets at the same lead as the projection. Earlier test observations become available only at subsequent forecast origins.",
    "no_joint": "The four variables come from different products and grids. Their separate probabilities are not combined into a disaster probability or a closed water budget.",
}
