import os
import shutil
import pytest
import logging
from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser():
    logger.info("start test")
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    yield browser
    logger.info("close the browser")
    browser.close()


# 定义一个 fixture 来创建和清理测试目录
@pytest.fixture
def test_directory(request):
    logger.info("create result folder")
    # 确保基础测试结果目录存在
    test_results_dir = Path('test_results')
    test_results_dir.mkdir(parents=True, exist_ok=True)

    # 获取当前日期
    date_str = datetime.now().strftime('%Y-%m-%d')
    # 根据时间创建唯一的测试序号
    test_count = sum(1 for _ in os.scandir(test_results_dir) if _.is_dir()) + 1
    test_dir_name = f"{date_str}-{test_count}"
    test_dir = test_results_dir / test_dir_name
    test_dir.mkdir(parents=True, exist_ok=True)  # 创建目录

    yield test_dir


@pytest.fixture
def page(browser, test_directory, request):
    # page fixture 创建一个新的浏览器页面
    # 会先调用browser和test_directory fixture
    # 失败时截图保存在test_directory中

    page = browser.new_page()

    # Capture screenshot if the test fails
    def capture_final_screenshot():
        if request.node.rep_call.failed:
            logger.info("test failed")
            screenshot_path = test_directory / "final-screenshot.png"
            page.screenshot(path=str(screenshot_path))
            logger.info(f"Test failed, final screenshot saved at {screenshot_path}")
        page.close()

    request.addfinalizer(capture_final_screenshot)
    yield page


# ========== Pytest hook：用于判断测试是否失败 ==========
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """在测试结束后，将执行结果写入 item 对象，供 fixture 使用。"""
    outcome = yield
    rep = outcome.get_result()

    setattr(item, f"rep_{rep.when}", rep)
