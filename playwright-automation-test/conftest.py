import pytest
import logging
from utils.config_loader import load_config
# Import fixtures to ensure they are registered
from fixtures.browser_fixture import browser, page
from fixtures.report_fixture import test_directory

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
