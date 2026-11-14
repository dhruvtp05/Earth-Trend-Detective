"""Experimental monthly predictive distributions, separate from trend analysis.

Select a seasonal baseline or damped seasonal-trend model on earlier rolling
forecasts. Estimate its error distribution on that development period and report
performance on 24 later targets. Every origin uses only earlier observations.
These are regional water-variable forecasts, not flood/drought event models.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from math import isfinite

import numpy as np

from .contracts import SeriesPoint

BASELINE = "Seasonal baseline"
TREND = "Damped seasonal trend"
MODELS = (BASELINE, TREND)
MIN_HISTORY = 120
DEVELOPMENT = 48
TEST = 24
TRAIN_WINDOW = 180
VERSION = "monthly-distribution-v1"


class PredictionUnavailable(ValueError):
    pass


def month_number(when: date) -> int:
    return when.year * 12 + when.month - 1


def add_months(when: date, count: int) -> date:
    year, month = divmod(month_number(when) + count, 12)
    return date(year, month + 1, 1)


def _raw(log_values):
    # Water quantities are nonnegative. Truncation is part of the model and is
    # applied identically to the development, test and future distributions.
    return np.maximum(0.0, np.expm1(np.clip(log_values, -30, 30)))


def _validate(points: list[SeriesPoint]) -> tuple[list[date], np.ndarray]:
    points = sorted(points, key=lambda point: point.date)
    dates = [date(p.date.year, p.date.month, 1) for p in points]
    values = np.asarray([p.value for p in points], dtype=float)
    if not dates or not all(isfinite(float(value)) and value >= 0 for value in values):
        raise PredictionUnavailable("Complete, finite, nonnegative monthly observations are required.")
    if any(month_number(b) - month_number(a) != 1 for a, b in zip(dates, dates[1:])):
        raise PredictionUnavailable("The saved series has missing or duplicate months.")
    return dates, values


def _fit(values: np.ndarray, dates: list[date], origin: int, model: str):
    """Fit only the trailing history available at this forecast origin."""
    first = max(0, origin + 1 - TRAIN_WINDOW)
    history = values[first : origin + 1]
    months = np.asarray([d.month - 1 for d in dates[first : origin + 1]])
    logs = np.log1p(history)
    time = np.arange(len(history), dtype=float) / 12
    if model == BASELINE:
        seasonal = np.asarray([logs[months == m].mean() for m in range(12)])
        slope = 0.0
        fitted = seasonal[months]
    else:
        design = np.column_stack([np.eye(12)[months], time])
        try:
            coefficients = np.linalg.lstsq(design, logs, rcond=None)[0]
        except np.linalg.LinAlgError as exc:
            raise PredictionUnavailable("The forecast model could not be fitted to this record.") from exc
        seasonal, slope = coefficients[:12], float(coefficients[-1])
        fitted = design @ coefficients
    residuals = logs - fitted
    scale = np.asarray([
        max(float(np.std(residuals[months == m], ddof=1)), 0.01)
        for m in range(12)
    ])
    return seasonal, slope, time[-1], scale, history, months


def _predict(fit, target: date, lead: int) -> tuple[float, float, float, float, float, float]:
    seasonal, slope, last_time, scale, history, months = fit
    month = target.month - 1
    effective_lead = sum(0.95**step for step in range(1, lead + 1)) / 12
    log_value = float(seasonal[month] + slope * (last_time + effective_lead))
    reference = history[months == month]
    lower, upper = (float(x) for x in np.quantile(reference, [0.25, 0.75]))
    return (
        log_value, float(scale[month]), lower, upper,
        float(np.mean(reference < lower)), float(np.mean(reference > upper)),
    )


def _distribution(prediction, errors: np.ndarray) -> np.ndarray:
    return _raw(prediction[0] + prediction[1] * errors)


def _tail_metrics(probabilities, actuals, baselines) -> dict:
    actuals = np.asarray(actuals, dtype=float)
    score = float(np.mean((np.asarray(probabilities) - actuals) ** 2))
    reference_score = float(np.mean((np.asarray(baselines) - actuals) ** 2))
    events = int(actuals.sum())
    skill = 1 - score / reference_score if reference_score > 1e-12 else None
    # A modest diagnostic gate, not a claim of operational calibration.
    supported = events >= 3 and TEST - events >= 3 and skill is not None and skill > 0
    return {"brier": score, "baseline_brier": reference_score, "skill": skill,
            "events": events, "targets": TEST, "supported": bool(supported)}


def forecast(points: list[SeriesPoint], *, as_of: date, months: int = 12) -> dict:
    """Forecast months strictly after both today and the last saved observation.

    Error distributions and tests use the same lead as each future target,
    including the gap between the saved record and the generation date.
    """
    if months < 1 or months > 12:
        raise PredictionUnavailable("Choose between 1 and 12 future months.")
    dates, values = _validate(points)
    if dates[-1] > as_of:
        raise PredictionUnavailable("The saved record contains observations after the generation date.")
    start = add_months(as_of, 1)
    targets = [add_months(start, i) for i in range(months)]
    leads = [month_number(d) - month_number(dates[-1]) for d in targets]
    if leads[-1] > 36:
        raise PredictionUnavailable("The saved observations are too old for this forecast. Add more recent data.")

    @lru_cache(maxsize=None)
    def fit(origin: int, model: str):
        return _fit(values, dates, origin, model)

    output = []
    for target, lead in zip(targets, leads):
        test_start = len(values) - TEST
        development_end = test_start - lead
        development_start = development_end - DEVELOPMENT + 1
        if development_start - lead + 1 < MIN_HISTORY:
            raise PredictionUnavailable("Not enough history to evaluate this forecast lead on separate later months.")

        def at(index: int, model: str):
            return _predict(fit(index - lead, model), dates[index], lead)

        development_indices = range(development_start, development_end + 1)
        development_predictions = {
            model: [at(i, model) for i in development_indices] for model in MODELS
        }
        development_mae = {
            model: float(np.mean([
                abs(float(values[i]) - float(_raw(pred[0])))
                for i, pred in zip(development_indices, development_predictions[model])
            ])) for model in MODELS
        }
        selected = min(MODELS, key=development_mae.get)
        errors = {
            model: np.asarray([
                (float(np.log1p(values[i])) - pred[0]) / pred[1]
                for i, pred in zip(development_indices, development_predictions[model])
            ]) for model in MODELS
        }
        test_mae, coverage, widths = {}, [], []
        low_probabilities, high_probabilities = [], []
        low_actuals, high_actuals, low_baselines, high_baselines = [], [], [], []
        for model in MODELS:
            absolute_errors = []
            for i in range(test_start, len(values)):
                pred = at(i, model)
                samples = _distribution(pred, errors[model])
                low, median, high = (float(v) for v in np.quantile(samples, [0.1, 0.5, 0.9]))
                absolute_errors.append(abs(float(values[i]) - median))
                if model == selected:
                    # A perfectly repeating series can have a zero-width
                    # interval; log/expm1 round-off must not turn an exact
                    # prediction into a coverage failure.
                    tolerance = 1e-10 * max(1.0, abs(float(values[i])), abs(low), abs(high))
                    coverage.append(low - tolerance <= values[i] <= high + tolerance)
                    widths.append(high - low)
                    low_probabilities.append(float(np.mean(samples < pred[2])))
                    high_probabilities.append(float(np.mean(samples > pred[3])))
                    low_actuals.append(values[i] < pred[2])
                    high_actuals.append(values[i] > pred[3])
                    low_baselines.append(pred[4])
                    high_baselines.append(pred[5])
            test_mae[model] = float(np.mean(absolute_errors))

        observed_coverage = float(np.mean(coverage))
        low_metrics = _tail_metrics(low_probabilities, low_actuals, low_baselines)
        high_metrics = _tail_metrics(high_probabilities, high_actuals, high_baselines)
        future = _predict(fit(len(values) - 1, selected), target, lead)
        samples = _distribution(future, errors[selected])
        lower, median, upper = (float(v) for v in np.quantile(samples, [0.1, 0.5, 0.9]))
        usable_interval = observed_coverage >= 0.65
        baseline_ok = test_mae[selected] <= test_mae[BASELINE] + 1e-12
        for metrics in (low_metrics, high_metrics):
            metrics["supported"] = bool(metrics["supported"] and usable_interval and baseline_ok)
        output.append({
            "date": target.isoformat(), "lead_months": lead, "median": median,
            "lower": lower, "upper": upper, "model": selected,
            "reference_lower": future[2], "reference_upper": future[3],
            "p_below": float(np.mean(samples < future[2])) if low_metrics["supported"] else None,
            "p_above": float(np.mean(samples > future[3])) if high_metrics["supported"] else None,
            "validation": {
                "development_start": dates[development_start].isoformat(),
                "development_end": dates[development_end].isoformat(),
                "first_test_origin": dates[test_start - lead].isoformat(),
                "test_start": dates[test_start].isoformat(), "test_end": dates[-1].isoformat(),
                "targets": TEST, "coverage": observed_coverage,
                "interval_width": float(np.mean(widths)), "mae": test_mae[selected],
                "baseline_mae": test_mae[BASELINE], "development_mae": development_mae,
                "low_tail": low_metrics, "high_tail": high_metrics,
                "limited_skill": not usable_interval or not baseline_ok,
            },
        })
    return {
        "status": "experimental", "version": VERSION, "as_of": as_of.isoformat(),
        "origin": dates[-1].isoformat(), "data_start": dates[0].isoformat(),
        "gap_months": max(0, month_number(as_of) - month_number(dates[-1])),
        "interval_level": 0.80, "months": output,
        "history": {"dates": [d.isoformat() for d in dates[-24:]],
                    "values": [float(v) for v in values[-24:]]},
        "disaster_probability": {"flood": None, "drought": None},
    }
