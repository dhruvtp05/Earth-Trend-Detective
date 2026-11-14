"""
Adapter for Section A (data retrieval, cleaning, metadata).

While Section A is still landing, this module forwards to the
labeled synthetic fixture in services.demo. Once Section A's real
`get_series(location_id, variable, start, end)` is available, wire
it in here — the UI should not change.

Expected real signature (agreed with Section A):

    def get_series(
        location_id: str,
        variable: str,
        start: date,
        end: date,
    ) -> tuple[list[SeriesPoint], DatasetMetadata]: ...
"""

from __future__ import annotations

from datetime import date

from .contracts import DatasetMetadata, SeriesPoint
from . import demo


def get_series(
    location_id: str,
    variable: str,
    start: date,
    end: date,
) -> tuple[list[SeriesPoint], DatasetMetadata]:
    """TEMPORARY: forwards to the synthetic fixture.

    Replace the body with a call into Section A's real module once
    their interface lands. Keep this function's signature stable.
    """
    inv = demo.get_investigation(period_start=start, period_end=end)
    return inv.points, inv.metadata
