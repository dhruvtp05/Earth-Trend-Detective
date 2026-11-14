"""
Stage 4 of the user journey (project brief §5): inspect the evidence.
"""

from __future__ import annotations

import streamlit as st

from services.contracts import Investigation
from services import copy as copy_module


def render(inv: Investigation) -> None:
    st.header("Inspect the evidence")
    st.caption(
        "Everything a careful reader needs to reproduce and interpret "
        "this investigation."
    )

    if inv.is_demo:
        st.warning(f"**{copy_module.SYNTHETIC_BADGE}**", icon="⚠️")

    with st.container(border=True):
        st.markdown("#### Dataset")
        st.markdown(
            f"- **Name**: {inv.metadata.dataset_name}\n"
            f"- **Version**: {inv.metadata.dataset_version}\n"
            f"- **Source**: [{inv.metadata.source_url}]({inv.metadata.source_url})\n"
            f"- **Retrieved**: {inv.metadata.retrieved_at.date().isoformat()}\n"
            f"- **Data kind**: {inv.metadata.data_kind}"
        )
        note = copy_module.coverage_sentence(inv.metadata)
        if note:
            st.caption(note)

    with st.container(border=True):
        st.markdown("#### Variable")
        st.markdown(
            f"- **Label**: {inv.metadata.variable_label}\n"
            f"- **Unit**: {inv.metadata.unit}\n"
            f"- **Definition**: {inv.metadata.variable_definition}"
        )

    with st.container(border=True):
        st.markdown("#### Geographic coverage")
        st.markdown(
            f"- **Area**: {inv.metadata.coordinates_or_bounds}\n"
            f"- **Resolution**: {inv.metadata.spatial_resolution}"
        )

    with st.container(border=True):
        st.markdown("#### Missing data")
        st.markdown(
            f"- **Handling**: {inv.metadata.missing_value_rules}\n"
            f"- **Valid observations used**: {inv.trend.valid_count}\n"
            f"- **Excluded observations**: {inv.trend.excluded_count}"
        )

    with st.container(border=True):
        st.markdown("#### Statistical method")
        st.markdown(
            f"- **Method**: {inv.trend.method}\n"
            f"- **Aggregation**: {inv.trend.aggregation}\n"
            f"- **Confidence level**: {int(round(inv.trend.confidence_level * 100))}%\n"
            f"- **Period analyzed**: "
            f"{inv.trend.period_start.isoformat()} to {inv.trend.period_end.isoformat()}"
        )
        if inv.trend.assumptions:
            st.markdown("**Assumptions**")
            for a in inv.trend.assumptions:
                st.markdown(f"- {a}")
        if inv.trend.warnings:
            st.markdown("**Warnings**")
            for w in inv.trend.warnings:
                st.markdown(f"- {w}")

    st.markdown("---")
    if st.button("Back to results", type="primary"):
        st.session_state["screen"] = "results"
        st.rerun()
