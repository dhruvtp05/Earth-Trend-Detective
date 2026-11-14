# Earth Trend Detective

An accessible dashboard that helps students and curious members of the public
investigate long-term changes in NASA Earth science data.

Built for **NASA Space Apps 2026** — *"Be An Earth System Trend Detective!"*
by a UIC Computer Science and Data Science team.

The app answers five questions for one place and one variable at a time:

- **What** is changing?
- **Where** and over **what period**?
- **How much** is it changing?
- **How uncertain** is the estimated trend?
- **What** can we reasonably conclude?

Initial demonstration: near-surface air temperature around Chicago.

## Live demo

- Hosted app: *add Streamlit Community Cloud URL here*
- 30-second demo video: *add link here*

## Run locally

```powershell
# from the project root
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (default: http://localhost:8501).

## Project structure

```
app.py                  entry point, routing, loading/error states
ui/
  explore.py            landing + selection screens
  results.py            result sentence, trend card, chart, downloads
  evidence.py           dataset, variable, method, sources
services/
  contracts.py          shared dataclasses (A ↔ B ↔ C)
  demo.py               labeled synthetic fixture (never a NASA finding)
  section_a.py          adapter for data retrieval (Section A)
  section_b.py          adapter for trend + uncertainty (Section B)
  copy.py               scientific-communication sentences
docs/
  product_plan.md       locked scope + open questions
  research_notes.md     interface references + usability notes
```

## Data source

Initial demonstration draws from **NASA MERRA-2** (M2T1NXSLV, variable `T2M`)
via Giovanni (https://giovanni.gsfc.nasa.gov/giovanni/).

MERRA-2 is a model **reanalysis** product, not a direct station measurement.
Any value it provides represents a grid cell near the location of interest,
not a specific weather station. The app labels this explicitly on every
screen.

While Section A's retrieval is being finalized, the app loads a clearly
labeled synthetic fixture (`services/demo.py`) and marks every surface with
**"Synthetic demo data — not NASA findings"**.

## Statistical method

Section B defines the method, aggregation, and uncertainty. The current
placeholder is ordinary least squares on annual means with a normal-
approximation 95% confidence interval on the slope; the UI will display
whatever method and interval Section B publishes.

The UI will **never**:

- Invent a confidence percentage.
- Describe a p-value as the probability the conclusion is true.
- Say "no change" merely because the result is not significant.
- Make a health or neighborhood-risk claim from a broad temperature grid.
- Label a reanalysis grid-cell value as a local weather-station measurement.

## AI use disclosure

Portions of the scaffolding (file structure, boilerplate, docstrings) were
drafted with the assistance of an AI coding assistant inside Cursor. All
scientific-communication sentences, dataset labeling rules, and the
statistical method are reviewed against the project brief and the data
contract agreed with Sections A and B.

## License

To be decided by the team. Default: MIT.
