# Earth Trend Detective: product plan

NASA Space Apps, "Be An Earth System Trend Detective!"
UIC Computer Science and Data Science team.

## Scope

The app investigates one variable in one region over a chosen period, and can
compare the same variable across two regions.

- **Regions:** Midwest (Region B) and Southwest (Region A), as area averages.
- **Variables delivered:** precipitation, evaporation from land, soil
  moisture (top 10 cm), storm surface runoff.
- **Starting example:** precipitation in the Midwest, which includes Chicago.

Changed from the original brief: Section A delivered regional precipitation and
soil moisture rather than Chicago temperature, so "Compare Two Places" moved
from stretch to core. "Does the Time Window Matter?" is covered by the period
slider; a dedicated side-by-side view remains a stretch.

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
interval from the t distribution, and no trend below 10 complete years. Every
screen and export marks these numbers as provisional. When Section B's method
lands, replace the function body and set `IS_PLACEHOLDER = False`.

## Screens

1. Landing: "Explore the Midwest example" or "Choose a region".
2. Selection: region, variable, period slider limited to available years, reset.
3. Result: title, result sentence, trend and interval, chart, chart description
   and tables, coverage and limitations, next actions, downloads.
4. Evidence: dataset, variable, coverage, missing data, method, how to read
   uncertainty, link to reproduce in Giovanni.
5. Compare: same variable, period and method for both regions.

## Open questions

Section A:
- [ ] Retrieval date for each file (shown as "not recorded yet").
- [ ] Confirm the units of soil moisture, runoff and evaporation. The files
      state none; the app uses the units in the product documentation, each
      with a note. Evaporation is converted from kg/m²/s to mm/day (x 86,400).

Section B:
- [ ] Trend method and how seasonality and autocorrelation are handled.
- [ ] Minimum number of years for a valid trend.
- [ ] Whether a chart confidence band will be supplied (none is drawn otherwise).

Section C:
- [ ] Deploy to Streamlit Community Cloud and add the link to the README.
- [ ] Usability test with three people (Template E).
- [ ] 30-second demo video once Section B's numbers are in.
