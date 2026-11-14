"""
Page-level styling: the globe fills the whole browser window.

Streamlit's header, toolbar and footer are hidden, and the globe
component's frame is pinned to the viewport. The selectors below are
Streamlit's own element names, which is why requirements.txt pins the
Streamlit version: check this file when upgrading.

Page padding and colours are not set here: they are theme options in
.streamlit/config.toml.
"""

from __future__ import annotations

import streamlit as st

from .globe import STAGE_KEY

BACKGROUND = "#03050A"   # also set in .streamlit/config.toml

_FULLSCREEN = f"""
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BACKGROUND} !important;
    overflow: hidden !important;
}}
header, footer, #MainMenu,
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"], [data-testid="stBottom"] {{
    display: none !important;
}}
.st-key-{STAGE_KEY} iframe {{
    position: fixed !important;
    top: 0; left: 0;
    width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
    border: 0 !important;
    z-index: 999990;
    background: {BACKGROUND};
}}
"""


def fullscreen_page() -> None:
    """Remove the page chrome and pin the globe to the viewport."""
    st.html(f"<style>{_FULLSCREEN}</style>")
