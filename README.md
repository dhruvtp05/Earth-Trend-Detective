# Earth Trend Detective

An accessible dashboard that helps students and curious members of the public
investigate long-term changes in NASA Earth science data.

Built for **NASA Space Apps**, *"Be An Earth System Trend Detective!"*, by a UIC
Computer Science and Data Science team.

For one region and one variable at a time, the app answers:

- What is changing?
- Where, and over what period?
- How much is it changing?
- How uncertain is the estimated trend?
- What can we reasonably conclude?

It can also compare the same variable across two regions.

> **Status:** the data is real NASA data. The trend numbers are provisional:
> they come from a placeholder method until the team's statistical analysis is
> integrated, and the app says so wherever they appear.

## Live demo

- Hosted app: *to be added*
- Demo video: *to be added*

## Run locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Then open the address Streamlit prints (by default http://localhost:8501).

Run the tests:

```powershell
pip install pytest
python -m pytest
```

## Data

Area-averaged monthly time series exported from
[NASA Giovanni](https://giovanni.gsfc.nasa.gov/giovanni/) and saved in `data/`.
The app reads these saved files; it does not make live requests.

| Variable | Dataset | Period |
|---|---|---|
| Precipitation (mm/day) | MERRA-2 M2TMNXFLX v5.12.4, bias-corrected total surface precipitation | 2005–2025 |
| Soil moisture, top 10 cm | GLDAS Noah Land Surface Model (GLDAS_NOAH025_M) v2.1 | 2000–2025 |
| Storm surface runoff | GLDAS Noah Land Surface Model (GLDAS_NOAH025_M) v2.1 | 2000–2025 |

| Region | Approximate box |
|---|---|
| Midwest (includes Chicago) | 40–49°N, 93–76°W |
| Southwest | 31–40°N, 115–106°W |

MERRA-2 is a reanalysis and GLDAS is a land-surface model. Their values are
averages over a large area, not measurements at a station, and the app labels
them that way. Each file's header holds the Giovanni link that reproduces it;
the app shows that link on the evidence screen.

To add a dataset, save the Giovanni CSV as
`data/{region}_{variable}_region{letter}.csv`. It is discovered automatically;
add a label and definition in `services/catalog.py`.

## Method

The statistical method belongs to the analysis team (Section B). The current
stand-in in `services/section_b.py` averages each complete calendar year, fits
ordinary least squares to the annual means and reports a 95% confidence
interval for the slope from the t distribution. It reports no trend when fewer
than 10 complete years are selected.

The interface never:

- shows an invented confidence percentage,
- says "no change" because a result is not statistically significant,
- presents a historical trend as a prediction or as evidence of a cause,
- draws a confidence band that the analysis did not supply,
- labels area-averaged model output as a local measurement.

## Project structure

```
app.py                  entry point and routing
ui/
  explore.py            landing and selection screens
  results.py            result sentence, trend, chart, downloads
  compare.py            two regions side by side
  evidence.py           dataset, method and sources
services/
  contracts.py          shared data structures (Sections A, B and C)
  catalog.py            regions, variables and data file discovery
  section_a.py          loads the saved Giovanni files
  section_b.py          trend and uncertainty (placeholder)
  investigate.py        combines data and analysis for the interface
  copy.py               every sentence that states a scientific result
data/                   saved NASA Giovanni exports
tests/                  data, method, wording and click-through tests
docs/                   product plan and research notes
```

## AI use disclosure

An AI coding assistant (in Cursor) was used to plan the interface and write
application code and tests. The data was selected and retrieved by team
members from NASA Giovanni. Team members review the wording of results against
the project's scientific-communication rules.

## License

To be decided by the team.
