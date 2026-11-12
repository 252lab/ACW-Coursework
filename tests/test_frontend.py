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
    expect(homepage.page.locator("#error-message")).to_have_count(0)

def test_same_start_and_end_locations(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the same start and end locations.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be an error message displayed for same start and end locations
    expect(homepage.page.locator("#error-message")).to_have_text("Start and end locations cannot be the same.") # placeholder error message text

def test_error_is_cleared_when_locations_are_changed(homepage: Homepage) -> None:
    '''
    Test that the error message is cleared when the start and end locations are changed to different values.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be an error message displayed for same start and end locations
    expect(homepage.page.locator("#error-message")).to_have_text("Start and end locations cannot be the same.") # placeholder error message text

    # change the end location to a different value
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be no error message displayed for different start and end locations
    expect(homepage.page.locator("#error-message")).to_have_count(0)

# Location input boxes cannot be empty

def test_start_location_cannot_be_empty(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the start location input box to be empty.
    '''
    homepage.start_location.fill("")
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    expect(homepage.page.locator("#error-message")).to_have_text("Start location cannot be empty.") # placeholder error message text

def test_end_location_cannot_be_empty(homepage: Homepage) -> None:
    '''
    Test that the form does not allow the end location input box to be empty.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty end location
    expect(homepage.page.locator("#error-message")).to_have_text("End location cannot be empty.") # placeholder error message text

def adding_start_location_clears_error_message(homepage: Homepage) -> None: 
    '''
    Test that adding a start location clears the error message for an empty start location input box.
    '''
    homepage.start_location.fill("")
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be an error message displayed for empty start location
    expect(homepage.page.locator("#error-message")).to_have_text("Start location cannot be empty.") # placeholder error message text

    # add a start location
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.submit_button.click()
    # there should be no error message displayed for empty start location
    expect(homepage.page.locator("#error-message")).to_have_count(0)

def adding_end_location_clears_error_message(homepage: Homepage) -> None:
    '''
    Test that adding an end location clears the error message for an empty end location input box.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("")
    homepage.submit_button.click()
    # there should be an error message displayed for empty end location
    expect(homepage.page.locator("#error-message")).to_have_text("End location cannot be empty.") # placeholder error message text

    # add an end location
    homepage.end_location.fill("Oxford Circus")
    homepage.submit_button.click()
    # there should be no error message displayed for empty end location
    expect(homepage.page.locator("#error-message")).to_have_count(0)

# The user cannot specify both a start time and an end time; they must choose one or the other.

def test_start_time_and_no_end_time_is_valid(homepage: Homepage) -> None:
    '''
    Test that the form allows a start time to be specified without an end time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.start_time.fill("08:00")
    homepage.submit_button.click()
    # there should be no error message displayed for specifying a start time without an end time
    expect(homepage.page.locator("#error-message")).to_have_count(0)

def test_end_time_and_no_start_time_is_valid(homepage: Homepage) -> None:
    '''
    Test that the form allows an end time to be specified without a start time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.end_time.fill("09:00")
    homepage.submit_button.click()
    # there should be no error message displayed for specifying an end time without a start time
    expect(homepage.page.locator("#error-message")).to_have_count(0)

def test_both_start_time_and_end_time_is_invalid(homepage: Homepage) -> None:
    '''
    Test that the form does not allow both a start time and an end time to be specified.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.start_time.fill("08:00")
    homepage.end_time.fill("09:00")
    homepage.submit_button.click()
    # there should be an error message displayed for specifying both a start time and an end time
    expect(homepage.page.locator("#error-message")).to_have_text("Cannot specify both a start time and an end time.") # placeholder error message text

# Specifying an invalid start time or end time should be automatically edited to a valid time.

def test_invalid_start_time_is_edited_to_valid_time(homepage: Homepage) -> None:
    '''
    Test that specifying an invalid start time is automatically edited to a valid time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.start_time.fill("25:00")  # invalid time
    homepage.submit_button.click()
    # the start time should be automatically edited to any valid time between 00:00 and 23:59
    # TODO: double check that this is the intended logic! 
    # this is the logic automatically provided by the HTML input type="time" element, but it may not be the intended logic for  our project!
    expect(homepage.start_time).to_have_value(lambda value: value >= "00:00" and value <= "23:59")

def test_invalid_end_time_is_edited_to_valid_time(homepage: Homepage) -> None:
    '''
    Test that specifying an invalid end time is automatically edited to a valid time.
    '''
    homepage.start_location.fill("King’s Cross St. Pancras")
    homepage.end_location.fill("Oxford Circus")
    homepage.end_time.fill("25:00")  # invalid time
    homepage.submit_button.click()
    # the end time should be automatically edited to any valid time between 00:00 and 23:59
    # TODO: double check that this is the intended logic! 
    # this is the logic automatically provided by the HTML input type="time" element, but it may not be the intended logic for  our project!
    expect(homepage.end_time).to_have_value(lambda value: value >= "00:00" and value <= "23:59")



# todo list of things to test:
# specifying an invalid end time should be automatically edited to a valid time
# specifying an invalid start and end time should be automatically edited to valid times, however there should be an error message displayed as BOTH times were specified 
# test that the user's station inputs are valid stations on the London Underground network (i.e. they exist in the tube_stations.json file)
# test that whitespace is stripped from the station inputs (e.g. "  Oxford Circus  " should be treated as "Oxford Circus")
