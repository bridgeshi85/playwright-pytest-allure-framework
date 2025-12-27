import os
import pytest
import logging
import allure
from utils.config_loader import load_config
# Import fixtures to ensure they are registered
from fixtures.report_fixture import save_screenshot

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """
    添加命令行参数，用于指定环境配置名称
    通过命令行--env 参数传入，默认为 "default"
    例如：pytest --env=staging
    该参数在pytest.ini中添加了
    """
    parser.addoption(
        "--env",
        action="store",
        default="default",
        help="Environment config name"
    )


@pytest.fixture(scope="session")
def config(pytestconfig):
    """加载当前运行环境配置"""
    logger.info("load config")
    env = pytestconfig.getoption("--env") or "default"
    return load_config(env)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    测试结束时截图并保存页面源代码到目录test_results/日期-x 比如 test_results/2024-06-01-2
    并将其附加到 Allure 报告中
    生成的文件命名为 {测试用例名称}.png 和 {测试用例名称}.html
    例如：test_login.png, test_login.html
    该钩子函数使用 pytest 的钩子机制实现
    """
    outcome = yield
    rep = outcome.get_result()

    # 测试完成后执行
    if rep.when == "call":
        logger.info("Test finished, capturing screenshot and page source for Allure report")
        # 获取 page fixture
        page = item.funcargs.get("page", None)
        test_directory = item.funcargs.get("test_directory")

        if not page or not test_directory:
            logger.warning("No page or test_directory fixture found; cannot capture screenshot or page source")
            return

        # Attach screenshot to Allure report
        screenshot_path = save_screenshot(page, test_directory, item.name)
        allure.attach.file(
            str(screenshot_path),
            name="Screenshot",
            attachment_type=allure.attachment_type.PNG,
        )

        # Save and attach page source to Allure report
        html_path = test_directory / f"{item.name}.html"
        html_path.write_text(page.content(), encoding="utf-8")
        allure.attach.file(
            str(html_path),
            name="Page Source",
            attachment_type=allure.attachment_type.HTML,
        )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    yield
    # Attach video to Allure report (if exists)
    logger.info("Test teardown, checking for video attachment")
    video_path = getattr(item, "_video_path", None)
    if video_path and os.path.exists(video_path):
        logger.info("Save video to Allure report")
        allure.attach.file(
            video_path,
            name="Video",
            attachment_type=allure.attachment_type.WEBM,
        )
