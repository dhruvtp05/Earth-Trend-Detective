"""
Shared input and output structures for Earth Trend Detective.

These dataclasses are the agreed interface between:
  - Section A (data retrieval, cleaning, metadata)
  - Section B (aggregation, trend, uncertainty)
  - Section C (user interface)

Do not change field names without updating the product plan and
coordinating with Sections A and B.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

# ---------------------------------------------------------------------------
# Section A output: raw series + dataset metadata
# ---------------------------------------------------------------------------

@dataclass
class SeriesPoint:
    """One observation in a time series."""
    date: date
    value: float


@dataclass
class DatasetMetadata:
    """Provenance and coverage for a retrieved series.

    `data_kind` must be one of:
      - "reanalysis"   (e.g. MERRA-2, ERA5 — model-assimilated)
      - "satellite"    (e.g. MODIS, AIRS)
      - "station"      (direct in-situ measurement)
      - "model"        (pure model output, no assimilation)
      - "synthetic"    (demo fixture, never a NASA finding)
    """
    dataset_name: str
    dataset_version: str
    source_url: str
    retrieved_at: datetime
    coordinates_or_bounds: str
    spatial_resolution: str
    data_kind: Literal["reanalysis", "satellite", "station", "model", "synthetic"]
    missing_value_rules: str
    unit: str
    variable_label: str          # human-readable, e.g. "Near-surface air temperature"
    variable_definition: str     # one-sentence plain-language definition


# ---------------------------------------------------------------------------
# Section B output: trend estimate + uncertainty + diagnostics
# ---------------------------------------------------------------------------

TrendStatus = Literal["ok", "insufficient_data", "invalid_selection", "analysis_failed"]


@dataclass
class TrendResult:
    """Output of the trend analysis.

    When `status != "ok"`, numeric fields may be None and the UI must
    suppress the trend result, showing only the status-appropriate message.
    """
    status: TrendStatus

    # Period actually analyzed (may be narrower than the user's request if
    # Section B had to trim for data availability).
    period_start: date
    period_end: date

    # How observations were aggregated before fitting (e.g. "annual mean").
    aggregation: str

    # Trend estimate.
    trend_per_decade: float | None
    trend_unit: str                 # e.g. "degC/decade"

    # Uncertainty.
    confidence_level: float         # e.g. 0.95
    ci_lower: float | None
    ci_upper: float | None

    # Diagnostics.
    valid_count: int
    excluded_count: int
    method: str                     # e.g. "Ordinary least squares on annual means"
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Optional chart overlays (only populated if Section B computed them
    # correctly; the UI will not synthesize them).
    fitted_dates: list[date] | None = None
    fitted_values: list[float] | None = None
    band_lower: list[float] | None = None
    band_upper: list[float] | None = None


# ---------------------------------------------------------------------------
# Convenience bundle passed from the service layer to the UI
# ---------------------------------------------------------------------------

@dataclass
class Investigation:
    """A complete, display-ready investigation bundle."""
    location_label: str              # e.g. "Chicago area"
    location_coverage: str           # e.g. "MERRA-2 grid cell nearest 41.88N, 87.63W"
    points: list[SeriesPoint]
    metadata: DatasetMetadata
    trend: TrendResult
    is_demo: bool                    # True when sourced from services.demo
