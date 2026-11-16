from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

INDEX_URL = (
    Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html"
).as_uri()

