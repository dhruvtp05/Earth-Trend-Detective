"""
Results-screen map: a pan-and-zoom map without place names that opens
close in on the selected region and pulls back to frame it.

Leaflet (BSD 2-Clause) is stored in ui/map_component/. Map tiles are
loaded from Esri's public tile services at run time (no API key), so
the map needs an internet connection; the rest of the app does not.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from . import globe

_COMPONENT_DIR = Path(__file__).resolve().parent / "map_component"
_map = components.declare_component("focus_map", path=str(_COMPONENT_DIR))


def render(available_ids: list[str], active_id: str, height: int = 620) -> str | None:
    """Show the map. Returns a region id once, when the user switches region."""
    value = _map(
        regions=globe.globe_regions(available_ids),
        active=active_id,
        intro_id=st.session_state.get("map_intro_id"),
        height=height,
        key="focus_map",
        default=None,
    )
    if not isinstance(value, dict):
        return None
    if value.get("nonce") == st.session_state.get("map_nonce"):
        return None
    st.session_state["map_nonce"] = value.get("nonce")
    region = value.get("region")
    return region if region in available_ids and region != active_id else None
