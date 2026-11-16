from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

LOADING_URL = (
    Path(__file__).resolve().parents[1] / "app" / "templates" / "loading.html"
).as_uri()

class LoadingPage:
    def __init(self, page: Page) -> None:
        self.page = page
        self.loader = page.locator(".loader")
        self.footer = page.locator("footer")

    def open(self) -> None:
        self.page.goto(LOADING_URL)

