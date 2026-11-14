# Master prompt: probabilistic flood outlook for Earth Trend Detective

Prepared 2026-11-14 from local and remote `main` at
`7ce465c659f38edc68ac5cf2938c81bcf7469b7e` (merged PR #1, `globe-fullscreen`).
This is a copy-ready implementation prompt. Creating this document does not
implement or validate a flood model.

---

You are a senior Python/JavaScript engineer working with a hydrologist and a
statistician on Earth Trend Detective, a NASA Space Apps project. Extend the
current application with a scientifically defensible probabilistic flood
outlook. Preserve the current full-screen globe and its visual design.

Deliver a working, source-backed flood-outlook feature first. Treat a custom ML
probability model as a separate milestone that requires appropriate data and
validation. Work through the authorized implementation and verification; when a
data requirement cannot be met, provide a useful unavailable state and identify
the missing input rather than manufacturing a successful forecast.

## 1. Start from the latest architecture

Read `AGENTS.md` if present, inspect `git status` and the current commit, then
read these files before editing:

- `README.md`, `requirements.txt`, `docs/product_plan.md`;
- `app.py`, `ui/theme.py`, `ui/globe.py`;
- `ui/globe_component/index.html`;
- `services/catalog.py`, `contracts.py`, `section_a.py`, `section_b.py`,
  `investigate.py`, and `copy.py`;
- `tests/test_app.py`, `tests/test_services.py`, and the eight CSV headers.

The reviewed baseline is `7ce465c`, but adapt if the repository has advanced.
Preserve unrelated local work. The older `docs/results_upgrade_plan.md` describes
a superseded interface and must not override the current code/product plan.

At this baseline:

- `app.py` renders one full-screen globe through `globe.render()`.
- Python builds a cached JSON payload in `ui/globe.py::build_payload()`.
- The camera tour, variable tick boxes, region labels, custom SVG charts,
  Charts & details panel, and mobile sheet run in `ui/globe_component/index.html`.
- `services/copy.py` owns scientific result wording and significance labels.
- `services/section_b.py` remains a provisional historical-trend method. Its
  fitted-line confidence band is not an event probability or a future-value
  prediction interval.
- `requirements.txt` declares only `streamlit==1.67.0`. Do not assume the old
  Plotly/pandas/numpy implementation or ML dependencies are available.
- The earlier `ui/results.py`, `compare.py`, `evidence.py`, `explore.py`,
  `focus_map.py`, `region_map.py`, and Leaflet component were removed. Do not
  recreate those screens to implement this feature.

Keep the globe, tour, controls, existing colors, region tabs, mobile behavior,
reduced-motion support, no-WebGL fallback, and historical results intact. Add
the feature inside the existing details panel, using the existing CSS patterns.

## 2. Define the product honestly

Start with one flood target; do not attempt a universal natural-disaster model.
Distinguish river flooding, rapid-onset flooding, urban surface flooding and
coastal flooding. Additional hazards require their own event definitions, data,
models and evaluation, rather than a combined disaster score.

Keep three products distinct:

1. **Official model guidance:** reproduce a verified provider's forecast and
   explain its exact probability definition.
2. **Experimental team model:** estimate a specified event probability only
   after acquiring labels and evaluating the model.
3. **Historical context:** display the existing hydroclimatic trends or
   anomalies, with their original time and geographic coverage.

The existing data are monthly, area-averaged MERRA-2/GLDAS values for two broad
US rectangles, ending in 2025. They contain no observed flood labels, gauge
thresholds, storm-scale recent inputs or archived weather forecasts. They cannot
by themselves establish a local next-day flood probability. The study boxes are
not watershed masks. GLDAS `Qs_acc` is storm surface runoff, not river stage or
total river discharge.

Never convert a slope, a significance badge, a rainfall percentile, an anomaly
score, or an arbitrary weighted sum into a percentage chance of flooding. Never
generate event labels by calling the largest monthly runoff values observed
floods. Do not equate hazard probability with damage, evacuation need or household
risk; those require exposure and vulnerability information.

## 3. First milestone: a sourced official flood outlook

Prefer a documented NOAA National Water Model probability product that covers
the chosen US demonstration area. The NOAA catalog lists 12-hour rapid-onset
and high-water probability products. Their probabilities use time-lagged ensemble
agreement with specific reach-level conditions and separate basin summaries.
Preserve the chosen product's own definition and horizon; do not replace them
with a generic claim about a town or the whole Midwest.

Before selecting an endpoint, inspect its current official metadata, schema,
units, spatial reference, timestamps, missing-value rules, coverage and access
terms. Verify whether values represent ensemble agreement, threshold exceedance,
an area summary, or another quantity. Annual exceedance probability and return
periods are not interchangeable with the probability of an event tomorrow.

Implement a bounded, server-side provider adapter with timeouts, documented
caching, schema checks and graceful failure. Do not expose credentials or add
browser requests to remote data services. Keep existing historical exploration
usable without network access. When a genuine response can be obtained, store a
small recorded fixture with its source and capture time for offline tests/demo
mode; never label an archived fixture as live. If none can be obtained, deliver
the unavailable state and clearly synthetic parser-only tests. Synthetic fixtures
must not be presented as scientific evidence.

Use a documented river reach, gauge or catchment that intersects a study area.
Explain what location the value applies to. Do not average reach probabilities
and present the result as the chance that a whole study rectangle floods. A
coverage summary may count displayed reaches, with its denominator and selection
rule, but is not a regional event probability. Missing or filtered-out features
must not silently become zero probability.

If the provider is unreachable, lacks required metadata, or does not cover the
area, show the actual reason and a source link. Continue implementing the adapter,
contract, recorded-fixture tests and UI failure states. Avoid publishing an
invented fallback percentage.

## 4. Custom ML milestone: specify the event before training

Implement this milestone only when the necessary observation and feature records
can actually be obtained. Otherwise document the unmet requirements and retain
the sourced outlook/historical-context functionality.

A suitable first custom target is:

> For a named river gauge, estimate the probability that its observed stage
> reaches or exceeds its documented minor-flood-stage threshold at least once
> during the 24 hours after the forecast issue time, conditional on information
> available by that issue time.

Record gauge/catchment identity, threshold source/version, units, vertical datum,
issue time, horizon and label coverage. Verify that observations and the
threshold share a compatible datum and unit. If no verified flood threshold is
available, do not guess one. A research-defined discharge threshold must instead
be labeled discharge exceedance, not an official flood-stage event.

This target can include an already ongoing exceedance. Show the observed current
state separately; do not describe continuation as a newly predicted onset. If
the target is changed to new onset, define that exclusion and retrain/evaluate
accordingly.

Acquire, verify and align:

- Continuous/subdaily gauge stage or appropriate observed discharge records,
  documented thresholds, quality flags, and actual labels for the future window.
- Daily/subdaily precipitation and antecedent conditions at compatible
  catchment/station scales. NASA IMERG may supply observed precipitation, but is
  not itself a future rainfall forecast; account for publication latency and
  processing-version differences.
- Forecast precipitation only from forecasts issued and available before the
  historical cutoff. Actual future rainfall is not a permitted predictor.
- Catchment geometry and identifiers, rather than treating the existing regional
  rectangles as basins. Terrain/land cover may be included if appropriately mapped.

Record measurement time, publication/availability time, retrieval time, timezone,
units, product version and transformations. Do not silently substitute final or
revised research products for near-real-time inputs in an operational replay.
Missing gauge coverage and incomplete target windows mean unknown labels, not
no flood. Absence of a disaster report is not a reliable negative label.

Start with a training-only seasonal/base-rate baseline and regularized logistic
regression. Add one more flexible challenger only if the available independent
events justify it. Keep forecast horizon and event definition identical for
all models. Fit transforms on training data only. Explain feature contributions
as model associations, not established causes.

## 5. Evaluate probability quality

Use time-ordered training, a later calibration/validation period, and a final
untouched test. Purge or embargo overlapping target windows across boundaries.
Keep the same flood episode/storm from leaking across splits through adjacent
dates or nearby gauges. If claiming transfer to new locations, add a spatial
holdout rather than relying on familiar gauges. Tune models, probability
calibration and action thresholds only on earlier data; do not select favorable
windows after seeing the final test.

Every predictor and transform must have been available at each prediction's
issue time. Test this by altering later observations and confirming earlier
features/predictions are unchanged. Do not feed centered windows, backwards-filled
future values, revised products unavailable at the cutoff, or future weather
observations into training/evaluation features.

Report actual sample sizes, independent flood-event counts, non-event coverage,
dates, geography and prevalence for every split. An abundance of adjacent hourly
rows is not an abundance of independent floods. If data are too sparse to assess
probability reliability, retain an unvalidated status and explain why.

Report Brier score and skill relative to the base-rate baseline, log loss,
reliability diagrams with bin counts, and precision–recall behavior. Show false
alarms, misses and lead time at thresholds chosen before the final test. Brier
score alone does not establish calibration; inspect reliability separately.
Retain natural event prevalence in evaluation. If training uses weighting or
resampling, evaluate/calibrate on representative, separate data. Do not invent
an accuracy score or declare success from a single favorable event.

Define release criteria before evaluating the final test. Publish the actual
result if a baseline performs better. For a custom model, withhold a validated
probability claim when event labels, calibration, temporal integrity or evaluation
are inadequate. An official provider probability remains attributed to that
provider and must not be described as the team's independently calibrated model.

## 6. A separate hazard data contract

Add a separate contract, for example `services/hazards/contracts.py`. Do not
repurpose `TrendResult`, its confidence interval, or its provisional flag.
An outlook needs at least:

- `hazard_type`, `event_definition`, `method_type` and `status`;
- `location_id`, location name, geometry/coverage and spatial reference;
- `issued_at`, `valid_start`, `valid_end`, `fetched_at`, and input cutoff;
- `probability` as a nullable number in [0, 1], plus `probability_meaning`;
- source/provider, product/model version, authoritative source URL;
- threshold definition/units/datum when applicable;
- validation summary/reference, limitations and data freshness;
- reason when unavailable, stale, out of coverage, insufficiently labeled or
  unvalidated; and snapshot metadata for a recorded demonstration.

Probability must be null when the requested estimate is unavailable. Zero is a
substantive estimate and must never be used as an error placeholder. Separate
data availability, forecast freshness and validation quality instead of forcing
all of them into one success flag. Normalize provider percentages once, validate
finite numbers, and reject ambiguous units or timestamps.

Exact input cutoffs or model-version fields may be unpublished by an official
provider. Leave these nullable and record "not supplied by provider" instead of
inventing metadata or rejecting an otherwise interpretable product. The event,
spatial applicability, issue/valid times, source and probability meaning remain
essential for presenting a current forecast.

## 7. Integrate with the current globe

Suggested boundaries, adapting names to the repository:

- `services/hazards/contracts.py`: typed outlook/provenance/status structures;
- `services/hazards/providers/noaa.py`: verified official-product adapter;
- `services/hazards/service.py`: geography selection, freshness and status logic;
- optional `services/hazards/features.py`, `model.py`, `evaluate.py` only when the
  custom model data gate passes;
- `services/copy.py`: reviewed educational/hazard wording;
- `ui/globe.py`: serialize a separate top-level hazard section with raw source
  timestamps and the appropriate precision;
- `ui/globe_component/index.html`: render the section within Charts & details;
- focused tests, small attributed fixtures, and `docs/flood_outlook.md`.

Do not calculate probabilities from the rounded chart payload in JavaScript.
Keep calculations and provider normalization in services. Preserve existing
trend payload semantics, stripe meaning and significance tests.

Two current implementation details require explicit handling:

1. `_cached_payload` currently keys historical content on local data-file
   signatures. Time-sensitive forecast data need a separate freshness-aware
   cache; a changing forecast cannot depend solely on a static CSV signature.
2. The component's `streamlit:render` listener currently ignores later payloads
   once `started` is true. If updates are supported, handle hazard updates
   deliberately while preserving camera, selected variables, region and panel
   state. A cache TTL alone does not refresh an already-open browser panel.

For an initial load-only version, explicitly show when data were loaded and how
to refresh; do not claim continuous live updates. Mark a forecast stale/expired
when its actual validity ends, including when a user leaves the page open. Keep
network failures from resetting the globe tour or crashing the trend viewer.

Add a compact **Flood outlook** section within the existing region details
panel. Beside a number show the defined event, actual location, source, issue
time, valid window and source/validation status. Explain the probability's
meaning in ordinary language. Label recorded forecasts and team experiments
clearly. Preserve the amber/violet/gray meanings for historical trends; do not
reuse a Significant badge to imply high flood likelihood.

Keep the hazard section separate from the per-variable rendering loop so it can
be read even when all historical variable boxes are unticked. The current panel
header uses `P.provisional`, and its footer applies `P.text.saved_data` broadly.
Scope those notices explicitly to historical trends; an official forecast needs
its own source, freshness and validation labels. Do not describe live provider
guidance as the team's provisional historical method or saved NASA time series.

Include brief **Why this matters** and **What this does not establish** copy.
Use a concise educational/experimental label and link to the relevant official
forecast/warning source. Do not imply that the app issues emergency warnings or
that a low probability guarantees safety. Preserve keyboard operation, reduced
motion, no-WebGL access, mobile sheet layout and readable text alternatives.
Escape external strings and validate source links before inserting them into
the component's HTML.

## 8. Verification and handoff

Run existing tests before and after implementation. Add tests that matter:

- Provider probability scale, event semantics, timestamps, CRS/geometry and units.
- Null versus zero; missing metadata; stale/expired response; empty coverage;
  timeout; unavailable network; recorded snapshot clearly marked historical.
- Hazard payload serialization, finite numbers and scientific wording separate
  from historical significance/confidence-band wording.
- Freshness-aware caching and any later-payload update path without resetting
  the tour or selected state.
- For custom ML: cutoff integrity, episode separation, incomplete labels,
  chronology of calibration, representative prevalence and honest baseline loss.
- Real browser checks for panel interactions, changing region, no-WebGL and
  narrow-screen behavior. Streamlit AppTest does not exercise the custom frontend.

Update exact control/markup assertions only for intentional additions to the
existing panel. Preserve their original intent rather than deleting tests to
make the suite pass. Keep remote data retrieval server-side and existing bundled
assets local. Add dependencies only when used, preserving the Streamlit pin;
keep heavy optional training packages separate if the viewer does not need them.

Deliver code, tests and documentation stating what is implemented, what data
were actually used, and what remains unsupported. Include an attributed recorded
fixture when a genuine response was obtainable; otherwise document that gap and
keep synthetic parser-only fixtures out of the scientific demonstration.
Include the event/location/horizon, provider or model, source links, observed
evaluation results if any, and a short demo walkthrough. Never invent a successful
training run or substitute a mock screenshot for a working feature.

Begin by reporting the current architecture and selecting the official-product
MVP. Then implement and verify the smallest end-to-end version. Progress on
independent ingestion/UI work when custom-model data are missing, and surface
the exact unmet requirement.

## Authoritative starting references

Recheck current product metadata and API documentation at implementation time.

- NOAA flood products and their precise probability definitions:
  https://water.noaa.gov/about/data-and-web-services-catalog
- NOAA National Water Model:
  https://water.noaa.gov/about/nwm
- USGS observations and station metadata:
  https://api.waterdata.usgs.gov/
- NASA IMERG observed precipitation:
  https://gpm.nasa.gov/data/imerg
- NASA GLDAS output-variable definitions:
  https://ldas.gsfc.nasa.gov/gldas/model-output
- Probability calibration and its evaluation:
  https://scikit-learn.org/stable/modules/calibration.html
- Alternative river-flood provider and its scope:
  https://global-flood.emergency.copernicus.eu/general-information/about-glofas/
