"""
Stages 1 and 2 of the user journey (project brief §5):
  - Start an investigation (landing).
  - Choose the investigation (selection controls).
"""

from __future__ import annotations

from datetime import date

import streamlit as st


# The MVP ships Concept A only: Chicago temperature. The selection
# UI is deliberately constrained until Sections A and B validate
# additional variables and locations.
SUPPORTED_LOCATIONS = {
    "chicago": "Chicago area",
}
SUPPORTED_VARIABLES = {
    "t2m_annual_mean": "Near-surface air temperature (annual mean)",
}

AVAILABLE_YEAR_MIN = 1980
AVAILABLE_YEAR_MAX = 2024


def _init_state() -> None:
    st.session_state.setdefault("screen", "landing")
    st.session_state.setdefault("location_id", "chicago")
    st.session_state.setdefault("variable_id", "t2m_annual_mean")
    st.session_state.setdefault(
        "period",
        (AVAILABLE_YEAR_MIN, AVAILABLE_YEAR_MAX),
    )


def render_landing() -> None:
    _init_state()

    st.title("Explore how a place has changed")
    st.markdown(
        "Use NASA Earth data to investigate long-term trends and "
        "understand the evidence behind them."
    )

    st.markdown("---")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("#### What this app can answer")
        st.markdown(
            "- **What** is changing in a place you care about?\n"
            "- **Where** and over **what period**?\n"
            "- **How much** is it changing, per decade?\n"
            "- **How uncertain** is the estimated trend?\n"
            "- **What** can we reasonably conclude from the evidence?"
        )
    with col_b:
        st.markdown("#### Start here")
        if st.button(
            "Explore the Chicago example",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["screen"] = "select"
            st.rerun()
        st.caption(
            "A verified saved example. You can change the location and "
            "period on the next screen."
        )


def render_selection() -> None:
    _init_state()

    st.header("Choose the investigation")
    st.caption(
        "Pick a location, a variable, and a time period. "
        "Only validated combinations are enabled."
    )

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            loc_label = st.selectbox(
                "Location",
                options=list(SUPPORTED_LOCATIONS.values()),
                index=0,
                help="Additional locations will be enabled as Section A "
                "validates their coverage.",
            )
            st.session_state["location_id"] = next(
                k for k, v in SUPPORTED_LOCATIONS.items() if v == loc_label
            )
        with c2:
            var_label = st.selectbox(
                "Variable",
                options=list(SUPPORTED_VARIABLES.values()),
                index=0,
                help="Temperature is the only enabled variable until "
                "another is validated.",
            )
            st.session_state["variable_id"] = next(
                k for k, v in SUPPORTED_VARIABLES.items() if v == var_label
            )

        st.markdown(
            "*Mean of the model-reanalyzed near-surface air temperature "
            "over each calendar year, in degrees Celsius.*"
        )
        st.caption(
            "Coverage: nearest reanalysis grid cell to the selected location "
            "(not a local weather station)."
        )

        period = st.slider(
            "Time period",
            min_value=AVAILABLE_YEAR_MIN,
            max_value=AVAILABLE_YEAR_MAX,
            value=st.session_state["period"],
            step=1,
            help=f"Available years: {AVAILABLE_YEAR_MIN}–{AVAILABLE_YEAR_MAX}.",
        )
        st.session_state["period"] = period

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("Back", use_container_width=True):
            st.session_state["screen"] = "landing"
            st.rerun()
    with col_r:
        if st.button(
            "Investigate",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["screen"] = "results"
            st.rerun()


def selected_period_dates() -> tuple[date, date]:
    start_year, end_year = st.session_state.get(
        "period", (AVAILABLE_YEAR_MIN, AVAILABLE_YEAR_MAX)
    )
    return date(start_year, 1, 1), date(end_year, 12, 31)
