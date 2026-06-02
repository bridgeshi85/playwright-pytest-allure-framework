import logging

logger = logging.getLogger(__name__)


class DashboardPage:
    """
    Page Object for /dashboard

    该页面在 3 秒后才渲染统计卡片（模拟异步数据加载）。
    测试若使用过短的 timeout 等待统计元素，将触发 flaky_element 失败。
    """

    URL_PATH = "/dashboard"

    def __init__(self, page):
        self.page = page

    def goto(self, base_url: str):
        url = base_url.rstrip("/") + self.URL_PATH
        logger.info(f"Navigating to dashboard: {url}")
        self.page.goto(url)

    def wait_for_stats(self, timeout: int = 5000):
        """
        等待统计卡片出现。
        正常超时应 > 3000ms；如果传入 timeout=1000 会触发 TimeoutError（flaky_element）。
        """
        logger.info(f"Waiting for stats to load (timeout={timeout}ms)")
        self.page.get_by_test_id("stat-users").wait_for(state="visible", timeout=timeout)

    def get_user_count(self) -> str:
        return self.page.get_by_test_id("stat-users").inner_text()

    def get_order_count(self) -> str:
        return self.page.get_by_test_id("stat-orders").inner_text()

    def get_revenue(self) -> str:
        return self.page.get_by_test_id("stat-revenue").inner_text()
