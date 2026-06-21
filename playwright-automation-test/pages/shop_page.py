import logging

logger = logging.getLogger(__name__)


class ShopPage:
    """
    Page Object for /shop

    页面调用 /api/products（不存在，返回 404）。
    测试若断言商品列表可见，将因 API 失败导致列表不渲染而报 TimeoutError。
    trace 中同时有 network 4xx 记录，AI 据此判断为 flaky_env。
    """

    URL_PATH = "/shop"

    def __init__(self, page):
        self.page = page

    def goto(self, base_url: str):
        url = base_url.rstrip("/") + self.URL_PATH
        logger.info(f"Navigating to shop: {url}")
        self.page.goto(url)

    def wait_for_product_list(self, timeout: int = 5000):
        """等待商品列表出现；API 404 时此元素永远不会出现。"""
        logger.info("Waiting for product-list to be visible")
        self.page.get_by_test_id("product-list").wait_for(state="visible", timeout=timeout)

    def is_error_shown(self) -> bool:
        """判断 API 错误提示是否显示。"""
        visible = self.page.get_by_test_id("api-error").is_visible()
        logger.info(f"api-error banner visible: {visible}")
        return visible
