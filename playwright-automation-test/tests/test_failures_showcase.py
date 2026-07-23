"""
test_failures_showcase.py
=========================
专门用于演示 AI Triage Skill 的 4 种失败类型。
每个测试都会**故意失败**，产生各具特征的 trace.zip，
供 parse_trace.py + triage_rules.md 分析。

失败类型速查：
  test_dashboard_stats_load_timeout  → flaky_element  （元素延迟渲染，timeout 太短）
  test_profile_email_assertion       → real_bug        （断言文本不匹配）
  test_profile_edit_button_not_found → real_bug        （UI 重构后 testid 已变更）
  test_shop_product_list_visible     → flaky_env       （/api/products 返回 404）
"""
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.dashboard_page import DashboardPage
from pages.profile_page import ProfilePage
from pages.shop_page import ShopPage
# ---------------------------------------------------------------------------
# 辅助：登录并跳转到首页
# ---------------------------------------------------------------------------

def _login(page, base_url: str):
    """登录操作封装，供各用例复用。"""
    login_page = LoginPage(page)
    login_page.goto(base_url)
    login_page.login("admin", "123456")
    home_page = HomePage(page)
    assert home_page.should_show_welcome_text(), "登录失败，无法进入后续测试"
# ---------------------------------------------------------------------------
# Case 1: flaky_element — Dashboard 统计卡片延迟渲染
# ---------------------------------------------------------------------------

def test_dashboard_stats_load_timeout(page, config):
    """
    预期失败类型：flaky_element
    失败原因：Dashboard 数据卡片在 3s 后才渲染，
              测试使用 timeout=1000ms 等待，必然超时。
    trace 特征：
      - failed action: locator.wait_for  selector='[data-testid="stat-users"]'
      - error: TimeoutError（1000ms exceeded）
      - 失败前 actions 正常（goto、登录流程、navigate to /dashboard）
    """
    _login(page, config["base_url"])

    dashboard = DashboardPage(page)
    dashboard.goto(config["base_url"])

    # ❌ timeout 故意设为 1000ms（远小于 3000ms 的渲染延迟）→ 触发 TimeoutError
    dashboard.wait_for_stats(timeout=1000)

    # 若到达这里说明元素已出现（不会到达）
    assert dashboard.get_user_count() == "1128"
# ---------------------------------------------------------------------------
# Case 2: real_bug — Profile 邮箱断言文本不匹配
# ---------------------------------------------------------------------------

def test_profile_email_assertion(page, config):
    """
    预期失败类型：real_bug（assertion 断言失败）
    失败原因：页面实际邮箱是 "admin@example.com"，
              测试错误地断言为 "admin@demo.com"。
    trace 特征：
      - failed action: expect.to_have_text
      - error: AssertionError，expected "admin@demo.com"，actual "admin@example.com"
      - 无网络错误，无 TimeoutError
    """
    _login(page, config["base_url"])

    profile = ProfilePage(page)
    profile.goto(config["base_url"])

    actual_email = profile.get_email()

    # ❌ 断言错误的期望值 → 触发 AssertionError
    assert actual_email == "admin@demo.com", (
        f"邮箱不匹配：期望 admin@demo.com，实际 {actual_email}"
    )
# ---------------------------------------------------------------------------
# Case 3: real_bug — Profile 编辑按钮 testid 已重构，旧 ID 找不到元素
# ---------------------------------------------------------------------------

def test_profile_edit_button_not_found(page, config):
    """
    预期失败类型：real_bug（element not found）
    失败原因：UI 重构后编辑按钮 testid 从 "btn-edit" 改为 "btn-edit-profile"，
              测试仍使用旧 testid，locator 解析为 0 个元素。
    trace 特征：
      - failed action: locator.click  selector='[data-testid="btn-edit"]'
      - error: TimeoutError / strict mode violation
      - DOM 快照中不存在 data-testid="btn-edit"（可加 --dom 验证）
    """
    _login(page, config["base_url"])

    profile = ProfilePage(page)
    profile.goto(config["base_url"])

    # ❌ 使用旧 testid，元素不存在 → 触发 TimeoutError（locator resolved to 0 elements）
    profile.click_edit_button_with_old_id()
# ---------------------------------------------------------------------------
# Case 4: flaky_env — Shop 页调用 /api/products 返回 404，商品列表不渲染
# ---------------------------------------------------------------------------

def test_shop_product_list_visible(page, config):
    """
    预期失败类型：flaky_env（环境/API 问题）
    失败原因：页面启动时 fetch /api/products，该接口不存在（404）。
              商品列表 data-testid="product-list" 因 API 失败而不渲染。
    trace 特征：
      - failed action: locator.wait_for  selector='[data-testid="product-list"]'
      - error: TimeoutError
      - network failures: GET /api/products → 404
      - console errors: "Failed to load products: API error: 404 Not Found"
    """
    _login(page, config["base_url"])

    shop = ShopPage(page)
    shop.goto(config["base_url"])

    # ❌ API 404 导致列表不渲染，5s 内等不到元素 → TimeoutError + network 4xx
    shop.wait_for_product_list(timeout=5000)

    # 若到达这里说明列表已出现（不会到达）
    assert not shop.is_error_shown(), "API 错误提示不应出现"
