import pytest
import logging

from playwright.sync_api import ViewportSize
from playwright.sync_api import sync_playwright
from fixtures.report_fixture import save_screenshot, test_directory


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

    :returns: A tuple of (context, trace_dir) where trace_dir is where trace.zip will be saved.
    :rtype: tuple[playwright.sync_api.BrowserContext, pathlib.Path]
    """
    # Place videos alongside screenshots under the unified output root.
    # test_directory is output/screenshots/<run-id>
    output_root = test_directory.parent.parent
    video_dir = output_root / "videos" / test_directory.name
    video_dir.mkdir(parents=True, exist_ok=True)

    # Traces directory: output/traces/<run-id>
    trace_dir = output_root / "traces" / test_directory.name
    trace_dir.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(
        ignore_https_errors=True,
        accept_downloads=True,
        record_video_dir=str(video_dir),
        viewport=ViewportSize({"width": 1920, "height": 1080}),
        locale=locale,
    )
    # Start tracing: captures screenshots, snapshots and sources for each action
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    return context, trace_dir


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
    logger.debug("close the browser")
    browser.close()
    playwright.stop()


@pytest.fixture
def page(browser, test_directory, request):
    """
    创建一个新的浏览器页面。
    - 依赖 browser 和 test_directory fixture。
    - 测试失败时自动截图并保存到 test_directory，并保存 trace.zip。
    - 测试结束后自动保存视频。
    :param browser: 浏览器对象 fixture
    :param test_directory: 测试结果目录 - 来自于 report_fixture.py
    :param request: pytest 请求对象
    """
    context, trace_dir = create_context(browser, test_directory)
    page = context.new_page()

    yield page

    # 判断测试是否失败
    test_failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False

    # 保存 trace.zip（仅在失败时，以节省磁盘空间；如需每次都保存可去掉条件）
    trace_path = trace_dir / f"{request.node.name}.zip"
    if test_failed:
        logger.debug(f"Test failed – saving trace to {trace_path}")
        context.tracing.stop(path=str(trace_path))
        request.node._trace_path = str(trace_path)
        # Attach trace to Allure report
        try:
            import allure
            allure.attach.file(
                str(trace_path),
                name="Playwright Trace",
                attachment_type=allure.attachment_type.ZIP,
            )
        except Exception as e:
            logger.warning(f"Could not attach trace to Allure: {e}")
    else:
        context.tracing.stop()  # Stop without saving

    # 获取video并保存路径到request.node，供后续allure报告使用
    if page.video:
        logger.debug("save video path to request.node")
        request.node._video_path = page.video.path()

    logger.debug("close the page")
    page.close()
    context.close()
