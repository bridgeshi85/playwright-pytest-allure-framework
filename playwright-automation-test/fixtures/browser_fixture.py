import pytest
import logging
from playwright.sync_api import sync_playwright
from fixtures.report_fixture import save_screenshot

logger = logging.getLogger(__name__)


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
