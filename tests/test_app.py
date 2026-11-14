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
    for kind in ("title", "header", "subheader", "markdown", "caption", "info", "warning", "error"):
        parts += [element.value for element in getattr(app, kind)]
    return "\n".join(parts)


LIST_BUTTON = "Choose a region from a list instead"


def _open_midwest() -> AppTest:
    """Default investigation (Midwest precipitation) via the list route."""
    return _click(_click(_start(), LIST_BUTTON), "Investigate")


def test_landing():
    app = _start()
    assert app.title[0].value == "Explore how a place has changed"
    assert [b.label for b in app.button] == [LIST_BUTTON]


def test_globe_regions_match_the_data_boxes():
    from services import catalog
    from ui import globe

    regions = {r["id"]: r for r in globe.globe_regions(catalog.region_ids())}
    assert set(regions) == {"midwest", "southwest"}
    assert [regions["midwest"][k] for k in ("west", "south", "east", "north")] == [-93, 40, -76, 49]
    assert [regions["southwest"][k] for k in ("west", "south", "east", "north")] == [-115, 31, -106, 40]
    assert regions["midwest"]["label"] == "US Midwest"
    # A region without saved data is not offered.
    assert globe.globe_regions(["midwest"])[0]["id"] == "midwest"
    assert len(globe.globe_regions(["midwest"])) == 1


def test_results_panel_shows_result_chart_and_provisional_notice():
    app = _open_midwest()
    text = _text(app)
    assert "MIDWEST REGION  ·  2005–2025" in text
    assert [s.value for s in app.subheader] == ["Precipitation"]
    assert "has an estimated trend of" in text
    assert "The 95% confidence interval for the trend is" in text
    assert "Provisional trend" in text
    assert "not measurements at a single place" in text
    assert len(app.metric) == 2
    assert len(app.get("plotly_chart")) == 1
    assert len(app.get("download_button")) == 2


def test_every_chart_type_renders_with_a_description():
    app = _open_midwest()
    options = app.radio(key="r_chart").options
    assert options == ["Trend line", "Yearly bars", "Histogram", "Seasonal pattern"]
    for option in options:
        app.radio(key="r_chart").set_value(option).run()
        assert not app.exception, (option, app.exception)
        assert len(app.get("plotly_chart")) == 1
        assert "**What the chart shows.**" in _text(app)
        # The result itself does not change with the chart type.
        assert len(app.metric) == 2


def test_chart_type_survives_leaving_and_returning():
    app = _open_midwest()
    app.radio(key="r_chart").set_value("Histogram").run()
    app = _click(app, "Inspect method and sources")
    app = _click(app, "Back to the result")
    assert app.radio(key="r_chart").value == "Histogram"


def test_evidence_and_back():
    app = _open_midwest()
    app = _click(app, "Inspect method and sources")
    text = _text(app)
    assert "Inspect the evidence" in text
    assert "MERRA-2" in text and "5.12.4" in text
    assert "Ordinary least squares" in text
    app = _click(app, "Back to the result")
    assert "MIDWEST REGION  ·  2005–2025" in _text(app)


def test_compare_view():
    app = _open_midwest()
    app = _click(app, "Compare with the Southwest")
    text = _text(app)
    assert "Precipitation: the Midwest and the Southwest, 2005–2025" in text
    assert "does not test whether the two trends differ" in text
    assert len(app.metric) == 2
    # The data chart plus the region map.
    assert len(app.get("plotly_chart")) == 2


def test_panel_controls_change_the_result_and_survive_navigation():
    app = _open_midwest()
    app.selectbox(key="r_region").select("southwest").run()
    app.selectbox(key="r_variable").select("soilmoisture").run()
    app.slider(key="r_period").set_value((2018, 2025)).run()
    assert not app.exception

    text = _text(app)
    assert "SOUTHWEST REGION  ·  2018–2025" in text
    assert [s.value for s in app.subheader] == ["Soil moisture (top 10 cm)"]
    assert "There is not enough usable data to estimate a reliable trend" in text
    assert len(app.metric) == 0, "no trend numbers when the analysis is not ok"
    assert "Provisional trend" not in text
    assert app.radio(key="r_chart").options == ["Monthly values", "Histogram", "Seasonal pattern"]

    # Leaving and returning keeps the selection.
    app = _click(app, "Inspect method and sources")
    app = _click(app, "Back to the result")
    assert app.selectbox(key="r_region").value == "southwest"
    assert app.selectbox(key="r_variable").value == "soilmoisture"
    assert app.slider(key="r_period").value == (2018, 2025)

    # "Full period" restores every available year, and the trend returns.
    app = _click(app, "Full period")
    assert app.slider(key="r_period").value == (2000, 2025)
    assert len(app.metric) == 2


def test_switching_variable_in_the_panel_keeps_period_inside_available_years():
    app = _open_midwest()
    app.selectbox(key="r_variable").select("soilmoisture").run()
    app.slider(key="r_period").set_value((2000, 2010)).run()
    app.selectbox(key="r_variable").select("precip").run()
    assert not app.exception
    assert app.slider(key="r_period").value == (2005, 2010)
    assert "MIDWEST REGION  ·  2005–2010" in _text(app)


def test_forecast_button_explains_the_plan_and_predicts_nothing():
    app = _open_midwest()
    before = [metric.value for metric in app.metric]
    app = _click(app, "Forecast (coming soon)")
    notes = [info.value for info in app.info if "Forecasting is planned" in info.value]
    assert len(notes) == 1
    assert "Nothing is predicted here today" in notes[0]
    assert [metric.value for metric in app.metric] == before
    app = _click(app, "Forecast (coming soon)")
    assert not any("Forecasting is planned" in info.value for info in app.info)


def test_dark_mode_applies_to_the_data_panel_only_when_switched_on():
    app = _open_midwest()

    def panel_is_dark() -> bool:
        return any("invert(0.92)" in block.value for block in app.markdown)

    assert not panel_is_dark()
    app.toggle(key="r_dark").set_value(True).run()
    assert not app.exception
    assert panel_is_dark()
    # The preference survives "Start over".
    app = _click(app, "Start over")
    app = _click(_click(app, LIST_BUTTON), "Investigate")
    assert app.toggle(key="r_dark").value is True


def test_selection_screen_keeps_period_inside_available_years():
    app = _click(_start(), LIST_BUTTON)
    app.selectbox[1].select("soilmoisture").run()
    app.slider[0].set_value((2000, 2010)).run()
    app.selectbox[1].select("precip").run()
    assert not app.exception
    assert app.slider[0].value == (2005, 2010)


def test_start_over_returns_to_landing():
    app = _open_midwest()
    app = _click(app, "Start over")
    assert app.title[0].value == "Explore how a place has changed"
