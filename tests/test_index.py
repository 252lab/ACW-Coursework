from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

INDEX_URL = (
    Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html"
).as_uri()

class Homepage:
    '''
    This class creates a representation of the Loading page, so that the tests use the Page Object Model.
    '''
    def __init__(self, page: Page) -> None:
        self.page = page
        self.heading = page.locator("h1")
        self.start_location = page.locator("#startLocation")
        self.end_location = page.locator("#endLocation")
        self.start_time = page.locator("#startTime")
        self.submit_button = page.locator('input[type="submit"]')
        self.map = page.locator("iframe")

    def open(self) -> None:
        self.page.goto(INDEX_URL)


@pytest.fixture
def homepage(request):
    playwright = sync_playwright().start()
    request.addfinalizer(playwright.stop)

    browser = playwright.chromium.launch()
    request.addfinalizer(browser.close)

    page = Homepage(browser.new_page())
    page.open()
    return page

@pytest.mark.smoke
def test_homepage_heading_is_visible(homepage: Homepage) -> None:
    '''
    Test that the homepage heading is visible and has the correct text.
    '''
    expect(homepage.heading).to_have_text("London Tube Route Planner")


@pytest.mark.smoke
def test_route_form_fields_are_present(homepage: Homepage) -> None:
    '''
    Test that the route form fields are present on the homepage.
    '''
    for field in (
        homepage.start_location,
        homepage.end_location,
        homepage.start_time,
    ):
        expect(field).to_have_count(1)

    expect(homepage.submit_button).to_be_visible()


def test_start_time_input_and_map_are_present(homepage: Homepage) -> None:
    '''
    Test that the start-time input and map are present on the homepage.
    '''
    expect(homepage.page.get_by_label("Start Time:")).to_be_visible()
    expect(homepage.start_time).to_have_attribute("type", "time")
    expect(homepage.map).to_have_count(1)

def test_station_fields_use_native_required_validation(homepage: Homepage) -> None:
    """Both station fields are marked required in the form."""
    for field in (homepage.start_location, homepage.end_location):
        expect(field).to_have_attribute("required", "")
        assert field.evaluate("element => element.checkValidity()") is False

    homepage.start_location.fill("Oxford Circus")
    assert homepage.start_location.evaluate("element => element.checkValidity()") is True
    assert homepage.end_location.evaluate("element => element.checkValidity()") is False


def test_start_time_is_optional(homepage: Homepage) -> None:
    """The start-time field is not marked required."""
    expect(homepage.start_time).not_to_have_attribute("required", "")
    assert homepage.start_time.evaluate("element => element.checkValidity()") is True
