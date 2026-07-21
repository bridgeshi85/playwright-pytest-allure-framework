import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def load_test_data(feature: str, filename: str) -> list[dict]:
    """从 data/{feature}/{filename} 加载测试数据。"""
    path = DATA_DIR / feature / filename
    logger.info(f"Loading test data from {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)