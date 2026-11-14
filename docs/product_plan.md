# Earth Trend Detective — product plan

NASA Space Apps · "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

## Scope (locked for the hackathon)

- **Concept A only**: "My Place, Over Time" — Chicago temperature.
- Concepts B ("Compare Two Places") and C ("Does the Time Window Matter?")
  are **stretch** and not scaffolded.

## Ownership

| Section | Owns | Delivers |
|---|---|---|
| A | Data retrieval, cleaning, units, metadata | `services.section_a.get_series(...)` |
| B | Aggregation, trend, uncertainty | `services.section_b.estimate_trend(...)` |
| C | UX, navigation, screens, accessibility, states, submission | everything in `ui/`, `app.py`, `docs/` |

Section C must not invent scientific results or silently replace B's method.

## Data contract (agreed in `services/contracts.py`)

- `SeriesPoint(date, value)`
- `DatasetMetadata(dataset_name, dataset_version, source_url, retrieved_at,
  coordinates_or_bounds, spatial_resolution, data_kind, missing_value_rules,
  unit, variable_label, variable_definition)`
- `TrendResult(status, period_start, period_end, aggregation,
  trend_per_decade, trend_unit, confidence_level, ci_lower, ci_upper,
  valid_count, excluded_count, method, assumptions, warnings,
  fitted_dates?, fitted_values?, band_lower?, band_upper?)`
- `status` ∈ {`ok`, `insufficient_data`, `invalid_selection`, `analysis_failed`}
- `data_kind` ∈ {`reanalysis`, `satellite`, `station`, `model`, `synthetic`}

## Dataset (initial demonstration)

- MERRA-2 M2T1NXSLV, variable `T2M` (2 m air temperature), via Giovanni.
- Nearest grid cell to Chicago (41.88°N, 87.63°W).
- Aggregation: annual mean (Section B to confirm).
- Period: 1980–2024, subject to Section A's confirmation of coverage.
- **Label as reanalysis grid cell, never as a Chicago weather station.**

## Screens

1. Landing — "Explore how a place has changed." Primary CTA: Explore the Chicago example.
2. Selection — location (Chicago), variable (temperature), period slider.
3. Results — title → sentence → trend + CI → chart → explanation → coverage → actions.
4. Evidence — dataset, variable, coverage, missing data, method.

## States

- Loading: "Loading the selected NASA data." → "Calculating the trend."
- Insufficient data: show status message, suppress trend result.
- Invalid selection: explain coverage, offer a valid selection.
- Data retrieval failed: "We couldn’t load the data. Retry, or explore the saved example." Selections preserved.
- Synthetic demo badge: "Synthetic demo data — not NASA findings" on every synthetic surface and in exports.

## Scientific-communication rules

Enforced in `services/copy.py`:
- Result template (§7).
- Uncertainty template (§7).
- CI-around-zero fallback (§7).
- Insufficient-data fallback (§7).
- `coverage_sentence` prevents labeling reanalysis as station data.

## Submission

- Public GitHub repo (shared with team).
- Streamlit Community Cloud URL as the primary submission link.
- 30-second video demo (preferred over 7-slide deck).
- README includes run instructions, data source, methods, and AI-use disclosure.

## Open questions

- [ ] Final dataset variable + aggregation (A + B).
- [ ] Minimum valid observation count for Section B's method.
- [ ] Whether Section B supplies a confidence band for the chart or only a slope CI.
- [ ] Exact Giovanni query URL and retrieval date (A).
