"""
Earth Trend Detective: entry point.

NASA Space Apps, "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

Sets the page configuration, keeps the user's selections in session
state and routes between the screens of project brief §5.
"""

from __future__ import annotations

import streamlit as st

from services import catalog, investigate, section_a
from services.contracts import Investigation
from ui import compare, evidence, explore, region_map, results

st.set_page_config(
    page_title="Earth Trend Detective",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SELECTION_KEYS = (
    "screen", "region_id", "variable_id", "period", "compare_region_id",
    "w_region", "w_variable", "w_period",
)


def _header() -> None:
    title, action = st.columns([4, 1], vertical_alignment="center")
    with title:
        st.markdown("**Earth Trend Detective**")
        st.caption("NASA Space Apps · UIC Computer Science and Data Science")
    with action:
        if st.session_state.get("screen", "landing") != "landing":
            if st.button("Start over", use_container_width=True):
                for key in SELECTION_KEYS:
                    st.session_state.pop(key, None)
                st.rerun()
    st.divider()


def _load(region_id: str) -> Investigation | None:
    """Load the current selection for one region, or show how to recover."""
    state = st.session_state
    start_year, end_year = state["period"]
    try:
        return investigate.load(region_id, state["variable_id"], start_year, end_year)
    except section_a.DataUnavailableError as exc:
        st.error(f"We couldn't load the saved data for this selection. {exc}")
    except Exception as exc:  # noqa: BLE001 - never show stale or partial results
        st.error("Something went wrong while preparing this result, so nothing is shown.")
        st.caption(f"Details: {exc}")
    if st.button("Choose a different selection", type="primary"):
        explore.go_to("select")
    return None


def main() -> None:
    _header()

    if not catalog.region_ids():
        st.error(
            "No saved NASA data files were found in the data folder, so there "
            "is nothing to explore yet."
        )
        return

    explore.init_state()
    state = st.session_state
    screen = state["screen"]

    if screen == "landing":
        explore.render_landing()
    elif screen == "select":
        explore.render_selection()
        region_map.render_region_map()
    elif screen == "results":
        inv = _load(state["region_id"])
        if inv is not None:
            results.render(inv)
            region_map.render_region_map([state["region_id"]])
    elif screen == "evidence":
        inv = _load(state["region_id"])
        if inv is not None:
            evidence.render(inv)
    elif screen == "compare":
        other = state.get("compare_region_id")
        if other is None or state["variable_id"] not in catalog.variable_ids(other):
            explore.go_to("results")
        loaded = [_load(state["region_id"]), _load(other)]
        if all(inv is not None for inv in loaded):
            compare.render(loaded)  # type: ignore[arg-type]
            region_map.render_region_map([state["region_id"], other])
    else:
        explore.go_to("landing")


main()