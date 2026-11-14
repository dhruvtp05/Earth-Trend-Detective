"""
Builds a display-ready Investigation from Section A's data and
Section B's analysis. No Streamlit imports: usable from tests.
"""

from __future__ import annotations

from datetime import date

from . import catalog, section_a, section_b
from .contracts import Investigation


def load(region_id: str, variable_id: str, start_year: int, end_year: int) -> Investigation:
    """Load one region/variable over whole calendar years.

    Raises section_a.DataUnavailableError if there is no saved data.
    """
    period_start = date(start_year, 1, 1)
    period_end = date(end_year, 12, 31)

    points, metadata = section_a.get_series(
        location_id=region_id,
        variable=variable_id,
        start=period_start,
        end=period_end,
    )
    trend = section_b.estimate_trend(
        points=points,
        period_start=period_start,
        period_end=period_end,
        unit=metadata.unit,
    )

    region = catalog.region_info(region_id)
    bounds = metadata.coordinates_or_bounds.removeprefix("Area average over ")
    return Investigation(
        region_id=region_id,
        variable_id=variable_id,
        location_label=region.label,
        location_coverage=f"the {region.label} region (area average over {bounds})",
        points=points,
        metadata=metadata,
        trend=trend,
        trend_is_placeholder=section_b.IS_PLACEHOLDER,
    )
