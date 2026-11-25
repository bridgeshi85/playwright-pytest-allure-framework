import os
import pytest
from pathlib import Path
from collections.abc import Iterator  # 引入 Iterator
from playwright.sync_api import Browser, BrowserContext

HAR_PATH = Path(__file__).resolve().parent.parent / "data" / "har" / "har_demo.har"
HAR_API_FILTER = "**/api/har-demo/**"

@pytest.fixture
# 将这里的返回值类型改为 Iterator[BrowserContext]
def har_context(browser: Browser) -> Iterator[BrowserContext]:
    """统一的 HAR 上下文，通过环境变量 RECORD_HAR 控制是录制还是回放"""
    # 确保目录存在
    HAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    context = browser.new_context()
    
    is_record_mode = os.getenv("RECORD_HAR") == "1"
    
    context.route_from_har(
        str(HAR_PATH),
        url=HAR_API_FILTER,
        update=is_record_mode,
        update_content="embed",
        not_found="abort" if not is_record_mode else "fallback"
    )
    
    yield context
    context.close()