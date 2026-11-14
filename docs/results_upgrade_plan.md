# Results screen and investigation upgrade plan

Prepared 2026-11-14 against commit `312da9f`. This is an implementation plan;
application behavior has not been changed by this document.

## Intended outcome

A student should be able to identify the result, understand its magnitude and
uncertainty, explain why the variable matters, and investigate whether the answer
depends on dates. Forecasting is a separate, evaluated experiment.

Keep the existing Streamlit application and Section A/B/C boundaries. Preserve
source links, provisional labels, table alternatives, and cautious result wording.
The challenge explicitly accepts basic linear trends and significance assessment
through confidence intervals; ML is an optional extension.

## What the current screen makes difficult

- `app.py::_render_results` assigns 45% of the page to a 620px map. The result,
  controls, and chart share the remaining 55%. A map remains useful context, but
  the historical evidence deserves most of the width.
- `ui/results.py::render` repeats parts of the finding, interval, conclusion, and
  limitations before the main exploration actions. The chart starts too late.
- `ui/theme.py` implements panel dark mode with CSS inversion. Explicit interface
  and Plotly colors will preserve chart colors and text contrast more predictably.
- Short selections can reach `ui/compare.py` with no annual arrays. The chart is
  empty while its description still refers to annual means and fitted lines.
- There is no result-specific explanation of relevance or deliberate two-window
  comparison. Forecast currently opens a planned-feature notice.

## Proposed results hierarchy

1. **Compact context:** region, variable, selected dates; source product, data end
   date and analysis status nearby. Use one persistent provisional notice.
2. **Finding:** a concise, status-aware conclusion. Keep estimated direction
   separate from whether its confidence interval excludes zero.
3. **Magnitude and evidence:** trend per decade, 95% slope interval, and usable
   years. A small interval plot with a zero reference can explain the interval.
   Do not turn confidence levels into a probability that a claim is true.
4. **Main chart:** annual means and the historical fit, with monthly observations
   available as a toggle. Place seasonal and distribution views behind a
   secondary selector. Axes always state the variable, units and dates.
5. **Why this matters:** sourced variable context, result-specific meaning, and
   a concise boundary on interpretation.
6. **Investigation actions:** compare regions, change the time window, and
   inspect the data and method. Forecast becomes available only through a
   validated forecast workflow.
7. **Details:** expandable coverage, assumptions, tables, provenance and downloads.

Desktop: evidence uses roughly 75% of the width and a compact context/map rail
uses 25%; keep controls usable rather than forcing this exact ratio at all sizes.
Mobile: finding and chart precede the optional map; controls wrap or stack. The
large results chart must not be squeezed next to a tall map. At 1440x900 the
finding and the beginning of the chart should be visible without scrolling.

Use one coherent theme across the result and chart, keyboard-accessible controls,
consistent focus states, restrained emphasis, and labels/line styles in addition
to color. Keep readable table and text alternatives.

## Explain importance without inventing impact

Use reviewed templates and computed values, not an unconstrained generated
scientific narrative. Add `services/interpretation.py` and a small source-backed
variable context catalog. Suggested structured fields:

- `finding`: direction, magnitude, dates, unit and interval from `TrendResult`.
- `relevance`: what this variable helps people investigate, with a source URL.
- `magnitude_context`: optional comparison with a defined reference mean or an
  externally justified threshold; include the reference dates and denominator.
- `limits`: regional averaging, product type, component/depth, provisional status,
  and unmeasured downstream consequences.
- `next_question`: a relevant window, region, or related-variable investigation.

For soil moisture, a panel could read:

> **Why study this?** Water near the soil surface is relevant to drying and
> wetting, and soil-moisture information supports drought and flood research.
>
> **What this result says:** The estimated historical direction and its interval
> describe this selected region and period, under the method's assumptions.
>
> **What remains unknown:** Top-10-cm regional model output does not establish
> crop losses, root-zone drought, household shortages, or the cause of the change.

NASA's [SMAP mission explanation](https://www.jpl.nasa.gov/missions/soil-moisture-active-passive-smap/)
supports general soil-moisture relevance. Clearly identify that the app's existing
series is GLDAS Noah, not a SMAP observation. For runoff use the delivered
`Qs_acc` component; it is not total river discharge or usable water supply.

Absolute trend magnitude can be supplemented with a clearly labeled fitted
historical change between the first and last annual timestamps. Derive it from
the analysis output. It is distinct from the observed difference between endpoint
years, a change in monthly totals, or a forecast. Percentages require a meaningful,
nonzero reference and add uncertainty; omit them when they would mislead.

Do not assign a generic "high impact" score or equate statistical significance
with practical importance. Practical importance needs external context that the
current files do not supply. Precipitation, evaporation, runoff and topsoil water
also do not constitute a closed water budget: the products, grids, components
and units differ.

## Time-window investigation

Add `services/window_sensitivity.py` and `ui/window_compare.py`, reusing
`investigate.load`. Begin with prespecified full-record and recent windows with
a common end year. For every window show both dates, valid years, slope, interval,
method, and status. Use a shared vertical scale for the time-series plot and a
zero reference on the slope-interval plot. Explain overlapping periods.

Real values from the current provisional method illustrate the need:

| Midwest soil moisture | Trend (kg/m² per decade) | 95% slope interval |
|---|---:|---:|
| 2005–2025 | -0.734 | -1.560 to +0.092 |
| 2015–2025 | -2.147 | -4.142 to -0.153 |

Both estimated directions are downward. Whether the interval excludes zero
depends on the selected dates. This illustrates sensitivity, not established
acceleration or a causal effect. The numbers remain provisional and must be
reviewed with Section B before use as a published finding.

Never choose the displayed window because it produces significance. If a later
start/end grid is added, display every eligible choice and mark it exploratory.
The fraction of overlapping windows that excludes zero is not a confidence level.
A genuine claim that slopes differ requires a separate, appropriate analysis.

## Forecasting and ML: a testable extension

The useful question is **"Can a model predict months it has not seen?"** A good
answer supports predictive skill for the tested data and horizons. It does not
prove a cause, a future climate outcome, or that a historical trend is significant.

Each regional series contains 252–312 monthly values, or only 21–26 annual means.
Start with small models on monthly data. A neural network is unnecessary for the
first version.

1. **Target and origin:** forecast one variable/region 1 and 3 months ahead.
   The latest saved observation is December 2025. Forecast dates must be based on
   that observation or an explicitly selected historical backtest origin, not the
   computer's current date. A present-day outlook requires more recent input data.
2. **Baselines:** same calendar month last year (seasonal naive) and calendar-month
   climatology computed only from training observations.
3. **First ML candidate:** regularized linear regression using observed lags
   1/2/3/12, shifted trailing means, and month-of-year features. Optional later
   challenger: gradient boosting. Unknown future inputs cannot be supplied from
   the actual future record. Fit scaling and feature transforms on training data.
4. **Evaluation:** rolling forecast origins using dates through 2023 for development;
   reserve 2024–2025 as an untouched final test. Freeze features, tuning, baselines,
   metrics and model selection before that test. Do not reuse the final test for
   further tuning. Evaluate the same origins and horizons for every model.
5. **Multi-step validity:** build every feature from values available at the
   forecast origin. Predicting three months ahead must not use the actual values
   of the intervening future months. State whether forecasts are direct or recursive.
6. **Report skill:** MAE/RMSE in the variable's units, skill versus the strongest
   baseline, dates, sample counts, folds, and horizon. Avoid MAPE for near-zero
   runoff. Report weak or inconsistent skill honestly; retain a better baseline.
7. **Prediction uncertainty:** compute future-value prediction intervals using
   a justified method. Measure coverage and width on held-out forecasts. Quantile
   models do not automatically provide calibrated intervals. Never reuse a slope
   confidence interval as a future observation band.
8. **Display gate:** numerical forecasts require adequate history, valid
   preprocessing, known origins, completed backtests and interval diagnostics.
   If no model beats the baseline, show that result; do not manufacture an ML win.
   If intervals are unreliable, explain the limitation and withhold a confident
   outlook rather than presenting a calibrated probability.

Use a new forecast contract/service rather than attaching future predictions to
`TrendResult`. Proposed `ForecastResult` includes status, origin, training dates,
horizons, model and baseline identifiers, backtest dates/counts, horizon-specific
metrics, prediction dates/values, prediction bounds, nominal level, empirical
coverage/width and warnings. Coordinate contract changes with Sections A/B.

The UI should distinguish **historical observations**, **held-out predictions**,
and **future forecasts** with labels, line styles and a visible origin divider.
Offer a "Replay a forecast" view before an outlook view: hide a historical block,
show the model's predictions, then reveal actual data and the baseline comparison.
Clearly label backtests as retrospective, not new observations or causal tests.

Primary guidance: [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html),
[scikit-learn lagged-feature forecasting example](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html),
and the authors' [Forecasting: Principles and Practice toolbox](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation).

## Implementation sequence and completion criteria

| Phase | Work and likely files | Completion criteria |
|---|---|---|
| 1. Reliable result states | `ui/compare.py`, `ui/results.py`, `ui/explore.py`, `tests/test_app.py` | Short windows show real monthly observations or a useful empty state; descriptions match traces; recovery actions work; validity guidance comes from the active method. |
| 2. Results layout | `app.py`, `ui/results.py`, `ui/theme.py`, Plotly styles | Finding/chart appear early; map is secondary; 1440/1024/390px layouts work; no horizontal overflow; both themes preserve contrast and series meaning. |
| 3. Importance and reproducibility | `services/interpretation.py`, context catalog, `ui/results.py`, `ui/evidence.py`, dataset manifest | Every relevance claim has a supporting source; generated copy respects status and units; JSON includes context sources and reference definitions; unknown dates stay unknown. |
| 4. Window sensitivity | `services/window_sensitivity.py`, `ui/window_compare.py`, routing, tests | Two explicitly labeled periods use the same variable/method and scales; all eligible results remain visible; overlapping windows and insufficient history are explained. |
| 5. Forecast evaluation | New `services/forecast.py`, contract, offline evaluation script/report | Reproducible chronological folds; no future leakage; common baseline evaluation dates; frozen final test; metrics/interval diagnostics per horizon. |
| 6. Forecast experience | New `ui/forecast.py`, routing and tests | Backtest and future origin are unmistakable; model/baseline performance visible; unavailable or weak results handled accurately; no unsupported claims of proof. |
| 7. Demo and usability | `docs/research_notes.md`, README, public project submission | Three users can explain the finding, interval, geography, relevance and window sensitivity; demo links work; reviewed method and provenance accompany the submission. |

Phases 1–4 are the recommended next contribution. Phase 5 is a distinct analysis
task; Phase 6 depends on its outputs. Keep reviewed provisional labels until
Section B accepts and validates the production method.

## Verification checklist

Verification performed while preparing this plan: installed pytest in the existing
project virtual environment, ran the existing suite successfully (**42 passed**),
and opened the application in a browser through the selection and results screens.
The Streamlit test harness required an unrestricted local socket pair; the suite
passed outside the restricted sandbox. Production UI/analysis code is unchanged.

Reproduce with `.venv/Scripts/python.exe -m pytest -q` from the repository root.
The proposed interface preview uses explicit chart-placement wireframes; it does
not represent a completed production screen or a trained forecast model.

- Existing service and Streamlit app tests pass in the project virtual environment.
- Add meaningful tests for short-period comparison and status-appropriate content.
- Interpretation tests cover positive/negative/zero-crossing intervals, invalid
  results, provisional flags, missing context and unit/reference handling.
- Window tests verify period labels, eligible/ineligible windows and consistent
  analysis settings, rather than merely mirroring presentation code.
- Forecast tests catch preprocessing and multi-step future leakage, mismatched
  model/baseline dates, insufficient history, baseline wins and origin labeling.
- Verify actual keyboard operation, dark/light contrast, table alternatives and
  responsive reading order in a browser; app tests do not fully exercise custom
  globe/Leaflet components.
- In three short usability sessions, ask users to explain an interval containing
  zero, distinguish relevance from measured harm, and explain why window results
  and forecast skill do not establish causality.
