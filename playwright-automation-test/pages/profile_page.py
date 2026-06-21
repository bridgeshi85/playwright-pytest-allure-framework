import logging

logger = logging.getLogger(__name__)


class ProfilePage:
    """
    Page Object for /profile

    演示两种 real_bug 失败场景：

    1. Assertion 失败：
       get_email() 返回 "admin@example.com"，
       测试若断言 "admin@demo.com" 触发 AssertionError。

    2. Element not found：
       UI 重构后编辑按钮 testid 已改为 "btn-edit-profile"，
       click_edit_button_with_old_id() 使用旧 testid "btn-edit"，
       将触发 "locator resolved to 0 elements"。
    """

    URL_PATH = "/profile"

    def __init__(self, page):
        self.page = page

    def goto(self, base_url: str):
        url = base_url.rstrip("/") + self.URL_PATH
        logger.info(f"Navigating to profile: {url}")
        self.page.goto(url)

    def get_username(self) -> str:
        text = self.page.get_by_test_id("user-name").inner_text()
        logger.info(f"user-name: {text}")
        return text

    def get_email(self) -> str:
        """返回页面实际邮箱：admin@example.com"""
        text = self.page.get_by_test_id("user-email").inner_text()
        logger.info(f"user-email: {text}")
        return text

    def get_role(self) -> str:
        text = self.page.get_by_test_id("user-role").inner_text()
        logger.info(f"user-role: {text}")
        return text

    def click_edit_button(self):
        """使用正确的新 testid，正常点击。"""
        logger.info("Clicking edit button (new testid: btn-edit-profile)")
        self.page.get_by_test_id("btn-edit-profile").click()

    def click_edit_button_with_old_id(self):
        """
        使用旧 testid 'btn-edit'（UI 重构后已不存在）。
        调用此方法将触发 real_bug (element not found)。
        """
        logger.info("Clicking edit button with OLD testid: btn-edit (will fail)")
        self.page.get_by_test_id("btn-edit").click(timeout=5000)
