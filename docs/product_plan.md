# Earth Trend Detective: product plan

NASA Space Apps, "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

## Scope

The app is one full-screen globe. It shows every delivered variable for both
regions, each over all the years its file covers.

- **Regions:** Southwest (Region A) and Midwest (Region B), as area averages.
- **Variables delivered:** precipitation, evaporation from land, soil
  moisture (top 10 cm), storm surface runoff.

Changed from the original brief: Section A delivered regional precipitation and
soil moisture rather than Chicago temperature, so both regions are shown
together. The earlier multi-screen version (selection, result, evidence and
compare screens, period slider, chart types, downloads) was replaced by the
globe; choosing a period ("Does the Time Window Matter?") is no longer offered
and remains a stretch.

## Ownership

| Section | Owns | Delivers |
|---|---|---|
| A | Data retrieval, cleaning, units, metadata | CSV files in `data/` |
| B | Aggregation, trend, uncertainty, validity rules | `services/section_b.estimate_trend(...)` |
| C | Interface, states, accessibility, submission | `app.py`, `ui/`, `docs/` |

Section C does not invent scientific results or replace Section B's method.

## Data delivered by Section A

Giovanni "Time Series, Area-Averaged" exports, monthly, no missing months.

| File | Region box | Dataset | Period |
|---|---|---|---|
| `southwest_precip_regionA.csv` | 31–40°N, 115–106.25°W | MERRA-2 M2TMNXFLX 5.12.4, PRECTOTCORR, mm/day | 2005–2025 |
| `midwest_precip_regionB.csv` | 40–49°N, 92.5–76.25°W | same | 2005–2025 |
| `southwest_soilmoisture_regionA.csv` | 31.125–39.875°N, 114.875–106.125°W | GLDAS_NOAH025_M 2.1, SoilMoi0_10cm_inst | 2000–2025 |
| `midwest_soilmoisture_regionB.csv` | 40.125–48.875°N, 92.875–76.125°W | same | 2000–2025 |
| `southwest_evap_regionA.csv`, `midwest_evap_regionB.csv` | as precipitation | MERRA-2 M2TMNXLND 5.12.4, EVLAND | 2005–2025 |
| `southwest_runoff_regionA.csv` | as soil moisture | GLDAS_NOAH025_M 2.1, Qs_acc | 2000–2025 |
| `midwest_runoff_regionB.csv` | as soil moisture | same | 2000–2025 |

File naming: `{region}_{variable}_region{letter}.csv`. Files that follow it are
picked up automatically; friendly labels live in `services/catalog.py`.

## Contract (`services/contracts.py`)

- `SeriesPoint(date, value)`
- `DatasetMetadata(dataset_name, dataset_version, source_url, retrieved_at,
  coordinates_or_bounds, spatial_resolution, data_kind, missing_value_rules,
  unit, variable_label, variable_definition, unit_note)`
- `TrendResult(status, period_start, period_end, aggregation, trend_per_decade,
  trend_unit, confidence_level, ci_lower, ci_upper, valid_count, excluded_count,
  method, assumptions, warnings, aggregated_dates?, aggregated_values?,
  fitted_dates?, fitted_values?, band_lower?, band_upper?)`
- `status`: `ok`, `insufficient_data`, `invalid_selection`, `analysis_failed`

Section B's function:

```python
estimate_trend(points, period_start, period_end, confidence_level=0.95, unit="") -> TrendResult
```

`points` are monthly. `valid_count` and `excluded_count` are counted in months.

## Trend method: placeholder until Section B delivers

`services/section_b.py` currently holds a stand-in so the interface can be built
on real data: annual means of complete years, ordinary least squares, 95%
interval for the slope from the t distribution, the matching 95% confidence
band for the fitted line, and no trend below 10 complete years. The charts
panel marks these numbers with a "Provisional" tag and a note; the labels on
the globe itself do not carry the tag. When Section B's method lands, replace
the function body (including `band_lower` and `band_upper`, or leave them
`None` to draw no band) and set `IS_PLACEHOLDER = False`.

## The globe screen

1. Idle: the globe spins slowly; the only control is Start.
2. Tour: the camera eases to the Southwest, then the Midwest, then frames
   both. A click, tap or Esc skips it.
3. Explore: each region shows one row of yearly stripes per ticked variable
   (brightness = yearly average; amber = increase, violet = decrease, gray =
   interval includes zero) and a label with the trend value, unit and a
   "Significant" or "Inconclusive" badge. Controls: one tick box per variable
   and the "Charts & details" switch.
4. Charts panel (click a region or use the switch): region tabs, then for each
   ticked variable the monthly values, annual means, fitted trend and
   confidence band, the interval and conclusion sentences, dataset facts, the
   Giovanni link and a table of yearly values. Close returns to the globe.

Rule for colour and badge: a direction is shown only when the 95% confidence
interval excludes zero (`services/copy.trend_direction`). On narrow screens the
labels shorten to the row names when both regions are in view; the full label
shows at each tour stop and in the panel.

## Open questions

Section A:
- [ ] Retrieval date for each file (shown as "not recorded yet").
- [ ] Confirm the units of soil moisture, runoff and evaporation. The files
      state none; the app uses the units in the product documentation, each
      with a note. Evaporation is converted from kg/m²/s to mm/day (x 86,400).

Section B:
- [ ] Trend method and how seasonality and autocorrelation are handled.
- [ ] Minimum number of years for a valid trend.
- [ ] Whether a chart confidence band will be supplied. The placeholder draws
      the ordinary least squares band; none is drawn if the method gives none.

Section C:
- [ ] Deploy to Streamlit Community Cloud and add the link to the README.
- [ ] Try the globe on a real phone (touch drag, pinch zoom, speed).
- [ ] Usability test with three people (Template E).
- [ ] 30-second demo video once Section B's numbers are in.
