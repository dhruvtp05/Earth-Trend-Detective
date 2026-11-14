"""
Stage 3 of the user journey (project brief §5): understand the result.

Order of elements:
  1. Investigation title with location and dates.
  2. One plain-language result sentence.
  3. Estimated change per decade and its uncertainty range.
  4. Time-series chart with fitted trend.
  5. Short explanation of what the chart shows.
  6. Data coverage and limitations.
  7. Actions: change selection, inspect method, compare, download.
"""

from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import catalog, copy as copy_module
from services.contracts import Investigation

from .explore import go_to

ACCENT = "#2E5EAA"
INK = "#1A1A1A"
MUTED = "#9AA3AF"


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


def _render_chart(inv: Investigation) -> None:
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
    if trend.aggregated_dates and trend.aggregated_values:
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

    figure.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        xaxis_title="Year",
        yaxis_title=f"{meta.variable_label} ({meta.unit})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    figure.update_xaxes(showgrid=True, gridcolor="#ECEEF2")
    figure.update_yaxes(showgrid=True, gridcolor="#ECEEF2")
    st.plotly_chart(figure, use_container_width=True)


def _render_chart_text(inv: Investigation) -> None:
    """Text summary and table alternative for the chart."""
    meta, trend = inv.metadata, inv.trend
    annual = annual_frame(inv)

    if trend.status == "ok" and not annual.empty:
        first, last = annual.iloc[0], annual.iloc[-1]
        lowest = annual.loc[annual["Annual mean"].idxmin()]
        highest = annual.loc[annual["Annual mean"].idxmax()]
        st.markdown(
            "**What the chart shows.** The thin grey line is each month's value, "
            "which rises and falls with the seasons. The blue points are yearly "
            "averages, which remove that seasonal cycle. The dashed line is the "
            "trend fitted through the yearly averages."
        )
        st.caption(
            f"Chart summary: {len(annual)} yearly averages of "
            f"{meta.variable_label.lower()} for {inv.location_coverage}. "
            f"{int(first['Year'])}: {copy_module.format_value(first['Annual mean'])} {meta.unit}. "
            f"{int(last['Year'])}: {copy_module.format_value(last['Annual mean'])} {meta.unit}. "
            f"Lowest: {copy_module.format_value(lowest['Annual mean'])} in {int(lowest['Year'])}. "
            f"Highest: {copy_module.format_value(highest['Annual mean'])} in {int(highest['Year'])}."
        )
        with st.expander("View the yearly averages as a table"):
            st.dataframe(annual, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            "**What the chart shows.** Each month's value for the selected period. "
            "No trend line is drawn because no trend was estimated."
        )

    with st.expander("View the monthly values as a table"):
        table = monthly_frame(inv)[["date", "value"]].rename(
            columns={"date": "Month", "value": f"Value ({meta.unit})"}
        )
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_downloads(inv: Investigation) -> None:
    slug = f"{inv.region_id}_{inv.variable_id}_{inv.trend.period_start.year}_{inv.trend.period_end.year}"
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Download data (CSV)",
            data=monthly_frame(inv).to_csv(index=False),
            file_name=f"earth_trend_detective_{slug}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "Download results summary (JSON)",
            data=json.dumps(summary_dict(inv), indent=2, ensure_ascii=False),
            file_name=f"earth_trend_detective_{slug}_summary.json",
            mime="application/json",
            use_container_width=True,
        )


def render(inv: Investigation) -> None:
    meta, trend = inv.metadata, inv.trend

    # 1. Title
    st.header(copy_module.title_sentence(inv.location_label, meta.variable_label, trend))
    st.caption(copy_module.SAVED_DATA_NOTICE)

    if trend.status == "ok" and trend.trend_per_decade is not None:
        if inv.trend_is_placeholder:
            st.warning(copy_module.PROVISIONAL_NOTICE)

        # 2. Result sentence
        st.markdown(
            f"##### {copy_module.result_sentence(inv.location_coverage, meta.variable_label, trend)}"
        )

        # 3. Trend and uncertainty
        decimals = copy_module.trend_decimals(trend)
        unit = copy_module.base_unit(trend.trend_unit)
        percent = round(trend.confidence_level * 100)
        left, right = st.columns(2)
        with left:
            st.metric(
                f"Estimated trend ({unit} per decade)",
                copy_module.format_signed(trend.trend_per_decade, decimals),
            )
        with right:
            st.metric(
                f"{percent}% confidence interval ({unit} per decade)",
                f"{copy_module.format_signed(trend.ci_lower, decimals)} to "
                f"{copy_module.format_signed(trend.ci_upper, decimals)}",
            )
        st.markdown(copy_module.uncertainty_sentence(trend))
        st.info(copy_module.conclusion_sentence(trend))
    else:
        # Insufficient data, invalid selection or failed analysis:
        # no trend numbers are shown.
        st.error(copy_module.conclusion_sentence(trend))
        for warning in trend.warnings:
            st.markdown(warning)
        if st.button("Change the time period", type="primary"):
            go_to("select")

    # 4–5. Chart and its description
    if inv.points:
        _render_chart(inv)
        _render_chart_text(inv)

    # 6. Coverage and limitations
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

    # 7. Actions
    st.markdown("#### Continue exploring")
    other_regions = [
        region
        for region in catalog.region_ids()
        if region != inv.region_id and inv.variable_id in catalog.variable_ids(region)
    ]
    columns = st.columns(3 if other_regions else 2)
    with columns[0]:
        if st.button("Change selection", use_container_width=True):
            go_to("select")
    with columns[1]:
        if st.button("Inspect method and sources", use_container_width=True):
            go_to("evidence")
    if other_regions:
        with columns[2]:
            other = catalog.region_info(other_regions[0]).label
            if st.button(f"Compare with the {other}", use_container_width=True):
                st.session_state["compare_region_id"] = other_regions[0]
                go_to("compare")

    _render_downloads(inv)
