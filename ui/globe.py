"""
Landing-screen globe: a rotating 3D Earth that turns to North America
and highlights the study regions when "Explore regions" is pressed.

The globe library (globe.gl, MIT) and the NASA Blue Marble texture are
stored in ui/globe_component/, so the app does not depend on an outside
server. Region boxes, colours and names come from ui/region_map.py so
the globe matches the flat map on the other screens.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from . import region_map

_COMPONENT_DIR = Path(__file__).resolve().parent / "globe_component"
_globe = components.declare_component("earth_globe", path=str(_COMPONENT_DIR))


def globe_regions(available_ids: list[str]) -> list[dict]:
    """Study regions that have saved data, in the shape the globe expects."""
    regions = []
    for info in region_map.REGIONS:
        if info["key"] not in available_ids:
            continue
        west, south, east, north = info["bbox"]
        regions.append(
            {
                "id": info["key"],
                "label": info["label"].split(": ", 1)[-1],
                "description": info["desc"],
                "color": info["color"],
                "west": west,
                "south": south,
                "east": east,
                "north": north,
            }
        )
    return regions


def render(available_ids: list[str], height: int = 540) -> str | None:
    """Show the globe. Returns a region id once, when the user picks one."""
    value = _globe(
        regions=globe_regions(available_ids),
        height=height,
        key="earth_globe",
        default=None,
    )
    if not isinstance(value, dict):
        return None
    # The component keeps its last value across reruns, so each click is
    # acted on only once.
    if value.get("nonce") == st.session_state.get("globe_nonce"):
        return None
    st.session_state["globe_nonce"] = value.get("nonce")
    region = value.get("region")
    return region if region in available_ids else None
