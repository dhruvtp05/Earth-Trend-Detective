"""
Page-level styling: page width per screen, the two-panel results layout
and the data panel's own light/dark mode.
"""

from __future__ import annotations

import streamlit as st

MAP_PANEL_KEY = "map_panel"
DATA_PANEL_KEY = "data_panel"

_NARROW = """
[data-testid="stMainBlockContainer"], .block-container { max-width: 46rem; }
"""

_SPLIT = f"""
[data-testid="stMainBlockContainer"], .block-container {{
    max-width: 96rem; padding-top: 3.5rem;
}}
.st-key-{DATA_PANEL_KEY} {{
    background: #FFFFFF; border: 1px solid #D9DDE4; border-radius: 14px;
    padding: 1.1rem 1.3rem 1.3rem;
}}
/* Keep the map in view while the data panel scrolls (wide screens only). */
@media (min-width: 900px) {{
    [data-testid="stColumn"]:has(.st-key-{MAP_PANEL_KEY}) {{
        position: sticky; top: 4rem; align-self: flex-start;
    }}
}}
"""

# Dark mode for the data panel alone. Inverting lightness and rotating the
# hue back turns every element in the panel dark, including charts and
# tables, while keeping blues blue and oranges orange.
_DATA_DARK = f"""
.st-key-{DATA_PANEL_KEY} {{
    filter: invert(0.92) hue-rotate(180deg);
    border-color: #C9CED6;
}}
"""


def _inject(css: str) -> None:
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def narrow_page() -> None:
    """Single-column reading width for the landing and text screens."""
    _inject(_NARROW)


def split_page(data_dark: bool) -> None:
    """Wide two-panel layout for the results screen."""
    _inject(_SPLIT + (_DATA_DARK if data_dark else ""))
