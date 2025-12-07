import pytest
import logging
from playwright.sync_api import sync_playwright
from fixtures.report_fixture import save_screenshot

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser():
    """
    启动并提供一个浏览器实例，测试结束后关闭浏览器。
    作用域为 session，整个测试会话中只启动一次浏览器
    """
    logger.info("start test")
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    yield browser
    logger.info("close the browser")
    browser.close()


@pytest.fixture
def page(browser, test_directory, request):
    """
    创建一个新的浏览器页面。
    - 依赖 browser 和 test_directory fixture。
    - 测试失败时自动截图并保存到 test_directory。
    :param browser: 浏览器对象 fixture
    :param test_directory: 测试结果目录 - 来自于 report_fixture.py
    :param request: pytest 请求对象
    """
    page = browser.new_page()

    def capture_final_screenshot():
        # 检查测试是否失败，若失败则截图
        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            logger.info("test failed")
            save_screenshot(page, test_directory, filename="failed-screenshot.png")
        page.close()

    # 测试结束后自动执行截图和关闭页面
    request.addfinalizer(capture_final_screenshot)

    yield page
