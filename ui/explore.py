"""
Stages 1 and 2 of the user journey (project brief §5):
  - Start an investigation (landing).
  - Choose the investigation (selection controls).

Selections are kept in st.session_state under "region_id", "variable_id"
and "period", separately from the widget keys, so they survive moving
between screens.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from services import catalog, copy as copy_module, section_a


def init_state() -> None:
    regions = catalog.region_ids()
    if not regions:
        return
    state = st.session_state
    state.setdefault("screen", "landing")

    if state.get("region_id") not in regions:
        state["region_id"] = (
            catalog.DEFAULT_REGION if catalog.DEFAULT_REGION in regions else regions[0]
        )
    variables = catalog.variable_ids(state["region_id"])
    if state.get("variable_id") not in variables:
        state["variable_id"] = (
            catalog.DEFAULT_VARIABLE if catalog.DEFAULT_VARIABLE in variables else variables[0]
        )
    state["period"] = _clamped_period(
        state.get("period"),
        section_a.available_years(state["region_id"], state["variable_id"]),
    )


def _clamped_period(
    period: tuple[int, int] | None, available: tuple[int, int]
) -> tuple[int, int]:
    """Keep a stored period inside the available years."""
    low, high = available
    if not period:
        return available
    start, end = max(period[0], low), min(period[1], high)
    return (start, end) if start <= end else available


def go_to(screen: str) -> None:
    st.session_state["screen"] = screen
    st.rerun()


def render_landing() -> None:
    st.title("Explore how a place has changed")
    st.markdown(
        "Use NASA Earth data to investigate long-term trends and "
        "understand the evidence behind them."
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### What you can find out")
        st.markdown(
            "- What is changing in a region?\n"
            "- Over what period, and by how much?\n"
            "- How uncertain is the estimated trend?\n"
            "- What can we reasonably conclude?"
        )
    with right:
        st.markdown("#### Start here")
        if st.button("Explore the Midwest example", type="primary", use_container_width=True):
            st.session_state["region_id"] = catalog.DEFAULT_REGION
            st.session_state["variable_id"] = catalog.DEFAULT_VARIABLE
            st.session_state["period"] = None
            init_state()
            go_to("results")
        st.caption(
            "Precipitation across the Midwest and Great Lakes, including Chicago. "
            + copy_module.SAVED_DATA_NOTICE
        )
        if st.button("Choose a region", use_container_width=True):
            go_to("select")


def _reset_period(available: tuple[int, int]) -> None:
    st.session_state["w_period"] = available


def render_selection() -> None:
    state = st.session_state

    st.header("Choose the investigation")
    st.caption("Pick a region, a variable and a time period. You can change them later.")

    with st.container(border=True):
        regions = catalog.region_ids()
        if state.get("w_region") not in regions:
            state["w_region"] = state["region_id"]
        region_id = st.selectbox(
            "Region",
            options=regions,
            format_func=catalog.region_option_label,
            key="w_region",
        )

        variables = catalog.variable_ids(region_id)
        if state.get("w_variable") not in variables:
            state["w_variable"] = (
                state["variable_id"] if state["variable_id"] in variables else variables[0]
            )
        variable_id = st.selectbox(
            "Variable",
            options=variables,
            format_func=catalog.variable_label,
            key="w_variable",
        )

        try:
            available = section_a.available_years(region_id, variable_id)
            _, metadata = section_a.get_series(
                region_id, variable_id, *_year_bounds(available)
            )
        except section_a.DataUnavailableError as exc:
            st.error(f"We couldn't load the saved data for this selection. {exc} Choose another region or variable.")
            return

        st.markdown(f"**What it measures.** {metadata.variable_definition} Unit: {metadata.unit}.")
        st.markdown(
            f"**Coverage.** {metadata.coordinates_or_bounds}. "
            "This is an average over the whole region, not a value for one town or station."
        )

        state["w_period"] = _clamped_period(
            state.get("w_period") or state.get("period"), available
        )
        period = st.slider(
            "Time period (years)",
            min_value=available[0],
            max_value=available[1],
            key="w_period",
            help="Only years with saved data can be selected.",
        )
        st.caption(f"Data is available for {available[0]}–{available[1]}.")
        st.button(
            "Reset to the full period",
            on_click=_reset_period,
            args=(available,),
        )

    state["region_id"] = region_id
    state["variable_id"] = variable_id
    state["period"] = period

    if period[0] == period[1]:
        st.warning("Choose a period longer than one year to estimate a trend.")

    back, forward = st.columns(2)
    with back:
        if st.button("Back", use_container_width=True):
            go_to("landing")
    with forward:
        if st.button("Investigate", type="primary", use_container_width=True):
            go_to("results")


def _year_bounds(years: tuple[int, int]) -> tuple[date, date]:
    return date(years[0], 1, 1), date(years[1], 12, 31)
