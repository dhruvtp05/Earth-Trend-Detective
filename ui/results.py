"""
Stage 3 of the user journey (project brief §5): understand the result.

Order of elements (do not reorder without updating the product plan):
  1. Investigation title with location and dates.
  2. One plain-language result sentence.
  3. Estimated change per decade and its uncertainty range.
  4. Time-series chart with fitted trend.
  5. Short explanation of what the chart shows.
  6. Data coverage and limitations.
  7. Actions: change selection, inspect method, download data.
"""

from __future__ import annotations

import io
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import copy as copy_module
from services.contracts import Investigation


def _points_dataframe(inv: Investigation) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [p.date for p in inv.points],
            "value": [p.value for p in inv.points],
        }
    )


def _render_chart(inv: Investigation) -> None:
    df = _points_dataframe(inv)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines+markers",
            name="Observed",
            line=dict(color="#2E5EAA", width=2),
            marker=dict(size=5),
            hovertemplate="%{x|%Y}: %{y:.2f} " + inv.metadata.unit + "<extra></extra>",
        )
    )

    if inv.trend.fitted_values and inv.trend.fitted_dates:
        fig.add_trace(
            go.Scatter(
                x=inv.trend.fitted_dates,
                y=inv.trend.fitted_values,
                mode="lines",
                name="Fitted trend",
                line=dict(color="#1A1A1A", width=2, dash="dash"),
                hoverinfo="skip",
            )
        )

    # Only draw a band if Section B supplied one — never synthesize.
    if inv.trend.band_lower and inv.trend.band_upper and inv.trend.fitted_dates:
        fig.add_trace(
            go.Scatter(
                x=list(inv.trend.fitted_dates) + list(reversed(inv.trend.fitted_dates)),
                y=list(inv.trend.band_upper) + list(reversed(inv.trend.band_lower)),
                fill="toself",
                fillcolor="rgba(46, 94, 170, 0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{int(round(inv.trend.confidence_level * 100))}% band",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
        xaxis_title="Year",
        yaxis_title=f"{inv.metadata.variable_label} ({inv.metadata.unit})",
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_text_alternative(inv: Investigation) -> None:
    """Accessibility: text summary + data-table alternative to the chart."""
    df = _points_dataframe(inv)
    first = df.iloc[0]
    last = df.iloc[-1]
    summary = (
        f"Time series of {inv.metadata.variable_label.lower()} at "
        f"{inv.location_coverage}. {len(df)} annual values from "
        f"{first['date'].year} ({first['value']:.2f} {inv.metadata.unit}) to "
        f"{last['date'].year} ({last['value']:.2f} {inv.metadata.unit})."
    )
    st.caption(summary)
    with st.expander("View the data as a table"):
        st.dataframe(
            df.rename(columns={"date": "Date", "value": f"Value ({inv.metadata.unit})"}),
            use_container_width=True,
            hide_index=True,
        )


def _render_downloads(inv: Investigation) -> None:
    df = _points_dataframe(inv)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)

    summary = {
        "location_label": inv.location_label,
        "location_coverage": inv.location_coverage,
        "dataset": {
            "name": inv.metadata.dataset_name,
            "version": inv.metadata.dataset_version,
            "source_url": inv.metadata.source_url,
            "retrieved_at": inv.metadata.retrieved_at.isoformat(),
            "data_kind": inv.metadata.data_kind,
            "spatial_resolution": inv.metadata.spatial_resolution,
            "unit": inv.metadata.unit,
            "variable_label": inv.metadata.variable_label,
        },
        "trend": {
            "status": inv.trend.status,
            "period_start": inv.trend.period_start.isoformat(),
            "period_end": inv.trend.period_end.isoformat(),
            "aggregation": inv.trend.aggregation,
            "trend_per_decade": inv.trend.trend_per_decade,
            "trend_unit": inv.trend.trend_unit,
            "confidence_level": inv.trend.confidence_level,
            "ci_lower": inv.trend.ci_lower,
            "ci_upper": inv.trend.ci_upper,
            "valid_count": inv.trend.valid_count,
            "excluded_count": inv.trend.excluded_count,
            "method": inv.trend.method,
            "assumptions": inv.trend.assumptions,
            "warnings": inv.trend.warnings,
        },
        "is_demo": inv.is_demo,
    }

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download data (CSV)",
            data=csv_buf.getvalue(),
            file_name="earth_trend_detective_series.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download analysis summary (JSON)",
            data=json.dumps(summary, indent=2),
            file_name="earth_trend_detective_summary.json",
            mime="application/json",
            use_container_width=True,
        )


def render(inv: Investigation) -> None:
    # --- 1. Title -----------------------------------------------------------
    st.header(
        copy_module.title_sentence(
            inv.location_label, inv.metadata.variable_label, inv.trend
        )
    )

    if inv.is_demo:
        st.warning(f"**{copy_module.SYNTHETIC_BADGE}**", icon="⚠️")

    # --- 2. Plain-language result sentence ----------------------------------
    st.subheader(
        copy_module.result_sentence(
            inv.location_coverage, inv.metadata.variable_label, inv.trend
        )
    )

    # --- 3. Trend + uncertainty cards --------------------------------------
    if inv.trend.status == "ok" and inv.trend.trend_per_decade is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.metric(
                "Estimated trend",
                f"{inv.trend.trend_per_decade:+.2f} {inv.trend.trend_unit}",
            )
        with c2:
            if inv.trend.ci_lower is not None and inv.trend.ci_upper is not None:
                pct = int(round(inv.trend.confidence_level * 100))
                st.metric(
                    f"{pct}% confidence interval",
                    f"{inv.trend.ci_lower:+.2f} to {inv.trend.ci_upper:+.2f}",
                    help="Range consistent with the data under the stated assumptions.",
                )

        st.markdown(copy_module.uncertainty_sentence(inv.trend))
        st.info(copy_module.conclusion_sentence(inv.trend))
    else:
        # Insufficient data, invalid selection, or analysis failure.
        st.error(copy_module.conclusion_sentence(inv.trend))

    # --- 4. Chart ----------------------------------------------------------
    _render_chart(inv)

    # --- 5. Short explanation ----------------------------------------------
    st.markdown(
        "**What the chart shows.** Each marker is one annual value. "
        "The dashed line, when present, is the fitted long-term trend "
        "produced by the analysis method listed below."
    )

    # Accessibility: text summary + table.
    _render_text_alternative(inv)

    # --- 6. Coverage and limitations ---------------------------------------
    with st.container(border=True):
        st.markdown("**Data coverage and limitations**")
        st.markdown(
            f"- Dataset: {inv.metadata.dataset_name} "
            f"(v{inv.metadata.dataset_version})\n"
            f"- Coverage: {inv.metadata.coordinates_or_bounds}\n"
            f"- Spatial resolution: {inv.metadata.spatial_resolution}\n"
            f"- Observations used: {inv.trend.valid_count} "
            f"(excluded: {inv.trend.excluded_count})"
        )
        coverage_note = copy_module.coverage_sentence(inv.metadata)
        if coverage_note:
            st.caption(coverage_note)
        for w in inv.trend.warnings:
            st.caption(f"⚠ {w}")

    # --- 7. Actions --------------------------------------------------------
    st.markdown("### Next")
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Change selection", use_container_width=True):
            st.session_state["screen"] = "select"
            st.rerun()
    with a2:
        if st.button("Inspect method and sources", use_container_width=True):
            st.session_state["screen"] = "evidence"
            st.rerun()
    with a3:
        pass  # downloads live below

    _render_downloads(inv)
