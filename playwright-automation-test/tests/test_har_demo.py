"""Focused examples for recording and replaying an API HAR snapshot."""

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from fixtures.har_fixture import HAR_PATH
from pages.har_demo_page import HarDemoPage


API_URL_FILTER = "**/api/har-demo/**"


@allure.feature("Network mocking")
@allure.story("HAR recording")
@allure.title("Record the HAR demo API snapshot")
@pytest.mark.har_recording
def test_record_har_demo(
    har_recording_context: BrowserContext, config: dict[str, object]
) -> None:
    """Record all three deterministic API responses into the reviewed HAR."""
    # Arrange
    page = har_recording_context.new_page()
    har_demo = HarDemoPage(page)

    # Act
    har_demo.goto(str(config["base_url"]))

    # Assert
    expect(har_demo.success_panel).to_be_visible()


@allure.feature("Network mocking")
@allure.story("HAR replay")
@allure.title("Replay the HAR demo while the API is unavailable")
def test_replay_har_demo(
    har_replay_context: BrowserContext, config: dict[str, object]
) -> None:
    """Render the complete demo page entirely from the reviewed HAR responses."""
    # Arrange
    har_replay_context.route_from_har(
        str(HAR_PATH),
        url=API_URL_FILTER,
        not_found="abort",
    )
    page = har_replay_context.new_page()
    har_demo = HarDemoPage(page)

    # Act
    har_demo.goto(str(config["base_url"]))

    # Assert
    expect(har_demo.success_panel).to_be_visible()
    expect(har_demo.profile_value).to_have_text("Ada Lovelace")
    expect(har_demo.permission_value).to_have_text("reports:read")
    expect(har_demo.metrics_value).to_have_text("12")
