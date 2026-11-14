"""Chronology, probability availability and distribution checks."""

from datetime import date
import json

import numpy as np
import pytest

from services import prediction, section_a
from services.contracts import SeriesPoint


def seasonal_points():
    return [SeriesPoint(date(2000 + i // 12, i % 12 + 1, 1), float(i % 12 + 1)) for i in range(26 * 12)]


def test_future_targets_account_for_the_gap_since_saved_observations():
    result = prediction.forecast(seasonal_points(), as_of=date(2026, 11, 14))
    assert result["origin"] == "2025-12-01"
    assert result["gap_months"] == 11
    assert result["months"][0]["date"] == "2026-12-01"
    assert result["months"][-1]["date"] == "2027-11-01"
    assert [m["lead_months"] for m in result["months"]] == list(range(12, 24))
    for month in result["months"]:
        assert month["lower"] <= month["median"] <= month["upper"]
        assert month["median"] == pytest.approx(int(month["date"][5:7]))
        v = month["validation"]
        assert v["development_end"] <= v["first_test_origin"] < v["test_start"]
        assert v["targets"] == 24
        assert v["coverage"] == 1
    assert result["disaster_probability"] == {"flood": None, "drought": None}
    json.dumps(result, allow_nan=False)


def test_development_and_origin_fit_cannot_see_later_values():
    points = seasonal_points()
    points = [SeriesPoint(p.date, p.value + 0.1 * np.sin(i)) for i, p in enumerate(points)]
    altered = [SeriesPoint(p.date, p.value + 100 if p.date > date(2023, 1, 1) else p.value) for p in points]
    original_result = prediction.forecast(points, as_of=date(2026, 11, 14), months=1)["months"][0]
    altered_result = prediction.forecast(altered, as_of=date(2026, 11, 14), months=1)["months"][0]
    assert original_result["validation"]["first_test_origin"] == "2023-01-01"
    assert original_result["validation"]["development_mae"] == altered_result["validation"]["development_mae"]
    assert original_result["model"] == altered_result["model"]
    dates, values = prediction._validate(points)
    _, future_values = prediction._validate(altered)
    origin = dates.index(date(2023, 1, 1))
    for model in prediction.MODELS:
        before = prediction._predict(prediction._fit(values, dates, origin, model), date(2024, 1, 1), 12)
        after = prediction._predict(prediction._fit(future_values, dates, origin, model), date(2024, 1, 1), 12)
        assert before == pytest.approx(after)


def test_probabilities_are_unavailable_without_independent_tail_evidence():
    result = prediction.forecast(seasonal_points(), as_of=date(2026, 11, 14), months=1)
    month = result["months"][0]
    assert month["p_below"] is None and month["p_above"] is None
    assert month["validation"]["low_tail"]["events"] == 0


@pytest.mark.parametrize("change", ["missing", "duplicate", "nan", "negative", "short"])
def test_unsupported_data_refuses_a_numerical_forecast(change):
    points = seasonal_points()
    if change == "missing": points.pop(100)
    elif change == "duplicate": points.append(points[100])
    elif change == "nan": points[100].value = float("nan")
    elif change == "negative": points[100].value = -1
    elif change == "short": points = points[-120:]
    with pytest.raises(prediction.PredictionUnavailable):
        prediction.forecast(points, as_of=date(2026, 11, 14))


def test_real_series_with_weak_interval_check_withholds_indicator_probability():
    points, _ = section_a.get_series("midwest", "precip", date(2005, 1, 1), date(2025, 12, 31))
    month = prediction.forecast(points, as_of=date(2026, 11, 14), months=1)["months"][0]
    assert month["validation"]["limited_skill"]
    assert month["p_below"] is None and month["p_above"] is None


def test_data_dated_after_generation_is_not_used_as_if_known():
    with pytest.raises(prediction.PredictionUnavailable, match="after the generation date"):
        prediction.forecast(seasonal_points(), as_of=date(2020, 1, 1))
