"""
The globe: the whole interface.

Python prepares every region/variable result once and hands it to the
globe component in a single payload. Ticking variables, the camera tour
and the charts panel then run entirely in the browser, with no reruns.

The globe library (globe.gl, MIT) and the NASA Blue Marble texture are
stored in ui/globe_component/, so the app does not depend on an outside
server. Every sentence and label that states a result comes from
services/copy.py.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

from services import catalog, copy as copy_module, investigate, prediction, section_a, section_b
from services.contracts import Investigation

STAGE_KEY = "globe_stage"

_COMPONENT_DIR = Path(__file__).resolve().parent / "globe_component"
_globe = components.declare_component("earth_globe", path=str(_COMPONENT_DIR))


def _round(value: float) -> float:
    """Five significant figures: enough for the charts, small to send."""
    return float(f"{value:.5g}")


def globe_regions() -> list[dict]:
    """Study regions with saved data and a known box, in camera-tour order."""
    regions = []
    for region_id in catalog.tour_region_ids():
        info = catalog.region_info(region_id)
        west, south, east, north = info.bbox  # type: ignore[misc]
        regions.append(
            {
                "id": info.id,
                "label": info.label,
                "letter": info.letter,
                "description": info.description,
                "west": west,
                "south": south,
                "east": east,
                "north": north,
            }
        )
    return regions


def _result(inv: Investigation) -> dict:
    """One region/variable result in the shape the globe component draws."""
    meta, trend = inv.metadata, inv.trend
    ok = trend.status == "ok" and trend.trend_per_decade is not None

    annual: dict = {"years": [], "mean": [], "fit": [], "lo": [], "hi": []}
    if trend.aggregated_dates and trend.aggregated_values:
        annual["years"] = [when.year for when in trend.aggregated_dates]
        annual["mean"] = [_round(value) for value in trend.aggregated_values]
    if trend.fitted_values:
        annual["fit"] = [_round(value) for value in trend.fitted_values]
    # A band is drawn only when the analysis supplies one.
    if trend.band_lower and trend.band_upper:
        annual["lo"] = [_round(value) for value in trend.band_lower]
        annual["hi"] = [_round(value) for value in trend.band_upper]

    facts = [
        ["Dataset", f"{meta.dataset_name}, version {meta.dataset_version}"],
        ["Coverage", meta.coordinates_or_bounds],
        ["Source grid", meta.spatial_resolution],
        ["Months used", f"{trend.valid_count} (left out: {trend.excluded_count})"],
        ["Method", trend.method],
        ["Aggregation", trend.aggregation],
    ]
    notes = [copy_module.coverage_sentence(meta), meta.unit_note]
    if not ok:
        notes += trend.warnings

    return {
        "status": trend.status,
        "direction": copy_module.trend_direction(trend),
        "headline": copy_module.trend_headline(trend),
        "badge": copy_module.significance_badge(trend),
        "badge_note": copy_module.significance_note(trend),
        "label": meta.variable_label,
        "definition": meta.variable_definition,
        "unit": meta.unit,
        "period": copy_module.period_label(trend),
        "trend_text": copy_module.trend_value_text(trend),
        "trend_unit": copy_module.trend_unit_label(trend),
        "trend_unit_short": trend.trend_unit,          # for narrow screens
        "interval_text": copy_module.interval_text(trend),
        "confidence_percent": round(trend.confidence_level * 100),
        "uncertainty": copy_module.uncertainty_sentence(trend),
        "conclusion": copy_module.conclusion_sentence(trend),
        "band_label": copy_module.band_label(trend) if annual["lo"] else "",
        "monthly": {
            "t": [round(p.date.year + (p.date.month - 0.5) / 12, 4) for p in inv.points],
            "v": [_round(p.value) for p in inv.points],
        },
        "annual": annual,
        "facts": facts,
        "notes": [note for note in notes if note],
        "source_url": meta.source_url,
    }


def _prediction(inv: Investigation, as_of: date) -> dict:
    metadata = {"label": inv.metadata.variable_label, "unit": inv.metadata.unit,
                "source_url": inv.metadata.source_url, "unit_note": inv.metadata.unit_note}
    try:
        return {**prediction.forecast(inv.points, as_of=as_of), **metadata}
    except (prediction.PredictionUnavailable, ArithmeticError) as exc:
        return {"status": "unavailable", "reason": str(exc), **metadata}


def build_payload(as_of: date | None = None) -> dict:
    """Everything the globe shows, for every region and variable.

    Each variable is analysed over all the years its saved file covers.
    """
    regions = globe_regions()
    as_of = as_of or datetime.now(ZoneInfo("America/Chicago")).date()
    results: dict[str, dict[str, dict]] = {}
    predictions: dict[str, dict[str, dict]] = {}
    variable_ids: list[str] = []
    years: list[int] = []
    first_years: set[int] = set()

    for region in regions:
        region_id = region["id"]
        results[region_id] = {}
        predictions[region_id] = {}
        for variable_id in catalog.variable_ids(region_id):
            try:
                first, last = section_a.available_years(region_id, variable_id)
                inv = investigate.load(region_id, variable_id, first, last)
            except section_a.DataUnavailableError:
                continue
            results[region_id][variable_id] = _result(inv)
            predictions[region_id][variable_id] = _prediction(inv, as_of)
            years += [first, last]
            first_years.add(first)
            if variable_id not in variable_ids:
                variable_ids.append(variable_id)

    # Catalog order first, so the tick boxes do not depend on file order.
    known = [v for v in catalog.VARIABLES if v in variable_ids]
    ordered = known + [v for v in variable_ids if v not in known]
    first_year, last_year = (min(years), max(years)) if years else (0, 0)

    return {
        "regions": regions,
        "variables": [
            {
                "id": variable_id,
                "label": catalog.variable_label(variable_id),
                "short": catalog.variable_short_label(variable_id),
            }
            for variable_id in ordered
        ],
        "results": results,
        "predictions": predictions,
        "generated_on": as_of.isoformat(),
        "first_year": first_year,
        "last_year": last_year,
        "provisional": bool(section_b.IS_PLACEHOLDER),
        "text": {
            "directions": copy_module.DIRECTION_LABELS,
            "series": copy_module.CHART_SERIES_LABELS,
            # Records that start later leave blank years in their stripes.
            "stripes": (
                copy_module.stripes_legend(first_year, last_year, len(first_years) > 1)
                if years
                else ""
            ),
            "color_key": copy_module.COLOR_KEY_TITLE,
            "faded_key": copy_module.FADED_KEY_LABEL,
            "hub_hint": copy_module.HUB_HINT,
            "chart_guide": copy_module.CHART_GUIDE,
            "provisional_tag": copy_module.PROVISIONAL_TAG,
            "provisional_notice": copy_module.PROVISIONAL_NOTICE,
            "saved_data": copy_module.SAVED_DATA_NOTICE,
            "short_record": copy_module.SHORT_RECORD_NOTE,
            "uncertainty_guide": copy_module.UNCERTAINTY_GUIDE,
            "prediction": copy_module.PREDICTION_TEXT,
        },
    }


def _data_signature() -> tuple:
    """Changes whenever a saved data file is added, removed or edited."""
    return tuple(
        (path.name, path.stat().st_mtime_ns, path.stat().st_size)
        for path in catalog.discover().values()
    )


@st.cache_data(show_spinner=False)
def _cached_payload(signature: tuple, as_of: date, model_version: str) -> dict:
    return build_payload(as_of)


def render() -> None:
    """Show the full-screen globe (sized by ui/theme.py)."""
    with st.container(key=STAGE_KEY):
        today = datetime.now(ZoneInfo("America/Chicago")).date()
        _globe(payload=_cached_payload(_data_signature(), today, prediction.VERSION), key="earth_globe", default=None)
