import allure
import pytest
from playwright.sync_api import Page, expect

from pages.home_page import HomePage
from pages.login_page import LoginPage
from utils.test_data_loader import load_test_data

_INVALID_LOGIN_CASES = load_test_data("login", "invalid_login_cases.json")


@allure.feature("User Authentication")
class TestLogin:
    """登录功能测试集。"""

    @allure.story("Valid login")
    @allure.title("使用有效凭据登录成功并跳转首页")
    def test_tc_login_001(self, page: Page, config: dict) -> None:
        # Arrange
        login_page = LoginPage(page)
        home_page = HomePage(page)
        login_page.open(config["base_url"])

        # Act
        login_page.login(username="admin", password="123456")

        # Assert
        expect(page).to_have_url(f"{config['base_url']}/home")
        expect(home_page.welcome_text).to_be_visible()

    @allure.story("Invalid login")
    @allure.title("使用无效凭据登录时停留在登录页并提示错误")
    @pytest.mark.parametrize(
        "case",
        _INVALID_LOGIN_CASES,
        ids=[c["description"] for c in _INVALID_LOGIN_CASES],
    )
    def test_tc_login_002(self, page: Page, config: dict, case: dict) -> None:
        # Arrange
        login_page = LoginPage(page)
        login_page.open(config["base_url"])

        # Act
        login_page.login(username=case["username"], password=case["password"])

        # Assert
        expect(login_page.error_message).to_be_visible()
        expect(page).to_have_url(f"{config['base_url']}/")
