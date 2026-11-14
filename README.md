# Earth Trend Detective

A full-screen interactive globe that helps students and curious members of the
public investigate long-term changes in NASA Earth science data.

Built for **NASA Space Apps**, *"Be An Earth System Trend Detective!"*, by a UIC
Computer Science and Data Science team.

For each region and variable, the app answers:

- What is changing?
- Where, and over what period?
- How much is it changing?
- How uncertain is the estimated trend?
- What can we reasonably conclude?

> **Status:** the data is real NASA data. The trend numbers are provisional:
> they come from a placeholder method until the team's statistical analysis is
> integrated. Historical details explain this; the Prediction tab contains a
> separate experimental forecasting method.

## How it works

1. The globe spins slowly under the app title, with a single **Start** button.
2. Start moves the camera to the Southwest (Region A), then the Midwest
   (Region B), then settles on both. A click, tap or Esc skips ahead.
3. Each region is a hub with its name, pinned to the middle of its study area,
   with one block per ticked variable around it and a red wire from the hub to
   each block. A block is a row of yearly stripes, one stripe per year, over a
   line with the variable's name, its trend and a "Significant" or
   "Inconclusive" badge. Brightness follows the yearly average. Color names
   the variable: orange for precipitation, teal for evaporation, brown for
   soil moisture and violet for runoff. When the 95% confidence interval
   includes zero the stripes are faded, the badge reads "Inconclusive" and no
   direction is shown. A color key in the corner is drawn with the stripes'
   own colors. In a small window the blocks drop the trend value, then the
   badge; on a phone with both regions in view only the hubs are shown.
4. Pointing at a hub lights its wires and blocks; pointing at a block lights
   that block, its wire and the hub. Clicking a block opens the charts panel
   and glides to that variable's card.
5. Clicking a hub or a region, or switching on **Charts & details**, opens a panel that
   takes about 40% of a laptop window. It starts with one plain-language line
   per variable ("Downward trend", "No clear trend"). Below that, each variable
   has a card: what the variable is, the result, a chart (monthly values,
   annual means, the fitted trend and its confidence band) and a "What this
   means" box with the conclusion and the confidence interval in words. The
   dataset details, the Giovanni link and the yearly values are folded away
   under each card.
6. **Prediction**, next to the region tabs, shows experimental future monthly
   medians and prediction ranges for precipitation, evaporation, topsoil moisture
   and runoff. Choose either region and a 3-, 6- or 12-month future window.

The controls are Start, one tick box per variable, the Charts & details switch,
region and Prediction tabs, prediction selectors, and close. On a phone the panel
opens as a sheet over the lower part of the screen. If the device prefers
reduced motion, the globe does not spin and Start goes straight to the final
view. Without 3D graphics the tick boxes and the charts panel are shown alone.

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
| Evaporation from land (shown in mm/day) | MERRA-2 M2TMNXLND v5.12.4, EVLAND | 2005–2025 |
| Soil moisture, top 10 cm | GLDAS Noah Land Surface Model (GLDAS_NOAH025_M) v2.1 | 2000–2025 |
| Storm surface runoff | GLDAS Noah Land Surface Model (GLDAS_NOAH025_M) v2.1 | 2000–2025 |

| Region | Approximate box |
|---|---|
| Midwest (includes Chicago) | 40–49°N, 93–76°W |
| Southwest | 31–40°N, 115–106°W |

MERRA-2 is a reanalysis and GLDAS is a land-surface model. Their values are
averages over a large area, not measurements at a station, and the app labels
them that way. Each file's header holds the Giovanni link that reproduces it;
the app shows that link in the charts panel. Each variable is analysed over all
the years its file covers.

To add a dataset, save the Giovanni CSV as
`data/{region}_{variable}_region{letter}.csv`. It is discovered automatically;
add a label and definition in `services/catalog.py`.

## Method

The statistical method belongs to the analysis team (Section B). The current
stand-in in `services/section_b.py` averages each complete calendar year, fits
ordinary least squares to the annual means and reports a 95% confidence
interval for the slope from the t distribution. It also supplies the standard
95% confidence band for the fitted line,
`fitted ± t · s · sqrt(1/n + (x − x̄)² / Sxx)`. It reports no trend when fewer
than 10 complete years are selected. Section B's method must supply its own
band; the chart draws none otherwise.

A trend is called "Significant" only when its 95% confidence interval excludes
zero. That says nothing about how large or important the change is.

The interface never:

- shows an invented confidence percentage,
- shows a trend as an increase or a decrease (arrow, badge, headline or full
  color) when its interval includes zero,
- says "no change" because a result is not statistically significant,
- presents a historical trend as a prediction or as evidence of a cause,
- draws a confidence band that the analysis did not supply,
- labels area-averaged model output as a local measurement.

### Experimental prediction

`services/prediction.py` compares a seasonal baseline with a damped seasonal-trend
model on log-transformed monthly observations. Earlier rolling forecast errors
form an empirical predictive distribution. Each future lead has its own model
selection period (48 targets), error distribution and later test (24 targets),
using only information available at each historical origin. Model outputs are
nonnegative, and prediction ranges describe future monthly values rather than
the historical fitted line.

Targets begin after today's date in America/Chicago. Their leads account for
the gap since the final saved observation, currently December 2025. No live
weather data are fetched. A daily cache regenerates on a new page load; a page
left open retains its displayed generation date until reloaded.

The nominal 80% prediction range is shown with actual held-out coverage and
baseline error. Poor performance is explicitly marked. Probabilities of values
below/above their calendar month's historical quartiles are withheld unless
their backtests have enough cases, positive Brier skill, acceptable interval
coverage and baseline performance. These are experimental monthly-condition
indicators, not calibrated disaster probabilities. There are no observed flood
or drought labels in the saved data; those disaster probabilities remain unknown.
See [prediction method and limits](docs/prediction_method.md).

## Project structure

```
app.py                  entry point: shows the globe
ui/
  globe.py              prepares every result once and sends it to the globe
  globe_component/      the globe page (index.html), globe library, NASA Blue
                        Marble textures, credits
  theme.py              hides Streamlit's page chrome so the globe fills the window
.streamlit/config.toml  dark theme, colors and zero page padding
.cursor/skills/         pointer to the Streamlit guidance that ships with the
                        installed Streamlit, for AI coding assistants
services/
  contracts.py          shared data structures (Sections A, B and C)
  catalog.py            regions, variables and data file discovery
  section_a.py          loads the saved Giovanni files
  section_b.py          trend and uncertainty (placeholder)
  investigate.py        combines data and analysis for the interface
  copy.py               every sentence that states a scientific result
  prediction.py         experimental monthly distributions and matching-lead tests
data/                   saved NASA Giovanni exports
tests/                  data, method, wording and globe payload tests
docs/                   product plan and research notes
```

The globe runs entirely in the browser after one payload from Python, so
ticking variables and opening charts never reloads the page. `requirements.txt`
pins Streamlit because `ui/theme.py` relies on Streamlit's element names.

## AI use disclosure

An AI coding assistant (in Cursor) was used to plan the interface and write
application code and tests. The data was selected and retrieved by team
members from NASA Giovanni. Team members review the wording of results against
the project's scientific-communication rules.

## License

To be decided by the team.
