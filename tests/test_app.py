"""Runs the app headlessly and checks the globe screen and what it is sent."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from services import catalog, copy
from ui import globe, theme

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")
COMPONENT = ROOT / "ui" / "globe_component"

VARIABLES = ["precip", "evap", "soilmoisture", "runoff"]


@pytest.fixture(scope="module")
def payload() -> dict:
    return globe.build_payload()


def _page_html() -> str:
    return (COMPONENT / "index.html").read_text(encoding="utf-8")


# --- The page ----------------------------------------------------------------


def test_app_is_one_full_screen_globe_with_no_streamlit_widgets():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception

    # Start, the tick boxes, the charts switch and close all live inside the
    # globe component; Streamlit itself adds no buttons or text.
    for kind in ("button", "title", "header", "subheader", "caption", "markdown", "selectbox",
                 "radio", "slider", "toggle", "checkbox", "metric", "info", "error"):
        assert len(getattr(app, kind)) == 0, kind

    styles = [block.value for block in app.html]
    assert len(styles) == 1
    css = styles[0]
    assert css.startswith("<style>") and css.endswith("</style>")
    assert f".st-key-{globe.STAGE_KEY} iframe" in css
    assert "position: fixed" in css and "100vw" in css and "100dvh" in css
    assert '[data-testid="stHeader"]' in css and "footer" in css


def test_theme_options_are_set_in_the_config_file_not_in_css():
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert f'backgroundColor = "{theme.BACKGROUND}"' in config
    # Quoted strings: Streamlit ignores unquoted numbers for these options.
    assert 'paddingTop = "0"' in config and 'paddingBottom = "0"' in config
    assert "block-container" not in theme._FULLSCREEN


# --- Regions -----------------------------------------------------------------


def test_globe_regions_match_the_data_boxes_in_tour_order():
    regions = globe.globe_regions()
    assert [r["id"] for r in regions] == ["southwest", "midwest"]
    assert [r["letter"] for r in regions] == ["A", "B"]
    assert [r["label"] for r in regions] == ["Southwest", "Midwest"]
    southwest, midwest = regions
    assert [southwest[k] for k in ("west", "south", "east", "north")] == [-115, 31, -106, 40]
    assert [midwest[k] for k in ("west", "south", "east", "north")] == [-93, 40, -76, 49]


def test_a_region_without_saved_data_is_not_offered(tmp_path, monkeypatch):
    source = catalog.discover()[("midwest", "precip")]
    (tmp_path / source.name).write_bytes(source.read_bytes())
    monkeypatch.setattr(catalog, "DATA_DIR", tmp_path)
    assert [r["id"] for r in globe.globe_regions()] == ["midwest"]


# --- What the globe is sent --------------------------------------------------


def test_payload_covers_every_region_and_variable(payload):
    assert [v["id"] for v in payload["variables"]] == VARIABLES
    assert [v["short"] for v in payload["variables"]] == [
        "Precipitation", "Evaporation", "Soil moisture", "Runoff",
    ]
    assert set(payload["results"]) == {"southwest", "midwest"}
    for region in payload["results"].values():
        assert list(region) == VARIABLES
    assert (payload["first_year"], payload["last_year"]) == (2000, 2025)
    assert payload["provisional"] is True
    json.dumps(payload)   # everything can be sent to the browser


def test_each_variable_uses_all_the_years_its_file_covers(payload):
    for region in payload["results"].values():
        assert region["precip"]["period"] == "2005–2025"
        assert region["soilmoisture"]["period"] == "2000–2025"
        assert len(region["precip"]["monthly"]["v"]) == 252
        assert len(region["soilmoisture"]["monthly"]["v"]) == 312
        assert region["soilmoisture"]["annual"]["years"] == list(range(2000, 2026))


def test_colour_follows_the_confidence_interval(payload):
    """A trend is coloured as a rise or fall only if its interval excludes zero."""
    for region_id, region in payload["results"].items():
        for variable_id, result in region.items():
            low, high = (
                float(part) for part in result["interval_text"].replace("−", "-").split(" to ")
            )
            trend = float(result["trend_text"].replace("−", "-"))
            if low <= 0 <= high:
                expected, badge = "inconclusive", "Inconclusive"
            else:
                expected, badge = ("increase" if trend > 0 else "decrease"), "Significant"
            assert result["direction"] == expected, (region_id, variable_id)
            assert result["badge"] == badge, (region_id, variable_id)


def test_directions_of_the_delivered_data(payload):
    for region in payload["results"].values():
        for variable_id, result in region.items():
            expected = "decrease" if variable_id == "soilmoisture" else "inconclusive"
            assert result["direction"] == expected


def test_labels_carry_value_unit_and_uncertainty_wording(payload):
    result = payload["results"]["midwest"]["precip"]
    assert re.fullmatch(r"[+-]\d+\.\d+", result["trend_text"])
    assert result["trend_unit"] == "mm/day per decade"
    assert result["trend_unit_short"] == "mm/day/decade"
    assert result["uncertainty"].startswith("The 95% confidence interval for the trend is ")
    assert result["uncertainty"].endswith("under the analysis assumptions.")
    assert result["conclusion"] == (
        "This analysis does not clearly distinguish an upward or downward "
        "long-term trend from variability over this period."
    )
    assert result["badge_note"] == (
        "Inconclusive: the 95% confidence interval includes zero, so no direction is shown."
    )

    significant = payload["results"]["midwest"]["soilmoisture"]
    assert "consistent with a downward long-term trend" in significant["conclusion"]
    assert "It is not a prediction" in significant["conclusion"]
    assert significant["badge_note"].startswith("Statistically significant: the 95%")


def test_panel_gives_a_plain_headline_and_says_what_each_variable_is(payload):
    for region in payload["results"].values():
        for variable_id, result in region.items():
            expected = "Downward trend" if variable_id == "soilmoisture" else "No clear trend"
            assert result["headline"] == expected
            # Not significant must never be worded as "no change".
            assert "no change" not in result["headline"].lower()
            assert result["definition"] == catalog.VARIABLES[variable_id].definition


def test_chart_series_are_complete_and_the_band_contains_the_fit(payload):
    for region in payload["results"].values():
        for result in region.values():
            annual = result["annual"]
            count = len(annual["years"])
            assert count >= 10
            assert [len(annual[k]) for k in ("mean", "fit", "lo", "hi")] == [count] * 4
            for low, fit, high in zip(annual["lo"], annual["fit"], annual["hi"]):
                assert low <= fit <= high
            assert result["band_label"] == "95% confidence band for the fitted trend"
            assert len(result["monthly"]["t"]) == len(result["monthly"]["v"])
            assert result["source_url"].startswith("https://giovanni.gsfc.nasa.gov/")
            assert [fact[0] for fact in result["facts"]] == [
                "Dataset", "Coverage", "Source grid", "Months used", "Method", "Aggregation",
            ]


def test_payload_text_comes_from_the_copy_module(payload):
    text = payload["text"]
    assert text["directions"] == copy.DIRECTION_LABELS
    assert text["provisional_tag"] == "Provisional"
    assert text["provisional_notice"] == copy.PROVISIONAL_NOTICE
    assert text["uncertainty_guide"] == copy.UNCERTAINTY_GUIDE
    assert text["chart_guide"] == copy.CHART_GUIDE
    assert text["color_key"] == "Color key"
    assert text["stripes"].startswith("Each stripe is one year, 2000 to 2025")
    assert "darker means a lower yearly average" in text["stripes"]
    # Precipitation and evaporation start in 2005, so the key explains the gap.
    assert text["stripes"].endswith("A blank start means that record begins later.")
    assert text["faded_key"] == "Faded: inconclusive"


# --- The component files -----------------------------------------------------


def test_component_has_only_start_ticks_details_switch_and_close():
    html = _page_html()
    body = html[html.index("<body"):html.index("<script")]
    assert re.findall(r'<button[^>]*id="([^"]+)"', body) == ["start", "close"]
    assert re.findall(r'<input[^>]*id="([^"]+)"', body) == ["detailsToggle"]
    assert ">Start</button>" in body
    assert "Charts &amp; details" in body


def test_start_page_shows_the_app_title():
    html = _page_html()
    assert f'<h1 id="title">{copy.APP_TITLE}</h1>' in html
    # Shown with the Start button only: it fades out when the tour begins.
    assert "body.idle.ready #title" in html


def test_color_key_is_drawn_with_the_colors_of_the_stripes():
    html = _page_html()
    # Stripes and key both take their colors from shade().
    assert "shade(v, result.direction, t)" in html
    assert "return shade(v, direction, t); });" in html
    # One ramp per variable, plus a faded sample for inconclusive results.
    assert 'rampCss(v.id, "increase")' in html
    assert 'rampCss(P.variables[0].id, "inconclusive")' in html


def test_color_names_the_variable_and_inconclusive_results_are_faded():
    html = _page_html()
    for variable_id in VARIABLES:
        assert re.search(rf"\b{variable_id}: \[\d+, \d+, \d+, \d+\]", html), variable_id
    # Full color needs a direction, and a direction needs an interval that
    # excludes zero (services/copy.trend_direction).
    assert 'var clear = direction === "increase" || direction === "decrease";' in html
    assert "c[1] * (clear ? 1 : FADED)" in html


def test_region_clusters_light_up_and_lead_to_the_charts():
    html = _page_html()
    # Hub: every wire and block. Block: itself, its wire and the hub.
    assert 'setHot(el, node.classList.contains("hub") ? "*" : node.getAttribute("data-v"));' in html
    # A block opens the panel and glides to its own card.
    assert 'openPanel(g.id, node.classList.contains("hub") ? null : node.getAttribute("data-v"));' in html
    assert "glideTo(pbody, top);" in html
    # The glide gives way to the visitor at once, and is skipped for reduced motion.
    assert '["wheel", "touchstart", "pointerdown", "keydown"]' in html
    assert "if (reduceMotion || Math.abs(top - from) < 2) { el.scrollTop = top; return; }" in html
    # Blocks are 20% see-through and hubs 60%.
    assert "text-align: left; opacity: 0.8;" in html
    assert "background: rgba(8, 46, 30, 0.40);" in html
    assert (COMPONENT / "archivo-black-latin.woff2").stat().st_size > 10_000


def test_charts_panel_takes_two_fifths_of_a_laptop_window():
    assert "--panel-w: clamp(380px, 40vw, 820px);" in _page_html()


def test_component_loads_nothing_from_another_server():
    html = _page_html()
    sources = re.findall(r'(?:src|href)="([^"]+)"', html)
    assert "globe.gl.min.js" in sources
    assert not [s for s in sources if s.startswith(("http:", "https:", "//"))]
    for name in ("globe.gl.min.js", "earth-2k.jpg", "earth-blue-marble.jpg"):
        assert (COMPONENT / name).stat().st_size > 100_000, name
    # The picture loaded first is small enough for a phone connection.
    assert (COMPONENT / "earth-2k.jpg").stat().st_size < 400_000


def test_component_has_no_leftover_debug_hooks():
    html = _page_html()
    assert "__dbg" not in html and "TEMP" not in html and "console.log" not in html
    assert not (COMPONENT / "_payload.json").exists()
