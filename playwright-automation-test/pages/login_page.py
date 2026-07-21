import logging

from playwright.sync_api import Locator, Page

logger = logging.getLogger(__name__)


class LoginPage:
    """登录页面 Page Object。

    封装所有登录页面的定位器与操作，不包含断言逻辑。
    """

    URL_PATH = "/"

    def __init__(self, page: Page) -> None:
        self.page = page
        # --- 表单区域 ---
        self.username_input: Locator = page.get_by_test_id("input-username")  # 用户名输入框
        self.password_input: Locator = page.get_by_test_id("input-password")  # 密码输入框
        self.submit_button: Locator = page.get_by_test_id("btn-login")  # 登录按钮
        # --- 反馈区域 ---
        # TODO: 请开发在错误提示上添加 data-testid，目前用 AntD 组件库状态 class 兜底定位
        self.error_message: Locator = page.locator(".ant-message-notice-error")  # 登录失败错误提示

    def open(self, base_url: str) -> None:
        """导航到登录页。"""
        logger.info(f"Navigating to login page: {base_url}{self.URL_PATH}")
        self.page.goto(f"{base_url}{self.URL_PATH}")

    def login(self, username: str, password: str) -> None:
        """执行完整登录操作。"""
        logger.info(f"Performing login with username: {username}")
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()
