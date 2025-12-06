import pytest
from utils.config_loader import load_config
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config(pytestconfig):
    """加载当前运行环境配置"""
    logger.info("load config")
    env = pytestconfig.getoption("--env") or "default"
    return load_config(env)
