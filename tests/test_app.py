"""Clicks through the app headlessly and checks each screen renders."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _start() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    return app


def _click(app: AppTest, label: str) -> AppTest:
    matches = [button for button in app.button if button.label == label]
    assert matches, f"No button labelled {label!r}; found {[b.label for b in app.button]}"
    matches[0].click().run()
    assert not app.exception, app.exception
    return app


def _text(app: AppTest) -> str:
    parts = []
    for kind in ("title", "header", "markdown", "caption", "info", "warning", "error"):
        parts += [element.value for element in getattr(app, kind)]
    return "\n".join(parts)


def test_landing():
    app = _start()
    assert app.title[0].value == "Explore how a place has changed"
    assert [b.label for b in app.button] == ["Explore the Midwest example", "Choose a region"]


def test_midwest_example_shows_result_chart_and_provisional_notice():
    app = _click(_start(), "Explore the Midwest example")
    text = _text(app)
    assert "Precipitation in the Midwest, 2005–2025" in text
    assert "has an estimated trend of" in text
    assert "The 95% confidence interval for the trend is" in text
    assert "Provisional trend" in text
    assert "not measurements at a single place" in text
    assert len(app.metric) == 2
    assert len(app.get("plotly_chart")) == 2
    assert len(app.get("download_button")) == 2


def test_evidence_and_back():
    app = _click(_start(), "Explore the Midwest example")
    app = _click(app, "Inspect method and sources")
    text = _text(app)
    assert "Inspect the evidence" in text
    assert "MERRA-2" in text and "5.12.4" in text
    assert "Ordinary least squares" in text
    app = _click(app, "Back to the result")
    assert "Precipitation in the Midwest, 2005–2025" in _text(app)


def test_compare_view():
    app = _click(_start(), "Explore the Midwest example")
    app = _click(app, "Compare with the Southwest")
    text = _text(app)
    assert "Precipitation: the Midwest and the Southwest, 2005–2025" in text
    assert "does not test whether the two trends differ" in text
    assert len(app.metric) == 2
    assert len(app.get("plotly_chart")) == 2


def test_selection_is_preserved_and_short_period_suppresses_trend():
    app = _click(_start(), "Choose a region")
    app.selectbox[0].select("southwest").run()
    app.selectbox[1].select("soilmoisture").run()
    app.slider[0].set_value((2018, 2025)).run()
    assert not app.exception
    app = _click(app, "Investigate")

    text = _text(app)
    assert "Soil moisture (top 10 cm) in the Southwest, 2018–2025" in text
    assert "There is not enough usable data to estimate a reliable trend" in text
    assert len(app.metric) == 0, "no trend numbers when the analysis is not ok"
    assert "Provisional trend" not in text

    # Going back keeps the selection.
    app = _click(app, "Change selection")
    assert app.selectbox[0].value == "southwest"
    assert app.selectbox[1].value == "soilmoisture"
    assert app.slider[0].value == (2018, 2025)

    # Reset restores the full period for this variable.
    app = _click(app, "Reset to the full period")
    assert app.slider[0].value == (2000, 2025)


def test_switching_variable_keeps_period_inside_available_years():
    app = _click(_start(), "Choose a region")
    app.selectbox[1].select("soilmoisture").run()
    app.slider[0].set_value((2000, 2010)).run()
    app.selectbox[1].select("precip").run()
    assert not app.exception
    assert app.slider[0].value == (2005, 2010)


def test_start_over_returns_to_landing():
    app = _click(_start(), "Explore the Midwest example")
    app = _click(app, "Start over")
    assert app.title[0].value == "Explore how a place has changed"
