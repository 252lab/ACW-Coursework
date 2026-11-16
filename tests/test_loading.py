from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

LOADING_URL = (
    Path(__file__).resolve().parents[1] / "app" / "templates" / "loading.html"
).as_uri()

class LoadingPage:
    '''
    This class creates a representation of the Loading page, so that the tests use the Page Object Model.
    '''
    def __init(self, page: Page) -> None:
        self.page = page
        self.loader = page.locator(".loader")
        self.footer = page.locator("footer")

    def open(self) -> None:
        self.page.goto(LOADING_URL)

@pytest.fixture
def loading_page():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch()
    page = LoadingPage(browser.new_page())
    page.open()
    yield page
    browser.close()
    playwright.stop()

@pytest.mark.smoke
def test_loading_page_loads(loading_page: LoadingPage) -> None:
    expect(loading_page.loader).to_be_visible()
    expect(loading_page.footer).to_be_visible()