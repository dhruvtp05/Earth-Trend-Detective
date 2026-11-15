# Earth Trend Detective 🌎

**Explore Earth's changing water systems through NASA Earth science data.**

Earth Trend Detective is an interactive geospatial visualization platform that helps users investigate long-term environmental changes across selected regions of the United States. By combining NASA satellite-derived observations, land-surface model outputs, historical trend analysis, and experimental forecasting, the project makes complex Earth science data easier to explore and interpret.

Built for the **2026 NASA Space Apps Challenge** — *Be An Earth System Trend Detective!*

<p align="center">
  <a href="https://earthdetective.us/"><strong>🌐 Explore the Live Application</strong></a>
</p>

---

## Overview

Environmental changes are rarely explained by a single measurement. Precipitation, evaporation, soil moisture, and surface runoff interact to shape regional water conditions.

Earth Trend Detective brings these variables together in an interactive 3D globe, allowing users to explore how regional water-related conditions have changed over time and examine experimental projections of future monthly conditions.

The application focuses on five questions:

- What environmental variables are changing?
- Where are these changes occurring?
- How have conditions evolved over time?
- How reliable are the estimated trends and projections?
- What conclusions can reasonably be drawn from the available data?

## Features

### Interactive 3D Globe

Explore the selected study regions through a full-screen interactive globe.

- Animated camera tour introducing both study regions.
- Interactive regional markers and environmental variable indicators.
- Color-coded visualizations for the four environmental variables.
- Interactive exploration through mouse, touch, and keyboard controls.
- Responsive charts and information panels.
- Reduced-motion support and a fallback interface when 3D graphics are unavailable.

### Historical Environmental Analysis

Explore historical monthly observations and annual summaries for each variable.

- Regional monthly time-series visualizations.
- Annual aggregation and estimated historical trends.
- Confidence intervals and uncertainty visualization.
- Plain-language explanations of statistical results.
- Access to dataset metadata and original NASA Giovanni retrieval links.

### Experimental Future Projections

The Prediction interface provides experimental monthly projections for selected environmental variables.

- Three-, six-, and twelve-month projection windows.
- Seasonal baseline and damped seasonal-trend model comparison.
- Predicted monthly medians and prediction intervals.
- Rolling-origin model evaluation.
- Historical seasonal comparisons where validation criteria permit.

**Important:** These projections are experimental statistical estimates, not operational weather forecasts or calibrated flood and drought predictions.

---

## Geographic Coverage

The current implementation focuses on two study regions in the United States.

| Region | Description | Approximate bounding box |
|---|---|---|
| Southwest (Region A) | Colorado River Basin area, including Arizona | 31°N–40°N, 115°W–106°W |
| Midwest (Region B) | Great Lakes region, including Chicago | 40°N–49°N, 93°W–76°W |

These bounding boxes define rectangular regional study areas rather than individual cities, weather stations, or administrative boundaries.

The application uses area-averaged environmental data. Consequently, its values represent broader regional conditions rather than measurements at a specific location.

Additional regions and variables can be incorporated through the existing dataset discovery and catalog architecture.

---

## NASA Data Sources

Earth Trend Detective uses two primary NASA Earth science data products:

**1. MERRA-2 — Modern-Era Retrospective Analysis for Research and Applications, Version 2**

MERRA-2 is a NASA atmospheric reanalysis that combines observations with a numerical weather prediction system to produce a consistent representation of historical atmospheric conditions.

**2. GLDAS — Global Land Data Assimilation System**

GLDAS combines satellite and ground-based observations with land-surface modeling to estimate terrestrial water and energy conditions.

The application currently uses monthly, area-averaged time series retrieved through [NASA Giovanni](https://giovanni.gsfc.nasa.gov/giovanni/).

### Dataset Inventory

| Environmental variable | NASA product | Variable identifier | Product version | Current data period |
|---|---|---|---|---|
| Precipitation | MERRA-2 M2TMNXFLX | PRECTOTCORR | 5.12.4 | 2005–2025 |
| Land evaporation | MERRA-2 M2TMNXLND | EVLAND | 5.12.4 | 2005–2025 |
| Topsoil moisture (0–10 cm) | GLDAS Noah GLDAS_NOAH025_M | SoilMoi0_10cm_inst | 2.1 | 2000–2025 |
| Storm surface runoff | GLDAS Noah GLDAS_NOAH025_M | Qs_acc | 2.1 | 2000–2025 |

The periods above describe the currently documented dataset coverage. Individual regional exports determine the observations actually available for analysis.

### Spatial and Temporal Resolution

| Dataset | Spatial resolution | Temporal resolution |
|---|---|---|
| MERRA-2 | 0.5° latitude × 0.625° longitude | Monthly |
| GLDAS Noah | 0.25° latitude × 0.25° longitude | Monthly |

### Environmental Variables

**Precipitation (PRECTOTCORR)**

Represents bias-corrected total surface precipitation, including rainfall and snowfall expressed as liquid-water equivalent.

Displayed in millimeters per day (mm/day).

**Land Evaporation (EVLAND)**

Represents water transferred from land surfaces to the atmosphere through evaporation and related land-surface processes.

The application currently applies a multiplier of 86,400 to the source values to display them in mm/day. This conversion follows the documented kg/m²/s unit, but the original export's unit metadata still requires confirmation.

**Soil Moisture (SoilMoi0_10cm_inst)**

Represents the amount of water stored in the upper 10 centimeters of soil.

The documented product unit is kg/m². Confirmation against the original export metadata remains pending.

**Storm Surface Runoff (Qs_acc)**

Represents water moving across the land surface rather than infiltrating into the soil.

The documented GLDAS monthly product unit is kg/m² per 3 hours. Confirmation against the original export metadata remains pending.

For complete variable definitions and unit handling, see [`services/catalog.py`](services/catalog.py).

---

## Data Acquisition and Processing

The current application uses saved NASA Giovanni CSV exports rather than making live NASA data requests whenever a user opens the website.

The data acquisition workflow is:

1. **Dataset selection:** Select the appropriate MERRA-2 or GLDAS product and environmental variable.
2. **Geographic selection:** Define the Midwest or Southwest study region using its bounding coordinates.
3. **Temporal selection:** Retrieve the available monthly time series.
4. **Data retrieval:** Export area-averaged time-series CSV files through NASA Giovanni.
5. **Local storage:** Store the retrieved datasets in the repository's `data/` directory.
6. **Data processing:** Parse observations, handle missing values, apply configured unit conversions, and prepare the time series for analysis.
7. **Visualization:** Deliver processed data to the interactive globe, historical charts, and experimental prediction interface.

### Reproducibility

Each saved Giovanni export retains metadata from the original retrieval, including information such as its bounding box, fill value, and reproduction URL.

The application exposes the corresponding Giovanni link in the dataset details panel so users can inspect and reproduce the original data retrieval.

### Data Handling

The application:

- Reads saved monthly CSV exports locally.
- Identifies missing and fill-value observations.
- Preserves missing observations rather than treating them as real measurements.
- Checks data availability before analysis.
- Applies variable-specific scaling where configured.
- Uses dataset metadata to describe the selected region and variable.

**Data availability note:** The current application does not automatically download new observations from NASA. Updating the historical record requires retrieving new exports and incorporating them into the repository.

---

## Statistical Methodology

Earth Trend Detective separates historical trend analysis from future prediction. They answer different questions and use different uncertainty measures.

### Historical Trend Analysis

The historical analysis interface summarizes long-term changes in the selected environmental variables.

The current implementation in [`services/section_b.py`](services/section_b.py) is a provisional statistical stand-in:

1. Retain calendar years containing all twelve monthly observations.
2. Calculate the annual mean from the twelve monthly values.
3. Fit an ordinary least squares linear regression to the annual means.
4. Estimate a 95% confidence interval for the trend slope using a Student's t distribution.
5. Calculate a confidence band for the fitted regression line.

A minimum of ten complete years is required by the current implementation.

The trend is expressed as a change per decade in the corresponding variable's units.

### Interpreting Statistical Significance

The interface uses the 95% confidence interval to communicate uncertainty around the estimated trend.

- **Significant:** The estimated slope's 95% confidence interval excludes zero.
- **Inconclusive:** The confidence interval includes zero.

An inconclusive result does not establish that no environmental change occurred. It indicates that the available analysis does not establish a statistically distinguishable positive or negative trend at the selected confidence level.

Statistical significance also does not necessarily imply practical or environmental importance.

**Methodology status:** The current historical trend implementation is explicitly marked as a placeholder pending replacement with the finalized analysis methodology. Historical trend values should therefore be interpreted as provisional rather than definitive scientific findings.

### Scientific Communication

The application is designed to avoid overstating what the available data can establish.

It does not:

- Invent confidence percentages.
- Present inconclusive trends as confirmed increases or decreases.
- Interpret a statistically insignificant result as proof of no change.
- Treat correlation or historical trends as evidence of causation.
- Present historical trend confidence intervals as prediction intervals.
- Describe regional model outputs as measurements from individual weather stations.

---

## Experimental Future Predictions

The Prediction interface provides experimental monthly projections using the saved historical observations.

Implementation: [`services/prediction.py`](services/prediction.py)

Detailed methodology: [`docs/prediction_method.md`](docs/prediction_method.md)

### Forecasting Models

Two candidate models are evaluated:

| Model | Description |
|---|---|
| Seasonal Baseline | Estimates expected values using historical calendar-month patterns. |
| Damped Seasonal Trend | Models calendar-month seasonality and a time trend, with future trend increments gradually damped. |

The models use a log1p transformation during fitting, with nonnegative values restored through the inverse transformation.

### Model Selection and Evaluation

The prediction system uses rolling-origin evaluation to avoid using future observations when fitting historical predictions.

The current configuration includes:

- Up to 180 months of training history.
- 48 earlier rolling forecast targets for model selection.
- Mean absolute error for comparing candidate models.
- 24 later rolling targets for separate evaluation.
- Lead-specific predictive error distributions.

The median and 10th and 90th percentiles provide a point projection and a nominal 80% prediction interval.

Observed test coverage and baseline performance are displayed to help users assess model limitations.

### Seasonal Condition Indicators

Where validation criteria are satisfied, the application can estimate whether a future monthly value may fall below its historical 25th percentile or above its historical 75th percentile for that calendar month.

These indicators describe relative environmental conditions, not confirmed disaster probabilities.

The application does not currently have observed flood or drought event labels, station-based flood thresholds, or a complete set of drought classification inputs.

Consequently:

- Flood probabilities are not estimated.
- Drought probabilities are not estimated.
- Unavailable probabilities are not presented as zero.
- Experimental monthly-condition indicators are not interpreted as operational disaster warnings.

### Forecast Limitations

Future projections are subject to several limitations:

- The historical record is finite.
- The evaluation period contains only 24 later rolling targets.
- Forecast errors may be dependent.
- Changes in climate patterns or environmental regimes may reduce model reliability.
- Uncertainty in the original NASA products is not fully represented.
- The models do not represent a complete regional water budget.

The projections should be interpreted as experimental statistical estimates rather than operational forecasts.

For the complete explanation of model assumptions, evaluation, and probability availability, see [`docs/prediction_method.md`](docs/prediction_method.md).

---

## Application Architecture

Earth Trend Detective is built using Python and Streamlit, with an interactive browser-based 3D globe.

The Python application prepares the data and analysis results, then sends a payload to the browser component. User interactions with the globe and charts are handled in the browser without requiring a complete Streamlit page reload for every interaction.

### Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application logic and data processing |
| Streamlit 1.67.0 | Application framework |
| NumPy | Numerical operations and forecasting |
| JavaScript | Interactive globe and client-side behavior |
| HTML / CSS | Application interface and presentation |
| NASA Giovanni | Environmental data retrieval |

### Project Structure

```text
nasa-space-apps-team-unemployed/
│
├── app.py
│
├── data/
│   └── Saved NASA Giovanni CSV exports
│
├── services/
│   ├── contracts.py
│   ├── catalog.py
│   ├── section_a.py
│   ├── section_b.py
│   ├── investigate.py
│   ├── copy.py
│   └── prediction.py
│
├── ui/
│   ├── globe.py
│   ├── theme.py
│   └── globe_component/
│       └── index.html
│
├── tests/
│
├── docs/
│   └── prediction_method.md
│
├── .streamlit/
│   └── config.toml
│
├── requirements.txt
└── README.md
```

### Main Components

- `app.py`: Application entry point.
- `services/catalog.py`: Central catalog of environmental variables, datasets, regions, and metadata.
- `services/section_a.py`: Reads and processes saved NASA Giovanni exports.
- `services/section_b.py`: Historical trend estimation and uncertainty calculations.
- `services/investigate.py`: Coordinates data processing and analysis for the application.
- `services/copy.py`: Centralizes scientific explanations and result wording.
- `services/prediction.py`: Experimental forecasting and predictive distribution calculations.
- `ui/globe.py`: Prepares application data and renders the interactive globe.
- `ui/globe_component/`: Browser-based globe visualization.
- `tests/`: Automated tests for data processing, statistical methods, scientific wording, and application payloads.
- `docs/`: Additional technical and methodological documentation.

---

## Installation and Local Development

### Requirements

- Python 3.12
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/dhruvtp05/nasa-space-apps-team-unemployed.git

cd nasa-space-apps-team-unemployed
```

### 2. Create a Virtual Environment

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3.12 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

Open the local URL provided by Streamlit, normally:

```text
http://localhost:8501
```

### 5. Run Tests

Install pytest if it is not already available:

```bash
pip install pytest
```

Run the test suite:

```bash
python -m pytest
```

---

## Deployment

The public application is hosted on Render, with its custom domain managed through Porkbun DNS.

**Live application:** https://earthdetective.us/

The source code and deployment repository are maintained on GitHub:

https://github.com/dhruvtp05/nasa-space-apps-team-unemployed

---

## AI Use Disclosure

AI-assisted development tools were used during the planning, implementation, and testing of the application.

Cursor was used to assist with interface development, application code, and automated tests.

NASA datasets were selected and retrieved by team members through NASA Giovanni. Team members review the application's scientific explanations, data interpretation, and communication of uncertainty.

AI assistance does not replace scientific validation or independent verification of the underlying data and statistical methods.

---

## Acknowledgments and Data Resources

We acknowledge NASA and its Earth science data infrastructure for providing the publicly accessible datasets used in this project.

- [NASA Giovanni](https://giovanni.gsfc.nasa.gov/giovanni/) — Environmental data discovery, analysis, and retrieval.
- [NASA MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/) — Atmospheric reanalysis.
- [NASA GLDAS](https://ldas.gsfc.nasa.gov/gldas) — Global land data assimilation and land-surface modeling.
- [NASA GLDAS Model Output](https://ldas.gsfc.nasa.gov/gldas/model-output) — Variable definitions and product information.

Additional methodology reference:

- [Forecasting: Principles and Practice — Forecasting Toolbox](https://otexts.com/fpp3/toolbox.html)

---

## License

A project license has not yet been selected.

Until a license is added to the repository, the code should not be assumed to be available for unrestricted reuse, modification, or redistribution. NASA dataset usage remains subject to the applicable NASA data and media usage guidelines.

---

**Earth Trend Detective**  
*Exploring environmental change through NASA Earth science data.*

