from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

ROUTE_URL = (
        Path(__file__).resolve().parents[1] / "app" / "templates" / "route.html"
).as_uri()

class RoutePage:
    '''
    This class creates a representation of he Route page, so that the tests use the Page Object Model.
    '''
    def __init__(self, page: Page) -> None:
        self.page = page
        self.heading = page.locator("h1")
        self.route_text = page.locator("p")
        self.map = page.locator("iframe")

    def open(self) -> None:
        self.page.goto(ROUTE_URL)

@pytest.fixture
def route_page():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch()
    page = RoutePage(browser.new_page())
    page.open()
    yield page
    browser.close()
    playwright.stop()

@pytest.mark.smoke
def test_route_page_heading_is_visible(route_page: RoutePage) -> None:
    expect(route_page.heading).to_have_text("Your Route")

@pytest.mark.smoke
def test_route_page_has_route_text(route_page: RoutePage) -> None:
    expect(route_page.page.get_by_text("Your most optimal route is:")).to_be_visible()