# NASA Earth System Dataset Guide

This repository uses monthly, area-averaged regional time-series datasets extracted via **NASA Giovanni** (`giovanni.gsfc.nasa.gov`) to compare hydroclimatic trends across two contrasting US regions.

## Study Regions
* **Region A — US Southwest (Colorado River Basin):** `-115, 31, -106, 40` (Arid/semi-arid snowmelt-dependent basin)
* **Region B — US Midwest (Great Lakes Basin):** `-93, 40, -76, 49` (Humid continental basin)

---

## Variables & Plain-English Definitions

### 1. Total Surface Precipitation (`precip`)
* **Files:** `data/southwest_precip_regionA.csv`, `data/midwest_precip_regionB.csv`
* **Plain-English Definition:** The total amount of water (rain and melted snow) falling onto the Earth's surface per day, averaged across each month.
* **Trend Significance:** Shows whether a region is receiving more or less total water input over time—often shifting in opposite directions across neighboring regions.
* **Source & Resolution:** NASA MERRA-2 Reanalysis (`M2TMNXFLX v5.12.4`), Monthly, `0.5° × 0.625°`

### 2. Surface Evapotranspiration / Land Evaporation (`evap`)
* **Files:** `data/southwest_evap_regionA.csv`, `data/midwest_evap_regionB.csv`
* **Plain-English Definition:** The rate at which water leaves the land surface and enters the atmosphere through direct soil/water evaporation and plant transpiration.
* **Trend Significance:** Warmer air increases atmospheric water demand, pulling moisture out of soils and rivers even when precipitation remains steady.
* **Source & Resolution:** NASA MERRA-2 Reanalysis (`M2TMNXLND v5.12.4`), Monthly, `0.5° × 0.625°`

### 3. Surface & Subsurface Runoff (`runoff`)
* **Files:** `data/southwest_runoff_regionA.csv`, `data/midwest_runoff_regionB.csv`
* **Plain-English Definition:** Excess water from rainfall or snowmelt that flows over land and through upper soil layers into streams, rivers, and reservoirs.
* **Trend Significance:** Measures usable surface water availability for cities, ecosystems, and agriculture.
* **Source & Resolution:** NASA MERRA-2 / GLDAS Land Surface Diagnostics, Monthly

### 4. Surface Soil Moisture Content, 0–10 cm (`soilmoisture`)
* **Files:** `data/southwest_soilmoisture_regionA.csv`, `data/midwest_soilmoisture_regionB.csv`
* **Plain-English Definition:** The amount of water stored in the top 10 centimeters of soil.
* **Trend Significance:** Integrates precipitation, evaporation, and runoff into a direct indicator of agricultural drought or soil saturation.
* **Source & Resolution:** NASA GLDAS Noah Land Surface Model, Monthly, `0.25° × 0.25°`