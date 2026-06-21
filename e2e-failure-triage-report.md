# 🔍 E2E 失败根因汇总报告

> 生成时间：2026-06-13 11:38  
> 分析用例数：4

---

## 汇总表

| 用例 | 分类 | 置信度 | 失败原因 | 修复方向 | 代码位置 |
|------|------|--------|----------|----------|----------|
| `test_dashboard_stats_load_timeout` | `flaky_test/element_missing` | 0.85 | 元素渲染需 3s，timeout 仅设 1000ms 导致超时 | 将 `timeout=1000` 调整为 ≥ 5000ms | `tests/test_failures_showcase.py:56` |
| `test_profile_email_assertion` | `real_bug/assertion_mismatch` | 0.90 | 断言期望值写错，期望 `admin@demo.com` 实际为 `admin@example.com` | 修正断言期望值为 `admin@example.com` | `tests/test_failures_showcase.py:84` |
| `test_profile_edit_button_not_found` | `flaky_test/selector_renamed` | 0.92 | UI 重构后 `btn-edit` 已更名为 `btn-edit-profile`，旧 testid 不存在 | 将 `btn-edit` 替换为 `btn-edit-profile` | `pages/profile_page.py:58` |
| `test_shop_product_list_visible` | `real_bug/api_failure` | 0.90 | `/api/products` 返回 404，商品列表无法渲染 | 检查后端接口 `GET /api/products`，提交缺陷工单 | `tests/test_failures_showcase.py:133` |

---

## 逐条详情

### `test_dashboard_stats_load_timeout`

- **分类**：`flaky_test` / `element_missing`  
- **置信度**：0.85（命中 `Rule 3 — Selector 不存在 / 延迟渲染`）  
- **失败原因**：Dashboard 统计卡片（`data-testid="stat-users"`）需要约 3000ms 才完成异步渲染，但测试代码中 `wait_for_stats(timeout=1000)` 故意将超时设置为 1000ms，必然触发 `TimeoutError`。
- **关键证据**：
  - `TimeoutError: Locator.wait_for: Timeout 1000ms exceeded`
  - 失败 selector：`[data-testid="stat-users"]`
  - 失败前动作正常（goto、登录、navigate to /dashboard）
  - 无网络错误，无 console 报错
- **修复方向**：将 `dashboard.wait_for_stats(timeout=1000)` 的超时值提升至 ≥ 5000ms（建议 10000ms），以覆盖组件异步加载延迟
- **代码位置**：`tests/test_failures_showcase.py:56 test_dashboard_stats_load_timeout`

---

### `test_profile_email_assertion`

- **分类**：`real_bug` / `assertion_mismatch`  
- **置信度**：0.90（命中 `Rule 4 — 数据断言失败`）  
- **失败原因**：测试断言邮箱为 `admin@demo.com`，但页面实际返回 `admin@example.com`。断言值与真实数据不符，属于测试代码中预期值写错，或后端数据与测试预期不一致。
- **关键证据**：
  - `AssertionError: 邮箱不匹配：期望 admin@demo.com，实际 admin@example.com`
  - `assert 'admin@example.com' == 'admin@demo.com'`
  - 无网络失败，无 TimeoutError
- **修复方向**：将测试代码中 `assert actual_email == "admin@demo.com"` 改为 `assert actual_email == "admin@example.com"`；或确认后端用户数据与测试期望一致
- **代码位置**：`tests/test_failures_showcase.py:84 test_profile_email_assertion`

---

### `test_profile_edit_button_not_found`

- **分类**：`flaky_test` / `selector_renamed`  
- **置信度**：0.92（命中 `Rule 2 — Selector 已改名`）  
- **失败原因**：UI 重构后编辑按钮的 `data-testid` 从 `btn-edit` 变更为 `btn-edit-profile`，测试代码仍使用旧 testid，locator 解析为 0 个元素，触发 5000ms 超时。
- **关键证据**：
  - `TimeoutError: Locator.click: Timeout 5000ms exceeded`
  - 失败 selector：`[data-testid="btn-edit"]`
  - 日志显示：`Clicking edit button with OLD testid: btn-edit (will fail)`
  - 页面实际存在 `[data-testid="btn-edit-profile"]`，功能相同
- **修复方向**：将 `[data-testid="btn-edit"]` 替换为 `[data-testid="btn-edit-profile"]`（`pages/profile_page.py` 中 `click_edit_button_with_old_id` 方法，或更新调用处）
- **代码位置**：`pages/profile_page.py:58 click_edit_button_with_old_id`

---

### `test_shop_product_list_visible`

- **分类**：`real_bug` / `api_failure`  
- **置信度**：0.90（命中 `Rule 1 — API 失败`）  
- **失败原因**：Shop 页面加载时调用 `GET /api/products`，该接口返回 404，前端在 API 失败状态下不渲染商品列表（`data-testid="product-list"`），5000ms 内等不到元素，触发 `TimeoutError`。
- **关键证据**：
  - `TimeoutError: Locator.wait_for: Timeout 5000ms exceeded`
  - 失败 selector：`[data-testid="product-list"]`
  - 网络失败：`GET 404 /api/products`
  - console 错误：`Failed to load products: API error: 404 Not Found`
- **修复方向**：检查 `GET /api/products` 对应的后端接口是否存在且正确部署；若接口未实现则提交缺陷工单；若为测试环境问题则检查环境配置 `base_url`
- **代码位置**：`tests/test_failures_showcase.py:133 test_shop_product_list_visible`

---

*报告由 AI Skill **triaging-e2e-failures** 自动生成 · 置信度 < 0.6 建议人工复核*
