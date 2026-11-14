"""
Stage 3 of the user journey (project brief §5): understand the result.

This is the data panel on the right of the results screen. Order:
  1. Controls: region, variable, time period, light/dark mode.
  2. Header: where, when and what.
  3. Plain-language result sentence, trend and uncertainty.
  4. Chart (several types) with a text description and tables.
  5. Data coverage and limitations.
  6. Continue exploring: method, compare, forecast (planned), downloads.
"""

from __future__ import annotations

import json
import statistics

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import catalog, copy as copy_module, section_a
from services.contracts import Investigation

from .explore import go_to

ACCENT = "#2E5EAA"
INK = "#1A1A1A"
MUTED = "#9AA3AF"
CHART_HEIGHT = 400

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

TREND, BARS, HISTOGRAM, SEASONAL = "Trend line", "Yearly bars", "Histogram", "Seasonal pattern"
MONTHLY = "Monthly values"


def monthly_frame(inv: Investigation) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [point.date for point in inv.points],
            "region": inv.location_label,
            "variable": inv.metadata.variable_label,
            "value": [point.value for point in inv.points],
            "unit": inv.metadata.unit,
        }
    )


def annual_frame(inv: Investigation) -> pd.DataFrame:
    trend = inv.trend
    if not trend.aggregated_dates or not trend.aggregated_values:
        return pd.DataFrame(columns=["Year", "Annual mean", "Fitted trend"])
    frame = pd.DataFrame(
        {
            "Year": [when.year for when in trend.aggregated_dates],
            "Annual mean": trend.aggregated_values,
        }
    )
    if trend.fitted_values and len(trend.fitted_values) == len(frame):
        frame["Fitted trend"] = trend.fitted_values
    return frame


def summary_dict(inv: Investigation) -> dict:
    """Reproducible summary: everything needed to interpret the numbers."""
    meta, trend = inv.metadata, inv.trend
    return {
        "region": inv.location_label,
        "coverage": inv.location_coverage,
        "dataset": {
            "name": meta.dataset_name,
            "version": meta.dataset_version,
            "source_url": meta.source_url,
            "retrieved_at": meta.retrieved_at.isoformat() if meta.retrieved_at else None,
            "data_kind": meta.data_kind,
            "spatial_resolution": meta.spatial_resolution,
            "variable": meta.variable_label,
            "variable_definition": meta.variable_definition,
            "unit": meta.unit,
            "unit_note": meta.unit_note,
            "missing_value_rules": meta.missing_value_rules,
        },
        "trend": {
            "provisional_placeholder_method": inv.trend_is_placeholder,
            "status": trend.status,
            "period_start": trend.period_start.isoformat(),
            "period_end": trend.period_end.isoformat(),
            "aggregation": trend.aggregation,
            "trend_per_decade": trend.trend_per_decade,
            "trend_unit": trend.trend_unit,
            "confidence_level": trend.confidence_level,
            "ci_lower": trend.ci_lower,
            "ci_upper": trend.ci_upper,
            "valid_count": trend.valid_count,
            "excluded_count": trend.excluded_count,
            "method": trend.method,
            "assumptions": trend.assumptions,
            "warnings": trend.warnings,
        },
    }


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


def _sync(widget_key: str, state_key: str) -> None:
    """Copy a widget's value to the selection that outlives the widget."""
    st.session_state[state_key] = st.session_state[widget_key]


def _reset_period() -> None:
    st.session_state["period"] = None  # init_state restores the full period


def render_controls() -> None:
    """Region, variable, period and display mode for the data panel.

    Each widget is refilled from the stored selection on every run, and
    writes back through a callback, so the map, the globe and this panel
    always agree.
    """
    state = st.session_state

    region_col, variable_col, mode_col = st.columns([5, 5, 3], vertical_alignment="bottom")
    with region_col:
        state["r_region"] = state["region_id"]
        st.selectbox(
            "Region",
            options=catalog.region_ids(),
            format_func=lambda region_id: catalog.region_info(region_id).label,
            key="r_region",
            on_change=_sync,
            args=("r_region", "region_id"),
        )
    with variable_col:
        state["r_variable"] = state["variable_id"]
        st.selectbox(
            "Variable",
            options=catalog.variable_ids(state["region_id"]),
            format_func=catalog.variable_label,
            key="r_variable",
            on_change=_sync,
            args=("r_variable", "variable_id"),
        )
    with mode_col:
        state["r_dark"] = bool(state.get("data_dark", False))
        st.toggle(
            "Dark mode",
            key="r_dark",
            on_change=_sync,
            args=("r_dark", "data_dark"),
            help="Changes this data panel only. The map has its own style setting.",
        )

    available = section_a.available_years(state["region_id"], state["variable_id"])
    period_col, reset_col = st.columns([10, 3], vertical_alignment="bottom")
    with period_col:
        state["r_period"] = tuple(state["period"])
        st.slider(
            f"Time period (data available {available[0]}–{available[1]})",
            min_value=available[0],
            max_value=available[1],
            key="r_period",
            on_change=_sync,
            args=("r_period", "period"),
        )
    with reset_col:
        st.button("Full period", on_click=_reset_period, width="stretch")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------


def _style(figure: go.Figure, x_title: str, y_title: str) -> go.Figure:
    figure.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=CHART_HEIGHT,
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=INK),
        bargap=0.25,
    )
    figure.update_xaxes(showgrid=True, gridcolor="#ECEEF2")
    figure.update_yaxes(showgrid=True, gridcolor="#ECEEF2")
    return figure


def _axis_label(inv: Investigation) -> str:
    return f"{inv.metadata.variable_label} ({inv.metadata.unit})"


def _add_fitted(figure: go.Figure, inv: Investigation) -> None:
    trend = inv.trend
    if trend.fitted_dates and trend.fitted_values:
        figure.add_trace(
            go.Scatter(
                x=trend.fitted_dates,
                y=trend.fitted_values,
                mode="lines",
                name="Fitted trend",
                line=dict(color=INK, width=2, dash="dash"),
                hoverinfo="skip",
            )
        )
    # A band is drawn only if Section B supplies one. A confidence interval
    # for the slope is not a band around every point.
    if trend.band_lower and trend.band_upper and trend.fitted_dates:
        figure.add_trace(
            go.Scatter(
                x=list(trend.fitted_dates) + list(reversed(trend.fitted_dates)),
                y=list(trend.band_upper) + list(reversed(trend.band_lower)),
                fill="toself",
                fillcolor="rgba(46, 94, 170, 0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{round(trend.confidence_level * 100)}% band",
                hoverinfo="skip",
            )
        )


def _trend_chart(inv: Investigation) -> tuple[go.Figure, str]:
    meta, trend = inv.metadata, inv.trend
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[point.date for point in inv.points],
            y=[point.value for point in inv.points],
            mode="lines",
            name="Monthly values",
            line=dict(color=MUTED, width=1),
            hovertemplate="%{x|%b %Y}: %{y:.3g} " + meta.unit + "<extra></extra>",
        )
    )
    has_annual = bool(trend.aggregated_dates and trend.aggregated_values)
    if has_annual:
        figure.add_trace(
            go.Scatter(
                x=trend.aggregated_dates,
                y=trend.aggregated_values,
                mode="lines+markers",
                name="Annual mean",
                line=dict(color=ACCENT, width=2),
                marker=dict(size=7),
                hovertemplate="%{x|%Y} mean: %{y:.3g} " + meta.unit + "<extra></extra>",
            )
        )
    _add_fitted(figure, inv)

    if has_annual:
        text = (
            "The thin grey line is each month's value, which rises and falls "
            "with the seasons. The blue points are yearly averages, which "
            "remove that seasonal cycle. The dashed line is the trend fitted "
            "through the yearly averages."
        )
    else:
        text = (
            "Each month's value for the selected period. No trend line is "
            "drawn because no trend was estimated."
        )
    return _style(figure, "Year", _axis_label(inv)), text


def _bar_chart(inv: Investigation) -> tuple[go.Figure, str]:
    meta, trend = inv.metadata, inv.trend
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=trend.aggregated_dates,
            y=trend.aggregated_values,
            name="Annual mean",
            marker=dict(color=ACCENT),
            hovertemplate="%{x|%Y} mean: %{y:.3g} " + meta.unit + "<extra></extra>",
        )
    )
    _add_fitted(figure, inv)
    text = (
        "Each bar is one year's average. The dashed line is the trend fitted "
        "through those averages. Bars start at zero, so small changes from "
        "year to year can look flatter here than in the trend line view."
    )
    return _style(figure, "Year", _axis_label(inv)), text


def _histogram(inv: Investigation) -> tuple[go.Figure, str]:
    meta = inv.metadata
    values = [point.value for point in inv.points]
    figure = go.Figure(
        go.Histogram(
            x=values,
            nbinsx=18,
            name="Months",
            marker=dict(color=ACCENT, line=dict(color="#FFFFFF", width=1)),
            hovertemplate="%{x} " + meta.unit + ": %{y} months<extra></extra>",
        )
    )
    text = (
        "How often each monthly value occurred in the selected period. Taller "
        "bars mean more months fell in that range. This shows the spread of "
        "values, not how they changed over time. "
        f"Lowest month: {copy_module.format_value(min(values))} {meta.unit}. "
        f"Middle (median) month: {copy_module.format_value(statistics.median(values))} {meta.unit}. "
        f"Highest month: {copy_module.format_value(max(values))} {meta.unit}."
    )
    return _style(figure, _axis_label(inv), "Number of months"), text


def seasonal_frame(inv: Investigation) -> pd.DataFrame:
    """Average of the selected period's values for each calendar month."""
    frame = pd.DataFrame(
        {"month": [p.date.month for p in inv.points], "value": [p.value for p in inv.points]}
    )
    means = frame.groupby("month")["value"].mean()
    return pd.DataFrame(
        {
            "Month": [MONTH_NAMES[month - 1] for month in means.index],
            f"Average ({inv.metadata.unit})": means.values,
        }
    )


def _seasonal_chart(inv: Investigation) -> tuple[go.Figure, str]:
    meta = inv.metadata
    frame = seasonal_frame(inv)
    months, values = frame.iloc[:, 0], frame.iloc[:, 1]
    figure = go.Figure(
        go.Bar(
            x=months,
            y=values,
            name="Average",
            marker=dict(color=ACCENT),
            hovertemplate="%{x}: %{y:.3g} " + meta.unit + "<extra></extra>",
        )
    )
    highest, lowest = values.idxmax(), values.idxmin()
    text = (
        "The average value for each calendar month over the selected period. "
        "This is the typical seasonal cycle, which the yearly averages remove "
        "before a trend is fitted. "
        f"Highest on average: {months[highest]} ({copy_module.format_value(values[highest])} {meta.unit}). "
        f"Lowest on average: {months[lowest]} ({copy_module.format_value(values[lowest])} {meta.unit})."
    )
    return _style(figure, "Calendar month", _axis_label(inv)), text


def chart_options(inv: Investigation) -> list[str]:
    """Chart types that make sense for this result."""
    if inv.trend.status == "ok" and inv.trend.aggregated_values:
        return [TREND, BARS, HISTOGRAM, SEASONAL]
    return [MONTHLY, HISTOGRAM, SEASONAL]


def _render_chart_section(inv: Investigation) -> None:
    state = st.session_state
    options = chart_options(inv)
    stored = state.get("chart_kind")
    state["r_chart"] = stored if stored in options else options[0]
    kind = st.radio(
        "Chart type",
        options=options,
        horizontal=True,
        key="r_chart",
        on_change=_sync,
        args=("r_chart", "chart_kind"),
    )

    builders = {
        TREND: _trend_chart,
        MONTHLY: _trend_chart,
        BARS: _bar_chart,
        HISTOGRAM: _histogram,
        SEASONAL: _seasonal_chart,
    }
    figure, text = builders[kind](inv)
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
    st.markdown(f"**What the chart shows.** {text}")

    # Table alternatives to the chart.
    annual = annual_frame(inv)
    meta = inv.metadata
    if kind == SEASONAL:
        with st.expander("View the calendar-month averages as a table"):
            st.dataframe(seasonal_frame(inv), width="stretch", hide_index=True)
    if not annual.empty:
        first, last = annual.iloc[0], annual.iloc[-1]
        lowest = annual.loc[annual["Annual mean"].idxmin()]
        highest = annual.loc[annual["Annual mean"].idxmax()]
        st.caption(
            f"Yearly averages, {len(annual)} years. "
            f"{int(first['Year'])}: {copy_module.format_value(first['Annual mean'])} {meta.unit}. "
            f"{int(last['Year'])}: {copy_module.format_value(last['Annual mean'])} {meta.unit}. "
            f"Lowest: {copy_module.format_value(lowest['Annual mean'])} in {int(lowest['Year'])}. "
            f"Highest: {copy_module.format_value(highest['Annual mean'])} in {int(highest['Year'])}."
        )
        with st.expander("View the yearly averages as a table"):
            st.dataframe(annual, width="stretch", hide_index=True)
    with st.expander("View the monthly values as a table"):
        table = monthly_frame(inv)[["date", "value"]].rename(
            columns={"date": "Month", "value": f"Value ({meta.unit})"}
        )
        st.dataframe(table, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------


def _render_downloads(inv: Investigation) -> None:
    slug = f"{inv.region_id}_{inv.variable_id}_{inv.trend.period_start.year}_{inv.trend.period_end.year}"
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Download data (CSV)",
            data=monthly_frame(inv).to_csv(index=False),
            file_name=f"earth_trend_detective_{slug}.csv",
            mime="text/csv",
            width="stretch",
        )
    with right:
        st.download_button(
            "Download results summary (JSON)",
            data=json.dumps(summary_dict(inv), indent=2, ensure_ascii=False),
            file_name=f"earth_trend_detective_{slug}_summary.json",
            mime="application/json",
            width="stretch",
        )


def _render_forecast_note(inv: Investigation) -> None:
    """Placeholder for the planned prediction feature. Shows no numbers."""
    st.info(
        f"**Forecasting is planned and not available yet.** It would estimate "
        f"how {inv.metadata.variable_label.lower()} in this region might "
        f"continue after {inv.trend.period_end.year}, using a prediction "
        f"method chosen and checked by the team's analysts. Nothing is "
        f"predicted here today: the trend on this page describes the past "
        f"record only and should not be read as a forecast."
    )


def render(inv: Investigation) -> None:
    meta, trend = inv.metadata, inv.trend
    state = st.session_state

    # Header: where and when, then what.
    st.caption(
        f"{inv.location_label.upper()} REGION  ·  {copy_module.period_label(trend)}  ·  "
        f"{copy_module.SAVED_DATA_NOTICE}"
    )
    st.subheader(meta.variable_label, anchor=False)

    if trend.status == "ok" and trend.trend_per_decade is not None:
        if inv.trend_is_placeholder:
            st.warning(copy_module.PROVISIONAL_NOTICE)

        st.markdown(
            f"**{copy_module.result_sentence(inv.location_coverage, meta.variable_label, trend)}**"
        )

        decimals = copy_module.trend_decimals(trend)
        unit = copy_module.base_unit(trend.trend_unit)
        percent = round(trend.confidence_level * 100)
        left, right = st.columns(2)
        with left:
            st.metric(
                f"Estimated trend ({unit} per decade)",
                copy_module.format_signed(trend.trend_per_decade, decimals),
                border=True,
            )
        with right:
            st.metric(
                f"{percent}% confidence interval ({unit} per decade)",
                f"{copy_module.format_signed(trend.ci_lower, decimals)} to "
                f"{copy_module.format_signed(trend.ci_upper, decimals)}",
                border=True,
            )
        st.markdown(copy_module.uncertainty_sentence(trend))
        st.info(copy_module.conclusion_sentence(trend))
    else:
        # Insufficient data, invalid selection or failed analysis:
        # no trend numbers are shown.
        st.error(copy_module.conclusion_sentence(trend))
        for warning in trend.warnings:
            st.markdown(warning)
        st.markdown("Choose a longer time period with the slider above.")

    if inv.points:
        _render_chart_section(inv)

    with st.container(border=True):
        st.markdown("**Data coverage and limitations**")
        lines = [
            f"- Dataset: {meta.dataset_name}, version {meta.dataset_version}",
            f"- Coverage: {meta.coordinates_or_bounds}",
            f"- Months used: {trend.valid_count} (left out: {trend.excluded_count})",
            f"- {copy_module.coverage_sentence(meta)}",
            "- The record is short for a climate trend, so the estimate is sensitive to the chosen period.",
        ]
        if meta.unit_note:
            lines.append(f"- {meta.unit_note}")
        st.markdown("\n".join(lines))

    st.markdown("#### Continue exploring")
    other_regions = [
        region
        for region in catalog.region_ids()
        if region != inv.region_id and inv.variable_id in catalog.variable_ids(region)
    ]
    columns = st.columns(3)
    with columns[0]:
        if st.button("Inspect method and sources", width="stretch"):
            go_to("evidence")
    with columns[1]:
        if other_regions:
            other = catalog.region_info(other_regions[0]).label
            if st.button(f"Compare with the {other}", width="stretch"):
                state["compare_region_id"] = other_regions[0]
                go_to("compare")
    with columns[2]:
        if st.button("Forecast (coming soon)", width="stretch"):
            state["show_forecast_note"] = not state.get("show_forecast_note", False)
    if state.get("show_forecast_note"):
        _render_forecast_note(inv)

    _render_downloads(inv)
