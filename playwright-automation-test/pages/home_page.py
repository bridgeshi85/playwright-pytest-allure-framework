import logging

from playwright.sync_api import Locator, Page

logger = logging.getLogger(__name__)


class HomePage:
    """首页 Page Object。

    封装首页的定位器，不包含断言逻辑。
    """

    URL_PATH = "/home"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.welcome_text: Locator = page.get_by_test_id("welcome-text")  # 登录成功后首页欢迎文本