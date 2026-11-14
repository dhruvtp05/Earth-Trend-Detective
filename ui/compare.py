"""
"Compare Two Places": the same variable, period and method for two regions.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import copy as copy_module
from services.contracts import Investigation

from .explore import go_to

# Colour is paired with marker shape and line style, so the regions can be
# told apart without relying on colour.
STYLES = [
    dict(color="#2E5EAA", symbol="circle", dash="solid"),
    dict(color="#B85C00", symbol="square", dash="solid"),
]


def _region_card(inv: Investigation) -> None:
    trend = inv.trend
    with st.container(border=True):
        st.markdown(f"#### {inv.location_label}")
        st.caption(inv.metadata.coordinates_or_bounds)
        if trend.status == "ok" and trend.trend_per_decade is not None:
            decimals = copy_module.trend_decimals(trend)
            unit = copy_module.base_unit(trend.trend_unit)
            st.metric(
                f"Estimated trend ({unit} per decade)",
                copy_module.format_signed(trend.trend_per_decade, decimals),
            )
            st.markdown(copy_module.uncertainty_sentence(trend))
            st.markdown(copy_module.conclusion_sentence(trend))
        else:
            st.error(copy_module.conclusion_sentence(trend))


def _chart(investigations: list[Investigation]) -> None:
    figure = go.Figure()
    for inv, style in zip(investigations, STYLES):
        trend = inv.trend
        if not trend.aggregated_dates or not trend.aggregated_values:
            continue
        figure.add_trace(
            go.Scatter(
                x=trend.aggregated_dates,
                y=trend.aggregated_values,
                mode="lines+markers",
                name=f"{inv.location_label}: annual mean",
                line=dict(color=style["color"], width=2),
                marker=dict(size=7, symbol=style["symbol"]),
                hovertemplate=inv.location_label
                + " %{x|%Y}: %{y:.3g} "
                + inv.metadata.unit
                + "<extra></extra>",
            )
        )
        if trend.fitted_dates and trend.fitted_values:
            figure.add_trace(
                go.Scatter(
                    x=trend.fitted_dates,
                    y=trend.fitted_values,
                    mode="lines",
                    name=f"{inv.location_label}: fitted trend",
                    line=dict(color=style["color"], width=2, dash="dash"),
                    hoverinfo="skip",
                )
            )

    meta = investigations[0].metadata
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
    st.plotly_chart(figure, width="stretch")


def _table(investigations: list[Investigation]) -> pd.DataFrame:
    frames = []
    for inv in investigations:
        trend = inv.trend
        if trend.aggregated_dates and trend.aggregated_values:
            frames.append(
                pd.Series(
                    trend.aggregated_values,
                    index=[when.year for when in trend.aggregated_dates],
                    name=f"{inv.location_label} ({inv.metadata.unit})",
                )
            )
    if not frames:
        return pd.DataFrame()
    table = pd.concat(frames, axis=1)
    table.index.name = "Year"
    return table.reset_index()


def render(investigations: list[Investigation]) -> None:
    first = investigations[0]
    names = " and the ".join(inv.location_label for inv in investigations)
    st.header(
        f"{first.metadata.variable_label}: the {names}, "
        f"{copy_module.period_label(first.trend)}"
    )
    st.caption(
        "Both regions use the same dataset, period, unit and method. "
        + copy_module.SAVED_DATA_NOTICE
    )

    if first.trend_is_placeholder and any(inv.trend.status == "ok" for inv in investigations):
        st.warning(copy_module.PROVISIONAL_NOTICE)

    for column, inv in zip(st.columns(len(investigations)), investigations):
        with column:
            _region_card(inv)

    st.info(
        "Each interval describes its own region. This view does not test "
        "whether the two trends differ from each other, and overlapping "
        "intervals do not show that the regions are changing in the same way."
    )

    _chart(investigations)
    st.markdown(
        "**What the chart shows.** Yearly averages for each region, with the "
        "trend fitted to each as a dashed line of the same colour. The regions "
        "differ in their typical level as well as in their trend."
    )
    table = _table(investigations)
    if not table.empty:
        with st.expander("View the yearly averages as a table"):
            st.dataframe(table, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        if st.button(f"Back to the {first.location_label} result", width="stretch"):
            go_to("results")
    with right:
        if st.button("Change selection", width="stretch"):
            go_to("select")
