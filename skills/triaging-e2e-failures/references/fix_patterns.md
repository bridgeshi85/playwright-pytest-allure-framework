# Fix Patterns — 修复建议规则

> Step 3 参考文档：当 Step 2 分类结果为 `flaky_element` 时，AI 根据以下模式生成可执行修复代码。

---

## 通用修复原则

1. **优先使用语义化 selector**：`get_by_role`、`get_by_text`、`get_by_label` > CSS > XPath
2. **避免绝对路径 XPath**：`/html/body/div[3]/button` 极易随 DOM 变化而失效
3. **避免动态 class**：如 `btn-primary-a3f9c` 含哈希后缀的类名
4. **善用 `data-testid`**：与前端约定专属测试属性，最稳定
5. **加等待而非加 sleep**：用 `wait_for_selector` / `wait_for_load_state` 代替 `time.sleep()`

---

## Pattern 1：TimeoutError — 元素未渲染

**症状：**
```
TimeoutError: Timeout 30000ms exceeded.
waiting for locator('#submit-btn') to be visible
```

**根因：** 元素存在于 DOM 但尚未渲染/可见，或页面跳转未完成。

**修复模式：**
```python
# ❌ 原代码
page.click("#submit-btn")

# ✅ 修复：先等待可见
page.wait_for_selector("#submit-btn", state="visible", timeout=10000)
page.click("#submit-btn")

# ✅ 修复（推荐）：用 expect 断言可见后操作
from playwright.sync_api import expect
expect(page.locator("#submit-btn")).to_be_visible(timeout=10000)
page.locator("#submit-btn").click()
```

---

## Pattern 2：selector 过期（class/id 变更）

**症状：**
```
TimeoutError: waiting for locator('.old-btn-class')
```
DOM 快照中未见该 class，但有功能相同的新 class。

**修复模式：**
```python
# ❌ 原代码（脆弱 class）
page.click(".old-btn-class")

# ✅ 修复方案 A：改用 data-testid（推荐，需前端配合）
page.locator("[data-testid='submit-button']").click()

# ✅ 修复方案 B：改用语义化 role
page.get_by_role("button", name="提交").click()

# ✅ 修复方案 C：改用文本
page.get_by_text("提交", exact=True).click()
```

---

## Pattern 3：strict mode violation（多元素匹配）

**症状：**
```
Error: strict mode violation: locator('.btn') resolved to 3 elements
```

**修复模式：**
```python
# ❌ 原代码（匹配多个）
page.locator(".btn").click()

# ✅ 修复：精确定位
page.locator(".btn").nth(0).click()                    # 取第一个
page.locator("form .btn").click()                      # 限定父容器
page.get_by_role("button", name="登录").click()        # 用文本区分
```

---

## Pattern 4：元素被遮挡（覆盖层/弹窗）

**症状：**
```
Error: element is not clickable at point (x, y); another element receives the click
```

**修复模式：**
```python
# ✅ 先关闭遮挡弹窗
dialog_close = page.locator("[data-testid='dialog-close']")
if dialog_close.is_visible():
    dialog_close.click()

# ✅ 或使用 force=True（谨慎，可能掩盖真实问题）
page.locator("#target").click(force=True)

# ✅ 等待遮挡层消失后再点击
page.locator(".loading-overlay").wait_for(state="hidden")
page.locator("#target").click()
```

---

## Pattern 5：页面跳转后元素 detached

**症状：**
```
Error: locator.click: Element is detached from DOM
```

**修复模式：**
```python
# ❌ 原代码（持有旧引用）
btn = page.locator("#btn")
page.navigate("/other")
btn.click()  # detached!

# ✅ 修复：跳转后重新获取引用
page.navigate("/other")
page.wait_for_load_state("networkidle")
page.locator("#btn").click()
```

---

## Pattern 6：等待网络请求完成

**症状：** 操作后数据未刷新，下一步断言失败。

**修复模式：**
```python
# ✅ 等待特定接口响应后再断言
with page.expect_response("**/api/tasks**") as resp:
    page.locator("[data-testid='save-btn']").click()
assert resp.value.status == 200

# ✅ 等待页面稳定
page.wait_for_load_state("networkidle", timeout=10000)
```

---

## Pattern 7：动态 id / 随机 hash class

**症状：** selector 中含数字序列或哈希，如 `#input-1749812345`、`.btn-ab3f9c12`

**修复模式：**
```python
# ❌ 原代码
page.fill("#input-1749812345", "value")

# ✅ 修复方案 A：改用 aria-label / placeholder
page.get_by_label("用户名").fill("value")
page.get_by_placeholder("请输入用户名").fill("value")

# ✅ 修复方案 B：CSS 属性选择器模糊匹配（谨慎）
page.locator("input[name='username']").fill("value")

# ✅ 修复方案 C：与前端约定 data-testid
page.locator("[data-testid='username-input']").fill("value")
```

---

## Selector 优先级速查表

| 优先级 | 方式 | 示例 | 稳定性 |
|--------|------|------|--------|
| 1 | `data-testid` | `[data-testid='login-btn']` | ⭐⭐⭐⭐⭐ |
| 2 | `get_by_role` | `get_by_role("button", name="登录")` | ⭐⭐⭐⭐⭐ |
| 3 | `get_by_label` | `get_by_label("用户名")` | ⭐⭐⭐⭐ |
| 4 | `get_by_placeholder` | `get_by_placeholder("请输入...")` | ⭐⭐⭐⭐ |
| 5 | `get_by_text` | `get_by_text("提交", exact=True)` | ⭐⭐⭐ |
| 6 | CSS 属性选择器 | `input[name='username']` | ⭐⭐⭐ |
| 7 | CSS class | `.submit-btn` | ⭐⭐ |
| 8 | XPath（相对） | `//button[text()='登录']` | ⭐⭐ |
| 9 | XPath（绝对） | `/html/body/div[3]/button` | ⭐ |

