"""Dedicated browser contexts for explicit HAR recording and replay tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext


HAR_PATH = Path(__file__).resolve().parent.parent / "data" / "har" / "har_demo.har"
HAR_API_FILTER = "**/api/har-demo/**"


@pytest.fixture
def har_recording_context(browser: Browser) -> Iterator[BrowserContext]:
    """Create a context that writes complete, embedded HAR responses on close."""
    HAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        record_har_content="embed",
        record_har_mode="full",
        record_har_path=str(HAR_PATH),
        record_har_url_filter=HAR_API_FILTER,
    )
    yield context
    context.close()


@pytest.fixture
def har_replay_context(browser: Browser) -> Iterator[BrowserContext]:
    """Create an isolated context for replaying the reviewed HAR snapshot."""
    context = browser.new_context()
    yield context
    context.close()
