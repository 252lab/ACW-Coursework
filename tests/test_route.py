from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

ROUTE_URL = (
        Path(__file__).resolve().parents[1] / "app" / "templates" / "route.html"
).as_uri()