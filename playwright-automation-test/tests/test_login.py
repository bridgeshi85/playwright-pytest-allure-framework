from pages.login_page import LoginPage
from pages.home_page import HomePage
import pytest


def test_login_success(page, config):
    login_page = LoginPage(page)
    home_page = HomePage(page)

    # 1. 打开登录页
    login_page.goto(config["base_url"])

    # 2. 登录操作
    # Todo - 暂时hardcode, 后续改为从文件读取实现data driven
    login_page.login("admin", "123456")
    # 3. 等待跳转到首页

    # 4. 断言跳转成功
    assert home_page.should_show_welcome_text(), "登录失败，未显示欢迎文本"
