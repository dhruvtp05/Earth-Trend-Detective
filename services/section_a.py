"""
Section A adapter: loads the saved Giovanni exports in data/.

Each file is a Giovanni "Time Series, Area-Averaged" CSV: a block of
`Key:,value` header rows (title, bounding boxes, reproduce URL, fill
value), a blank line, then `time, <column>` rows of monthly values.

These are saved datasets, not live requests.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

from . import catalog
from .contracts import DatasetMetadata, SeriesPoint


class DataUnavailableError(Exception):
    """The requested region/variable has no usable saved data."""


@dataclass
class _ParsedFile:
    header: dict[str, str]
    column: str
    fill_value: float | None
    rows: list[tuple[date, float | None]]   # None = missing


def _parse(path: Path) -> _ParsedFile:
    header: dict[str, str] = {}
    column = ""
    raw_rows: list[tuple[date, str]] = []

    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if not row or not any(cell.strip() for cell in row):
                continue
            first = row[0].strip()
            second = row[1].strip() if len(row) > 1 else ""
            if first.endswith(":"):
                header[first[:-1].strip()] = second
            elif first.lower() == "time":
                column = second
            else:
                try:
                    when = datetime.strptime(first, "%Y-%m-%d %H:%M:%S").date()
                except ValueError as exc:
                    raise DataUnavailableError(
                        f"{path.name}: unrecognised date '{first}'."
                    ) from exc
                raw_rows.append((when, second))

    if not raw_rows:
        raise DataUnavailableError(f"{path.name} contains no data rows.")

    fill_value: float | None = None
    for key, value in header.items():
        if key.startswith("Fill Value"):
            try:
                fill_value = float(value)
            except ValueError:
                fill_value = None

    rows: list[tuple[date, float | None]] = []
    for when, text in raw_rows:
        try:
            value: float | None = float(text)
        except ValueError:
            value = None
        if value is not None and (
            math.isnan(value)
            or (fill_value is not None and math.isclose(value, fill_value, rel_tol=1e-9))
        ):
            value = None
        rows.append((when, value))

    return _ParsedFile(header=header, column=column, fill_value=fill_value, rows=rows)


def _path_for(region_id: str, variable_id: str) -> Path:
    path = catalog.discover().get((region_id, variable_id))
    if path is None:
        raise DataUnavailableError(
            f"No saved data for {catalog.variable_label(variable_id)} in "
            f"{catalog.region_info(region_id).label}."
        )
    return path


def _format_bounds(bbox: str) -> str:
    """'-92.5,40,-76.25,49' (west,south,east,north) -> '40°N–49°N, 92.5°W–76.25°W'."""
    try:
        west, south, east, north = (float(part) for part in bbox.split(","))
    except ValueError:
        return bbox

    def lat(value: float) -> str:
        return f"{abs(value):g}°{'N' if value >= 0 else 'S'}"

    def lon(value: float) -> str:
        return f"{abs(value):g}°{'E' if value >= 0 else 'W'}"

    return f"{lat(south)}–{lat(north)}, {lon(west)}–{lon(east)}"


def _unit_from_url(url: str, column: str) -> str | None:
    """Unit Giovanni attached to this file's own variable, if any.

    A reproduce URL can list several variables, so the unit is taken only
    when it is attached to the variable named in the data column.
    """
    variable = column.removeprefix("mean_")
    if not variable:
        return None
    match = re.search(re.escape(variable) + r"\(units=([^)]+)\)", unquote(url))
    return match.group(1) if match else None


def _fallback_label(title: str, variable_id: str) -> str:
    """Label for a variable the catalog does not know yet."""
    label = re.sub(r"^Time Series, Area-Averaged of\s*", "", title).strip()
    return label or catalog.variable_label(variable_id)


def available_years(region_id: str, variable_id: str) -> tuple[int, int]:
    """First and last calendar year present in the saved file."""
    parsed = _parse(_path_for(region_id, variable_id))
    years = [when.year for when, value in parsed.rows if value is not None]
    if not years:
        raise DataUnavailableError("The saved file has no usable values.")
    return min(years), max(years)


def get_series(
    location_id: str,
    variable: str,
    start: date,
    end: date,
) -> tuple[list[SeriesPoint], DatasetMetadata]:
    """Monthly series and metadata for one region and variable."""
    parsed = _parse(_path_for(location_id, variable))

    in_period = [(when, value) for when, value in parsed.rows if start <= when <= end]
    info = catalog.VARIABLES.get(variable)
    scale = info.scale if info is not None else 1.0
    points = [
        SeriesPoint(date=when, value=value * scale)
        for when, value in in_period
        if value is not None
    ]
    missing = len(in_period) - len(points)

    fill_text = "blank" if parsed.fill_value is None else f"equal to the fill value ({parsed.fill_value:g}) or blank"
    missing_rules = (
        f"Months {fill_text} are treated as missing and left out. "
        f"{missing} of {len(in_period)} months in the selected period were missing."
    )

    bounds = _format_bounds(
        parsed.header.get("Data Bounding Box") or parsed.header.get("User Bounding Box", "")
    )
    source_url = parsed.header.get("URL to Reproduce Results", "")

    if info is not None:
        metadata = DatasetMetadata(
            dataset_name=info.dataset_name,
            dataset_version=info.dataset_version,
            source_url=source_url,
            retrieved_at=None,
            coordinates_or_bounds=f"Area average over {bounds}",
            spatial_resolution=info.spatial_resolution,
            data_kind=info.data_kind,
            missing_value_rules=missing_rules,
            unit=info.unit,
            variable_label=info.label,
            variable_definition=info.definition,
            unit_note=info.unit_note,
        )
    else:
        # A dataset the catalog has no entry for yet: show only what the
        # file itself states.
        unit = _unit_from_url(source_url, parsed.column)
        metadata = DatasetMetadata(
            dataset_name=parsed.column or "Not stated in the data file",
            dataset_version="See dataset identifier",
            source_url=source_url,
            retrieved_at=None,
            coordinates_or_bounds=f"Area average over {bounds}",
            spatial_resolution="See dataset title: " + parsed.header.get("Title", "not stated"),
            data_kind="model",
            missing_value_rules=missing_rules,
            unit=unit or "unit not stated",
            variable_label=_fallback_label(parsed.header.get("Title", ""), variable),
            variable_definition=parsed.header.get("Title", "Not stated in the data file."),
            unit_note="" if unit else "The data file does not state a unit.",
        )

    return points, metadata


def bounds_label(region_id: str, variable_id: str) -> str:
    """Formatted bounding box for one saved file."""
    parsed = _parse(_path_for(region_id, variable_id))
    return _format_bounds(
        parsed.header.get("Data Bounding Box") or parsed.header.get("User Bounding Box", "")
    )
