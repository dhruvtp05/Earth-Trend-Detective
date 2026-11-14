"""
Stage 4 of the user journey (project brief §5): inspect the evidence.
"""

from __future__ import annotations

import streamlit as st

from services import copy as copy_module
from services.contracts import Investigation

from .explore import go_to


def render(inv: Investigation) -> None:
    meta, trend = inv.metadata, inv.trend

    st.header("Inspect the evidence")
    st.caption(
        f"Sources and method for: "
        f"{copy_module.title_sentence(inv.location_label, meta.variable_label, trend)}."
    )

    with st.container(border=True):
        st.markdown("#### Dataset")
        retrieved = (
            meta.retrieved_at.date().isoformat()
            if meta.retrieved_at
            else "Not recorded yet (to be supplied by the data team)"
        )
        st.markdown(
            f"- **Name:** {meta.dataset_name}\n"
            f"- **Version:** {meta.dataset_version}\n"
            f"- **Retrieved:** {retrieved}\n"
            f"- **How it was obtained:** area-averaged time series from NASA Giovanni. "
            f"{copy_module.SAVED_DATA_NOTICE}"
        )
        if meta.source_url:
            st.link_button("Reproduce this series in NASA Giovanni", meta.source_url)
        st.caption(copy_module.coverage_sentence(meta))

    with st.container(border=True):
        st.markdown("#### Variable")
        st.markdown(
            f"- **Name:** {meta.variable_label}\n"
            f"- **Definition:** {meta.variable_definition}\n"
            f"- **Unit:** {meta.unit}"
        )
        if meta.unit_note:
            st.caption(meta.unit_note)

    with st.container(border=True):
        st.markdown("#### Geographic coverage")
        st.markdown(
            f"- **Area:** {meta.coordinates_or_bounds}\n"
            f"- **Resolution of the source grid:** {meta.spatial_resolution}"
        )

    with st.container(border=True):
        st.markdown("#### Missing data")
        st.markdown(
            f"- **Handling:** {meta.missing_value_rules}\n"
            f"- **Months used in the trend:** {trend.valid_count}\n"
            f"- **Months left out of the trend:** {trend.excluded_count}"
        )

    with st.container(border=True):
        st.markdown("#### Statistical method")
        if inv.trend_is_placeholder:
            st.warning(copy_module.PROVISIONAL_NOTICE)
        st.markdown(
            f"- **Method:** {trend.method}\n"
            f"- **Aggregation:** {trend.aggregation}\n"
            f"- **Confidence level:** {round(trend.confidence_level * 100)}%\n"
            f"- **Period analysed:** {trend.period_start.isoformat()} to "
            f"{trend.period_end.isoformat()}"
        )
        if trend.assumptions:
            st.markdown("**Assumptions**")
            st.markdown("\n".join(f"- {item}" for item in trend.assumptions))
        if trend.warnings:
            st.markdown("**Notes**")
            st.markdown("\n".join(f"- {item}" for item in trend.warnings))

    with st.container(border=True):
        st.markdown("#### How to read the uncertainty")
        st.markdown(
            "The confidence interval is a range of trend values that are "
            "compatible with the data under the assumptions above. A wide "
            "interval means the data do not pin the trend down well. If the "
            "interval includes zero, the data cannot tell a rising trend from "
            "a falling one; that is different from showing there was no change."
        )

    if st.button("Back to the result", type="primary"):
        go_to("results")
