import os
from datetime import datetime
from pathlib import Path

import pytest
import logging

logger = logging.getLogger(__name__)


def save_screenshot(page, test_directory, filename="final-screenshot.png"):
    """
    截图并记录日志
    :param page: 当前页面对象
    :param test_directory: 测试目录
    :param filename: 截图文件名
    """
    screenshot_path = test_directory / filename
    page.screenshot(path=str(screenshot_path))
    logger.info(f"Test failed, final screenshot saved at {screenshot_path}")


@pytest.fixture
def test_directory(request):
    """
    创建测试结果目录
    目录格式：test_results/YYYY-MM-DD-序号
    例如：test_results/2023-10-05-1
    目录中保存该次测试的所有结果文件，如截图、日志等。
    依赖于 test_results 目录的存在。如果不存在，则创建该目录。
    :param request:
    :return:
    """
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
