"""
Earth Trend Detective: entry point.

NASA Space Apps, "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

The app is one full-screen globe. Everything on it (the camera tour, the
variable tick boxes, the charts panel) runs inside the globe component;
see ui/globe.py and ui/globe_component/index.html.
"""

from __future__ import annotations

import streamlit as st

from services import catalog
from ui import globe, theme

st.set_page_config(
    page_title="Earth Trend Detective",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    if not catalog.tour_region_ids():
        st.error(
            "No saved NASA data files were found in the data folder, so there "
            "is nothing to explore yet."
        )
        return

    theme.fullscreen_page()
    globe.render()


main()
