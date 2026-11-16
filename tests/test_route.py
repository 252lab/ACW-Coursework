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