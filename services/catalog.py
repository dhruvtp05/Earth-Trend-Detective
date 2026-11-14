"""
Catalog of the regions and variables Section A has delivered.

Data files live in data/ and are named:

    {region}_{variable}_region{letter}.csv      e.g. midwest_precip_regionB.csv

Any file matching that pattern is discovered automatically. Regions and
variables listed below get friendly labels; anything else falls back to
labels derived from the file itself, so a new dataset shows up without a
code change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .contracts import DataKind

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_FILENAME_RE = re.compile(
    r"^(?P<region>[a-z]+)_(?P<variable>[a-z0-9_]+)_region(?P<letter>[A-Za-z])\.csv$"
)


@dataclass(frozen=True)
class RegionInfo:
    id: str
    label: str            # short, e.g. "Midwest"
    description: str      # what a newcomer would recognise


@dataclass(frozen=True)
class VariableInfo:
    id: str
    label: str
    definition: str
    unit: str
    dataset_name: str
    dataset_version: str
    spatial_resolution: str
    data_kind: DataKind
    unit_note: str = ""
    # Multiplier applied to the file's values to reach `unit`.
    scale: float = 1.0


REGIONS: dict[str, RegionInfo] = {
    "midwest": RegionInfo(
        id="midwest",
        label="Midwest",
        description="Midwest and Great Lakes, including Chicago",
    ),
    "southwest": RegionInfo(
        id="southwest",
        label="Southwest",
        description="Southwest, including Arizona and New Mexico",
    ),
}

VARIABLES: dict[str, VariableInfo] = {
    "precip": VariableInfo(
        id="precip",
        label="Precipitation",
        definition=(
            "Average daily precipitation (rain plus snow, as liquid water) "
            "in each month, averaged over the region."
        ),
        unit="mm/day",
        dataset_name="MERRA-2 M2TMNXFLX, bias-corrected total surface precipitation (PRECTOTCORR)",
        dataset_version="5.12.4",
        spatial_resolution="0.5° latitude × 0.625° longitude, monthly",
        data_kind="reanalysis",
    ),
    "evap": VariableInfo(
        id="evap",
        label="Evaporation from land",
        definition=(
            "Water returned from the land to the air, from soil, plants and "
            "surface water, as an average daily amount in each month, "
            "averaged over the region."
        ),
        unit="mm/day",
        unit_note=(
            "The data file does not state a unit. kg/m²/s is the unit documented "
            "for this MERRA-2 variable; the app multiplies it by 86,400 to show "
            "mm/day, the same unit as precipitation. Awaiting Section A's "
            "confirmation."
        ),
        scale=86400.0,
        dataset_name="MERRA-2 M2TMNXLND, evaporation from land (EVLAND)",
        dataset_version="5.12.4",
        spatial_resolution="0.5° latitude × 0.625° longitude, monthly",
        data_kind="reanalysis",
    ),
    "soilmoisture": VariableInfo(
        id="soilmoisture",
        label="Soil moisture (top 10 cm)",
        definition=(
            "Amount of water held in the top 10 cm of soil in each month, "
            "averaged over the region."
        ),
        unit="kg/m²",
        unit_note=(
            "The data file does not state a unit. kg/m² is the unit documented "
            "for this GLDAS product and is awaiting Section A's confirmation."
        ),
        dataset_name="GLDAS Noah Land Surface Model L4 (GLDAS_NOAH025_M), soil moisture 0–10 cm (SoilMoi0_10cm_inst)",
        dataset_version="2.1",
        spatial_resolution="0.25° latitude × 0.25° longitude, monthly",
        data_kind="model",
    ),
    "runoff": VariableInfo(
        id="runoff",
        label="Storm surface runoff",
        definition=(
            "Water from rain or snowmelt that runs off over the land surface "
            "instead of soaking into the soil, as the average amount per "
            "3 hours in each month, averaged over the region."
        ),
        unit="kg/m² per 3 h",
        unit_note=(
            "The data file does not state a unit. kg/m² per 3 hours is the unit "
            "documented for this GLDAS monthly product and is awaiting Section "
            "A's confirmation."
        ),
        dataset_name="GLDAS Noah Land Surface Model L4 (GLDAS_NOAH025_M), storm surface runoff (Qs_acc)",
        dataset_version="2.1",
        spatial_resolution="0.25° latitude × 0.25° longitude, monthly",
        data_kind="model",
    ),
}

DEFAULT_REGION = "midwest"
DEFAULT_VARIABLE = "precip"


def discover() -> dict[tuple[str, str], Path]:
    """Map (region_id, variable_id) to its data file."""
    found: dict[tuple[str, str], Path] = {}
    if not DATA_DIR.is_dir():
        return found
    for path in sorted(DATA_DIR.glob("*.csv")):
        match = _FILENAME_RE.match(path.name)
        if match:
            found[(match["region"], match["variable"])] = path
    return found


def region_ids() -> list[str]:
    """Available regions, known ones first in their declared order."""
    present = {region for region, _ in discover()}
    known = [r for r in REGIONS if r in present]
    return known + sorted(present - set(known))


def variable_ids(region_id: str) -> list[str]:
    """Variables available for one region, known ones first."""
    present = {var for region, var in discover() if region == region_id}
    known = [v for v in VARIABLES if v in present]
    return known + sorted(present - set(known))


def region_info(region_id: str) -> RegionInfo:
    if region_id in REGIONS:
        return REGIONS[region_id]
    label = region_id.replace("_", " ").title()
    return RegionInfo(id=region_id, label=label, description=label)


def region_option_label(region_id: str) -> str:
    info = region_info(region_id)
    if info.description == info.label:
        return info.label
    return f"{info.label} ({info.description})"


def variable_label(variable_id: str) -> str:
    if variable_id in VARIABLES:
        return VARIABLES[variable_id].label
    return variable_id.replace("_", " ").capitalize()
