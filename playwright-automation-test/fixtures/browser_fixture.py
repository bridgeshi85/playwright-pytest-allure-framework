import pytest
import logging

from playwright.sync_api import ViewportSize
from playwright.sync_api import sync_playwright
from fixtures.report_fixture import save_screenshot

logger = logging.getLogger(__name__)


def create_context(browser, test_directory, locale="en-US"):
    """
    Create a new browser context with specified configurations.

    :param browser: The Playwright browser instance used to create a new context.
    :type browser: playwright.sync_api.Browser
    :param test_directory: The base directory where test-related files, including videos, will be stored.
    :type test_directory: pathlib.Path
    :param locale: The locale to use in the context (e.g., 'en-US'). Defaults to 'en-US'.
    :type locale: str

    :returns: A new browser context configured with the provided settings.
    :rtype: playwright.sync_api.BrowserContext
    """
    video_dir = test_directory / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        ignore_https_errors=True,
        accept_downloads=True,
        record_video_dir=str(video_dir),
        viewport=ViewportSize({"width": 1920, "height": 1080}),
        locale=locale,
    )
    return context


@pytest.fixture(scope="session")
def browser(config):
    """
    :param config: 配置对象 fixture - 来自 conftest.py
    启动并提供一个浏览器实例，测试结束后关闭浏览器。
    默认浏览器为chrome , 默认headless 模式
    通过configs/env.xxx.yaml 文件配置浏览器类型和参数
    例如：
    browser: "chromium"  # 可选 "chromium", "firefox", "webkit"
    headless: true
    slowmo: 50
    """
    logger.info("start test session: launching browser")

    playwright = sync_playwright().start()

    browser_type = config.get("browser", "chromium")
    headless = config.get("headless", True)
    slowmo = config.get("slowmo", 0)

    launch_kwargs = {
        "headless": headless,
        "slow_mo": slowmo
    }

    logger.info(f"launch browser={browser_type}, headless={headless}, slowmo={slowmo}")

    # 根据 browser_type 动态选择浏览器
    browser = getattr(playwright, browser_type).launch(**launch_kwargs)

    yield browser
    logger.info("close the browser")
    browser.close()
    playwright.stop()


@pytest.fixture
def page(browser, test_directory, request):
    """
    创建一个新的浏览器页面。
    - 依赖 browser 和 test_directory fixture。
    - 测试失败时自动截图并保存到 test_directory。
    - 测试结束后自动保存视频。
    :param browser: 浏览器对象 fixture
    :param test_directory: 测试结果目录 - 来自于 report_fixture.py
    :param request: pytest 请求对象
    """
    context = create_context(browser, test_directory)
    page = context.new_page()

    yield page
    rep = getattr(request.node, "rep_call", None)
    logger.info("end test case: saving video and closing page")

    # 1️⃣ 测试失败时截图并保存
    if rep and rep.failed:
        save_screenshot(page, test_directory)

    # 2️⃣ 关闭页面和上下文
    logger.info("close the page")
    context.close()
    page.close()

