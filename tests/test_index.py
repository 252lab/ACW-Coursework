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
        self.start_time_tab = page.get_by_role("button", name="Start Time")
        self.map = page.locator("iframe")
        self.error_message = page.locator("#error-message")
        self.error_text = page.locator("#error-text")

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


def test_time_tabs_and_map_are_present(homepage: Homepage) -> None:
    '''
    Test that the time tabs and map are present on the homepage.
    '''
    expect(homepage.start_time_tab).to_be_visible()
    expect(homepage.map).to_have_count(1)

# TEST CASES FOR VALIDATION OF FORM INPUTS 

# Location input boxes cannot be empty

def test_start_location_cannot_be_empty(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the start location input box to be empty.
    '''
    homepage.start_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    # note: the id of the error message is "error-text", however, this test is still failing
    expect(homepage.error_text).to_have_text("Please fill in this field.")

def test_adding_start_location_clears_error_message(homepage: Homepage) -> None:
    '''
    Test that adding a start location clears the error message for an empty start location input box.
    '''
    homepage.start_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    expect(homepage.error_text).to_have_text("Please fill in this field.")

    # add a start location
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be no error message displayed for empty start location
    expect(homepage.error_message).to_be_hidden()

def test_if_no_times_specified_start_time_is_set_to_current_time(homepage: Homepage) -> None:
    '''
    Test that if no start time or end time is specified, the start time is set to the current time.
    '''
    expected_time = homepage.page.evaluate("""() => {
        const now = new Date();
        return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    }""")

    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    expect(homepage.start_time).to_have_value("")
    expect(homepage.end_time).to_have_value("")
    homepage.submit_button.click()
    expect(homepage.error_message).to_be_hidden()
    expect(homepage.start_time).to_have_value(expected_time)


# test that whitespace is stripped from the station inputs (e.g. "  Oxford Circus  " should be treated as "Oxford Circus")

def test_valid_start_station_with_whitespace(homepage: Homepage) -> None:
    '''
    Test that the form allows a valid start station to be specified.
    '''
    homepage.start_location.fill("  Oxford Circus  ")  # valid station with whitespace
    homepage.end_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be no error message displayed for a valid start station
    expect(homepage.error_message).to_be_hidden()

def test_valid_end_station_with_whitespace(homepage: Homepage) -> None:
    '''
    Test that the form allows a valid end station to be specified.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("  Oxford Circus  ")  # valid station with whitespace
    homepage.submit_button.click()
    # there should be no error message displayed for a valid end station
    expect(homepage.error_message).to_be_hidden()
