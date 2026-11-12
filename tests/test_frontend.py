from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

INDEX_URL = (Path(__file__).resolve().parents[1] / "index.html").as_uri()


class Homepage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.heading = page.locator("h1")
        self.start_location = page.locator("#startLocation")
        self.end_location = page.locator("#endLocation")
        self.start_time = page.locator("#startTime")
        self.end_time = page.locator("#endTime")
        self.submit_button = page.locator('input[type="submit"]')
        self.start_time_tab = page.get_by_role("button", name="Start Time")
        self.end_time_tab = page.get_by_role("button", name="End Time")
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
        homepage.end_time,
    ):
        expect(field).to_have_count(1)

    expect(homepage.submit_button).to_be_visible()


def test_time_tabs_and_map_are_present(homepage: Homepage) -> None:
    '''
    Test that the time tabs and map are present on the homepage.
    '''
    expect(homepage.start_time_tab).to_be_visible()
    expect(homepage.end_time_tab).to_be_visible()
    expect(homepage.map).to_have_count(1)

# TEST CASES FOR VALIDATION OF FORM INPUTS 

# End location cannot equal start location 

def test_different_start_and_end_locations(homepage: Homepage) -> None:
    '''
    Test that the form  allows different start and end locations.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be no error message displayed for different start and end locations
    expect(homepage.error_message).to_be_hidden()

@pytest.mark.skip(reason="This test is currently failing as this feature has not been implemented yet.")
def test_same_start_and_end_locations(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the same start and end locations.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be an error message displayed for same start and end locations
    expect(homepage.error_text).to_have_text("Start and end locations cannot be the same.")
    expect(homepage.error_message).to_be_visible()

@pytest.mark.skip(reason="This test is currently failing as this feature has not been implemented yet.")
def test_error_is_cleared_when_locations_are_changed(homepage: Homepage) -> None:
    '''
    Test that the error message is cleared when the start and end locations are changed to different values.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be an error message displayed for same start and end locations
    expect(homepage.error_text).to_have_text("Start and end locations cannot be the same.")
    expect(homepage.error_message).to_be_visible()

    # change the end location to a different value
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be no error message displayed for different start and end locations
    expect(homepage.error_message).to_be_hidden()

# Location input boxes cannot be empty

@pytest.mark.skip(reason="Need to verify intended functionality.")
def test_start_location_cannot_be_empty(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the start location input box to be empty.
    '''
    homepage.start_location.fill("")
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    # note: the id of the error message is "error-text", however, this test is still failing
    expect(homepage.error_text).to_have_text("Please fill in this field.")

@pytest.mark.skip(reason="Need to verify intended functionality.")
def test_end_location_cannot_be_empty(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the end location input box to be empty.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty end location
    expect(homepage.error_text).to_have_text("Please fill in this field.")

@pytest.mark.skip(reason="The page that should be displayed after submitting details hasn't been implemented yet.")
def test_adding_start_location_clears_error_message(homepage: Homepage) -> None:
    '''
    Test that adding a start location clears the error message for an empty start location input box.
    '''
    homepage.start_location.fill("")
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    expect(homepage.error_text).to_have_text("Please fill in this field.")

    # add a start location
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be no error message displayed for empty start location
    expect(homepage.error_message).to_be_hidden()

@pytest.mark.skip(reason="The page that should be displayed after submitting details hasn't been implemented yet.")
def test_adding_end_location_clears_error_message(homepage: Homepage) -> None:
    '''
    Test that adding an end location clears the error message for an empty end location input box.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty end location
    expect(homepage.error_text).to_have_text("Please fill in this field.")

    # add an end location
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be no error message displayed for empty end location
    expect(homepage.error_message).to_be_hidden()

# The user cannot specify both a start time and an end time; they must choose one or the other.

@pytest.mark.skip(reason="This functionality hasn't been implemented yet.")
def test_start_time_and_no_end_time_is_valid(homepage: Homepage) -> None:
    '''
    Test that the form allows a start time to be specified without an end time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.start_time_tab.click()
    homepage.start_time.fill("08:00")
    homepage.submit_button.click()
    # there should be no error message displayed for specifying a start time without an end time
    expect(homepage.page.locator("#error-text")).to_have_count(0)

@pytest.mark.skip(reason="This functionality hasn't been implemented yet.")
def test_end_time_and_no_start_time_is_valid(homepage: Homepage) -> None:
    '''
    Test that the form allows an end time to be specified without a start time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.end_time_tab.click()
    homepage.end_time.fill("09:00")
    homepage.submit_button.click()
    # there should be no error message displayed for specifying an end time without a start time
    expect(homepage.page.locator("#error-text")).to_have_count(0)

@pytest.mark.skip(reason="This functionality hasn't been implemented yet.")
def test_both_start_time_and_end_time_is_invalid(homepage: Homepage) -> None:
    '''
    Test that the form does not allow both a start time and an end time to be specified.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.start_time_tab.click()
    homepage.start_time.fill("08:00")
    homepage.end_time_tab.click()
    homepage.end_time.fill("09:00")
    homepage.submit_button.click()
    # there should be an error message displayed for specifying both a start time and an end time
    expect(homepage.error_text).to_have_text("Cannot specify both a start time and an end time.")
    expect(homepage.error_message).to_be_visible()


@pytest.mark.skip(reason="This functionality hasn't been implemented yet.")
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

# test that the user's station inputs are valid stations on the London Underground network
