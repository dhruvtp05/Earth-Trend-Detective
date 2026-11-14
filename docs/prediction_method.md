# Experimental monthly prediction

The Prediction tab replaces the yellow historical Provisional header badge in
the existing globe details panel. Historical provisional wording remains in the
historical details footer. The globe, region tabs and historical trend method
are preserved.

## Inputs and dates

Each region/variable uses its saved monthly NASA CSV, in the units supplied by
Section A. Inputs must be contiguous, unique, finite and nonnegative. The saved
files currently end in December 2025. Forecast targets start in the calendar
month after the generation date in America/Chicago. A projection for December
2026 therefore has a 12-month lead from December 2025, not a one-month lead.
Forecast tests use that same lead. No recent observations are invented to fill
the gap. The UI records origin, generation date and target dates.

## Models and predictive distribution

The candidates are a seasonal baseline and a damped seasonal trend. They use up
to 180 earlier months and the log1p transform. The baseline fits a mean for each
calendar month. The trend model fits calendar-month fixed effects and a linear
time term, then damps extrapolated trend increments by 0.95 per month. Predictive
samples return through expm1 and are truncated at zero; this transformation is
also applied in evaluation.

For every lead, 48 earlier rolling targets select the model by mean absolute
error. Their log-scale errors, scaled by origin-specific calendar-month spread,
provide an empirical distribution. Twenty-four later targets are evaluated
separately. Development ends by the first test origin, even for long leads.
Training, reference quartiles and scales are fitted only using observations
available at each origin. Earlier test observations become available to later
rolling origins, which is explicitly not a frozen-model test.

The median and 10th/90th quantiles provide a point forecast and nominal 80%
prediction range. This is a model-based distribution, not an operationally
calibrated weather forecast. Shared monthly errors are dependent, only 24 test
targets are available, and data-source uncertainty/regime changes are not fully
represented. Display actual coverage and error; do not interpret the historical
trend confidence band as this predictive range.

## Probabilities and unavailable states

An experimental seasonal indicator can estimate the chance that a future month
is below the historical 25th percentile or above the 75th percentile for that
calendar month. Future references use the trailing saved history; test references
are fitted only on history at each test origin. These are relative water-variable
events, not flood/drought labels.

Indicator percentages are withheld unless the relevant lead has at least three
positive and three negative test cases, positive Brier skill against a
training-only seasonal reference, at least 65% observed coverage for the nominal
80% interval, and selected-model error no worse than the baseline. These are
predeclared diagnostic gates, not a certification of calibration. Failure means
`null`/Unavailable, never zero. Point/range projections remain visible with a
limited-skill label when the interval/baseline check fails.

Topsoil moisture below a seasonal quartile is a near-surface dryness indicator;
surface runoff above a quartile is a wetness indicator. The saved regional model
output has no flood-event labels, station flood thresholds or drought-event
labels. Flood and drought probabilities are therefore `null`; separate factors
are never multiplied into a disaster score. Different products/grids/components
also do not form a closed water budget.

## Reproduction

Run `python -m pytest`. `tests/test_prediction.py` checks future date alignment,
lead-aware split boundaries, future-data perturbation, perfect seasonal data,
unsupported records, and unavailable probability states. Globe payload tests
cover all eight series and preserve historical semantics. Browser checks are
required for the component's tab, selectors, charts and mobile behavior.

Reference methodology: [rolling-origin evaluation and predictive distributions](https://otexts.com/fpp3/toolbox.html).
[US Drought Monitor classification](https://droughtmonitor.unl.edu/About/AbouttheData/DroughtClassification.aspx)
illustrates why a single topsoil measure is not a complete drought diagnosis.
[NASA GLDAS output definitions](https://ldas.gsfc.nasa.gov/gldas/model-output)
distinguish surface runoff, baseflow and soil-water quantities.
