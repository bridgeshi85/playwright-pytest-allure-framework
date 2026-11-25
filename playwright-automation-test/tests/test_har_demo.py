"""Focused examples for recording and replaying an API HAR snapshot."""

from pathlib import Path

import allure
from playwright.sync_api import BrowserContext, expect

from fixtures.report_fixture import save_screenshot
from pages.har_demo_page import HarDemoPage


@allure.feature("Network mocking")
@allure.story("HAR Record and Replay")
@allure.title("Verify HAR demo API snapshot")
def test_har_demo_flow(
    har_context: BrowserContext,
    config: dict[str, object],
    test_directory: Path,
) -> None:
    """
    单用例设计：UI 操作只写一遍。
    本地运行时执行 RECORD_HAR=1 pytest ... 更新快照；CI 中默认离线回放。
    """
    # Arrange
    page = har_context.new_page()
    har_demo = HarDemoPage(page)

    # Act
    print(f"Base URL: {config['base_url']}")
    har_demo.goto(str(config["base_url"]))
    
    # Assert
    expect(har_demo.success_panel).to_be_visible()
    expect(har_demo.profile_value).to_have_text("Demo User")
    expect(har_demo.permission_value).to_have_text("dashboard:read")
    expect(har_demo.metrics_value).to_have_text("3")

    screenshot_path = save_screenshot(page, test_directory, "har-replay")
    allure.attach.file(
        str(screenshot_path),
        name="HAR replay result",
        attachment_type=allure.attachment_type.PNG,
    )
