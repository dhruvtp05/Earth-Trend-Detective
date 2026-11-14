import plotly.graph_objects as go
import streamlit as st

REGIONS = [
    {
        "key": "southwest",
        "label": "Region A: US Southwest",
        "bbox": (-115.0, 31.0, -106.0, 40.0),  # West, South, East, North
        "color": "#E05A47",
        "desc": "Colorado River Basin (Arid / Snowmelt-Dependent)",
    },
    {
        "key": "midwest",
        "label": "Region B: US Midwest",
        "bbox": (-93.0, 40.0, -76.0, 49.0),
        "color": "#2B7BBA",
        "desc": "Great Lakes Basin (Humid Continental)",
    },
]


def _bbox_polygon(west: float, south: float, east: float, north: float):
    lons = [west, east, east, west, west]
    lats = [south, south, north, north, south]
    return lons, lats


def render_region_map(active_region_ids: list[str] | None = None) -> None:
    """Render an interactive North America map showing the study bounding boxes."""
    active_tokens = " ".join(active_region_ids or []).lower()
    fig = go.Figure()

    for info in REGIONS:
        west, south, east, north = info["bbox"]
        lons, lats = _bbox_polygon(west, south, east, north)
        center_lon = (west + east) / 2
        center_lat = (south + north) / 2

        is_active = not active_tokens or info["key"] in active_tokens
        opacity = 0.42 if is_active else 0.12
        line_width = 3.0 if is_active else 1.5

        hover_text = (
            f"<b>{info['label']}</b><br>"
            f"{info['desc']}<br>"
            f"Bounds: {west}° to {east}°E, {south}° to {north}°N"
        )

        fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                mode="lines",
                fill="toself",
                fillcolor=info["color"],
                opacity=opacity,
                line=dict(color=info["color"], width=line_width),
                name=info["label"],
                text=hover_text,
                hoverinfo="text",
            )
        )

        fig.add_trace(
            go.Scattergeo(
                lon=[center_lon],
                lat=[center_lat],
                mode="text",
                text=[info["label"].replace("Region ", "")],
                textfont=dict(size=12, color="#111111"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.update_geos(
        scope="north america",
        projection_type="albers usa",
        showland=True,
        landcolor="#F4F4F2",
        showlakes=True,
        lakecolor="#D6EAF8",
        showcountries=True,
        countrycolor="#CCCCCC",
        showsubunits=True,
        subunitcolor="#DCDCDC",
        lataxis_range=[24, 53],
        lonaxis_range=[-125, -67],
    )

    fig.update_layout(
        title="Study Regions Averaged from NASA MERRA-2 & GLDAS Grids",
        height=340,
        margin=dict(l=10, r=10, t=42, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01),
    )

    st.plotly_chart(fig, width="stretch")
