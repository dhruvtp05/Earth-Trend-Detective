"""
Earth Trend Detective — entry point.

NASA Space Apps 2026 — "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

This file:
  - sets global page configuration,
  - initializes session state,
  - routes between the four screens from project brief §5,
  - loads the labeled synthetic fixture while Sections A and B
    deliver their real outputs.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from services import demo
from services import section_a, section_b
from services.contracts import Investigation
from ui import evidence, explore, results


# ---------------------------------------------------------------------------
# Global page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Earth Trend Detective",
    page_icon="🌎",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Data loading
#
# For the MVP demo path we read from the labeled synthetic fixture.
# To enable the real path, set USE_LIVE_DATA = True and ensure
# services.section_a and services.section_b are pointed at the real
# implementations.
# ---------------------------------------------------------------------------

USE_LIVE_DATA = False


def _load_investigation(
    location_id: str,
    variable_id: str,
    period_start: date,
    period_end: date,
) -> Investigation:
    if not USE_LIVE_DATA:
        # Deterministic, labeled synthetic fixture.
        return demo.get_investigation(
            period_start=period_start, period_end=period_end
        )

    with st.status("Loading the selected NASA data…", expanded=False) as status:
        points, metadata = section_a.get_series(
            location_id=location_id,
            variable=variable_id,
            start=period_start,
            end=period_end,
        )
        status.update(label="Calculating the trend…")
        trend = section_b.estimate_trend(
            points=points,
            period_start=period_start,
            period_end=period_end,
        )
        status.update(label="Ready.", state="complete")

    return Investigation(
        location_label="Chicago area",
        location_coverage=metadata.coordinates_or_bounds,
        points=points,
        metadata=metadata,
        trend=trend,
        is_demo=False,
    )


# ---------------------------------------------------------------------------
# Header + routing
# ---------------------------------------------------------------------------

def _header() -> None:
    cols = st.columns([1, 6, 2])
    with cols[0]:
        st.markdown("### 🌎")
    with cols[1]:
        st.markdown("### Earth Trend Detective")
        st.caption("NASA Space Apps · UIC CS + Data Science")
    with cols[2]:
        if st.session_state.get("screen") != "landing":
            if st.button("Restart", use_container_width=True):
                for k in ("screen", "period", "location_id", "variable_id"):
                    st.session_state.pop(k, None)
                st.rerun()


def main() -> None:
    _header()
    st.markdown("---")

    screen = st.session_state.get("screen", "landing")

    if screen == "landing":
        explore.render_landing()
    elif screen == "select":
        explore.render_selection()
    elif screen == "results":
        period_start, period_end = explore.selected_period_dates()
        try:
            inv = _load_investigation(
                location_id=st.session_state.get("location_id", "chicago"),
                variable_id=st.session_state.get("variable_id", "t2m_annual_mean"),
                period_start=period_start,
                period_end=period_end,
            )
        except Exception as exc:  # pragma: no cover
            st.error(
                "We couldn’t load the data. Retry, or explore the saved example."
            )
            st.caption(f"Details: {exc}")
            if st.button("Load the saved example"):
                st.session_state["period"] = (1980, 2024)
                st.rerun()
            return
        results.render(inv)
    elif screen == "evidence":
        period_start, period_end = explore.selected_period_dates()
        inv = _load_investigation(
            location_id=st.session_state.get("location_id", "chicago"),
            variable_id=st.session_state.get("variable_id", "t2m_annual_mean"),
            period_start=period_start,
            period_end=period_end,
        )
        evidence.render(inv)
    else:
        st.session_state["screen"] = "landing"
        st.rerun()


if __name__ == "__main__":
    main()
else:
    main()
