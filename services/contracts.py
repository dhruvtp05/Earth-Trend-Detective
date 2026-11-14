"""
Shared input and output structures for Earth Trend Detective.

These dataclasses are the agreed interface between:
  - Section A (data retrieval, cleaning, metadata)
  - Section B (aggregation, trend, uncertainty)
  - Section C (user interface)

Do not change field names without updating docs/product_plan.md and
coordinating with Sections A and B.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

# ---------------------------------------------------------------------------
# Section A output: series + dataset metadata
# ---------------------------------------------------------------------------


@dataclass
class SeriesPoint:
    """One observation in a time series."""

    date: date
    value: float


DataKind = Literal["reanalysis", "satellite", "station", "model"]


@dataclass
class DatasetMetadata:
    """Provenance and coverage for a retrieved series.

    `data_kind`:
      - "reanalysis"  model constrained by observations (e.g. MERRA-2)
      - "model"       land-surface or other model output (e.g. GLDAS Noah)
      - "satellite"   satellite-derived estimate
      - "station"     direct in-situ measurement
    """

    dataset_name: str
    dataset_version: str
    source_url: str
    retrieved_at: datetime | None      # None until Section A records it
    coordinates_or_bounds: str
    spatial_resolution: str
    data_kind: DataKind
    missing_value_rules: str
    unit: str
    variable_label: str                # human-readable, e.g. "Precipitation"
    variable_definition: str           # one-sentence plain-language definition
    unit_note: str = ""                # caveat about the unit, if any


# ---------------------------------------------------------------------------
# Section B output: trend estimate + uncertainty + diagnostics
# ---------------------------------------------------------------------------

TrendStatus = Literal["ok", "insufficient_data", "invalid_selection", "analysis_failed"]


@dataclass
class TrendResult:
    """Output of the trend analysis.

    When `status != "ok"`, numeric fields are None and the UI suppresses
    the trend, showing only the status-appropriate message.
    """

    status: TrendStatus

    # Period actually analyzed.
    period_start: date
    period_end: date

    # How observations were aggregated before fitting (e.g. "Annual mean").
    aggregation: str

    # Trend estimate.
    trend_per_decade: float | None
    trend_unit: str                    # e.g. "mm/day/decade"

    # Uncertainty.
    confidence_level: float            # e.g. 0.95
    ci_lower: float | None
    ci_upper: float | None

    # Diagnostics, counted in original observations (months).
    valid_count: int
    excluded_count: int
    method: str
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Optional chart overlays. The UI never synthesizes these.
    aggregated_dates: list[date] | None = None     # e.g. one per year
    aggregated_values: list[float] | None = None
    fitted_dates: list[date] | None = None
    fitted_values: list[float] | None = None
    band_lower: list[float] | None = None
    band_upper: list[float] | None = None


# ---------------------------------------------------------------------------
# Bundle passed from the service layer to the UI
# ---------------------------------------------------------------------------


@dataclass
class Investigation:
    """A complete, display-ready investigation."""

    region_id: str
    variable_id: str
    location_label: str                # e.g. "Midwest"
    location_coverage: str             # e.g. "the Midwest region (area average over ...)"
    points: list[SeriesPoint]
    metadata: DatasetMetadata
    trend: TrendResult
    # True while the trend comes from Section C's stand-in method rather
    # than Section B's validated analysis.
    trend_is_placeholder: bool
