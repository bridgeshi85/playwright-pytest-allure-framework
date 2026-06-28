---
name: playwright-test-planner
description: >
 通过浏览器快照分析页面结构，生成语言无关的测试规格文档（spec.yaml），供 playwright-test-generator 消费。
 触发词："分析页面"、"生成 spec"、"帮我规划测试"、"探索这个页面"、"写测试前先分析"、"生成测试规格"、"test planner"。
 使用场景：用户提供待测功能描述和 URL，skill 探索页面后输出 specs/{feature}_spec.yaml。
 前置条件：需要 Playwright MCP（@playwright/mcp）提供浏览器工具。MCP 配置已内置于 .claude/settings.json，首次使用执行 `npx @playwright/mcp@latest` 确认依赖已安装，然后重新打开 Claude Code 即可自动加载。
 完成后：提示用户确认 spec，然后运行 playwright-test-generator skill 生成代码。
---

# Playwright Test Planner Skill

通过浏览器快照分析页面结构 → 提取元素信息 → 输出 `specs/{feature}_spec.yaml`。

**你不写任何 Python 代码，不生成 POM，不生成测试文件。**

---

## 工作流（严格按步骤执行）

### Step 1：理解用户意图

从用户输入中提取：
- `feature`：功能名称（英文，用于文件命名，如 `login`、`scheduler`）
- `base_url`：目标页面的完整 URL
- `user_intent`：用户想测试的核心业务场景

若信息不完整，先询问用户再继续。

---

### Step 2：探索主页面

```bash
# 导航并拍快照（通过 Playwright MCP）
browser_navigate(url=<base_url>)
browser_snapshot()
```

从快照（ARIA 树）中识别所有**可交互元素**，按以下优先级提取定位属性：

| 优先级 | 条件 | 对应 locator 策略 | spec 中 `locator_strategy` 值 |
|--------|------|-------------------|-------------------------------|
| 1 | 元素有 `data-testid` 或 `testid` 属性 | `page.get_by_test_id(value)` | `get_by_test_id` |
| 2 | 元素有稳定、非动态生成的 `id` 属性 | `page.locator("#id")` | `css_id` |
| 3 | 无以上属性，但可通过语义化属性组合唯一定位（≤3 层） | `page.locator("tag[attr=val][attr2=val2]")` | `css_combo` |
| 4 | 输入框有 `placeholder` 属性（备选，仅限 input 元素） | `page.get_by_placeholder(value)` | `get_by_placeholder` |

> **关键规则**：找到即停止，不向下兼容。对每个元素只记录最高优先级的定位方式。

#### Locator 质量检查规则（提取时强制执行）

**禁止使用以下属性作为定位依据**，发现时跳过，继续往下找：

| 禁止类型 | 识别特征 | 原因 |
|----------|----------|------|
| 动态 class | 形如 `css-1a2b3c`、`sc-xxxxx`、哈希后缀 | 每次构建变化，必然导致脚本失效 |
| 样式类 | 形如 `col-md-4`、`hover-light`、`btn-primary`、`flex-center` | 样式重构即失效，无领域语义 |
| 动态 id | 形如 `input-1234`、`el-7f3a`、包含数字后缀的随机 id | 每次渲染不同，不可靠 |
| 纯数字索引 | `nth=2`、`:eq(3)` | 顺序变化即失效，除非明确业务语义（第一条/最后一条） |
| 文本内容 | 通过 visible text 定位 | 文本易变且多语言不友好，一律禁止（特殊豁免见下方） |

> **唯一豁免**：表格数据行 / 动态列表中，行的文本内容本身就是测试数据的一部分时，允许使用 `page.get_by_text(value, exact=True)`。此时记录 `locator_strategy: get_by_text`，并在 `note` 字段说明"该元素为动态数据行，文本即业务标识符"。其他任何场景（按钮、标签、标题、表单项）一律不得使用。

**CSS 组合定位的约束**（仅在优先级 3 时适用）：

- 只使用**语义化属性**，允许清单如下：

  | 属性类型 | 示例 | 说明 |
  |---------|------|------|
  | `[role]` | `[role="dialog"]`、`[role="button"]` | HTML 语义角色 |
  | `[aria-*]` | `[aria-label="关闭"]`、`[aria-expanded="true"]` | 无障碍属性 |
  | `[type]`、`[name]` | `input[type="email"]`、`input[name="search"]` | 结构化表单属性 |
  | `[data-*]`（非 testid） | `[data-status="active"]` | 业务数据属性 |
  | 业务语义 class | `.product-price`、`.add-to-cart` | 有领域含义的 class |

  **禁止**：样式类（`.btn-primary`、`.col-md-4`）、动态哈希类（`.css-1a2b3c`）

- 路径层级控制在 **2～3 层以内**；超过 3 层须重新寻找更近的锚点
- 生成前验证唯一性：快照中搜索该选择器，确认只匹配到目标元素
- 在 spec 的 `note` 字段说明为何无法使用优先级 1～2 的策略

**父锚点消歧义**（当目标元素单独定位不唯一时）：

如果符合以下条件，允许用最近的稳定祖先元素作为锚点缩小范围，只使用父元素的 `data-testid`。
- 父元素必须有稳定的 `data-testid` 属性
- spec 中 `locator_value` 直接记录完整 CSS 路径，Generator 生成单个 `page.locator("...")`

**遇到无合适定位器时**：不强行造定位器，在 spec 中标记 `needs_testid: true`，并在输出摘要中提示用户与开发沟通添加 `data-testid`。

---

### Step 3：探索交互后页面（如有跳转或状态变化）

对提交表单、点击按钮等操作后可能出现的目标页面或弹窗，根据页面结构**推断**（不实际点击）交互后会出现哪些元素，标注 `post_action: true`，由 generator 验证。

---

### Step 4：分析测试场景

根据 `user_intent` 和页面结构设计：
- **至少 1 个正向场景**（happy path）
- **至少 1 个负向场景**（error case）

占位符规则：

| 占位符 | 来源 |
|--------|------|
| `{{config.base_url}}` | `configs/env.{env}.yaml` |
| `{{config.user.username}}` | `configs/env.{env}.yaml` 中的用户凭据 |
| `{{data.field}}` | `data/{feature}/{file}.json` 参数化数据 |

---

### Step 5：输出 spec.yaml

```bash
# 若 specs/ 不存在，先创建
mkdir -p specs/
```

在 `specs/{feature}_spec.yaml` 输出，格式见下方模板。完整字段说明见 `references/spec-schema.md`。

**不创建任何 `.py` 文件，不运行任何测试命令。**

完成后展示摘要（feature 名、页面数、场景数），并提示：
> "已生成 `specs/{feature}_spec.yaml`。请确认场景覆盖是否完整，确认后运行 `playwright-test-generator` skill 生成代码。"

---

## spec.yaml 模板

```yaml
# 由 playwright-test-planner 自动生成
meta:
  feature: "login"
  allure_feature: "User Authentication"
  generated_by: "playwright-test-planner"
  base_url: "http://localhost:5173"

pages:
  - class_name: LoginPage
    file_path: pages/login_page.py
    url_path: /login
    elements:
      - name: username_input
        locator_strategy: get_by_test_id
        locator_value: "input-username"
        note: "用户名输入框"
      - name: password_input
        locator_strategy: get_by_test_id
        locator_value: "input-password"
        note: "密码输入框"
      - name: submit_button
        locator_strategy: get_by_test_id
        locator_value: "btn-login"
        note: "登录按钮"
      - name: error_message
        locator_strategy: css_combo
        locator_value: "[role='alert'].login-error"
        note: "登录失败错误提示"
        post_action: true
        needs_testid: true

  - class_name: DashboardPage
    file_path: pages/dashboard_page.py
    url_path: /dashboard
    post_navigation: true
    elements:
      - name: welcome_heading
        locator_strategy: get_by_test_id
        locator_value: "dashboard-welcome"
        note: "欢迎标题"
        post_action: true

scenarios:
  - id: TC_LOGIN_001
    story: "Valid login"
    title: "使用有效凭据登录成功"
    type: positive
    actions:
      - step: 1
        action: navigate
        target_page: LoginPage
      - step: 2
        action: fill
        page: LoginPage
        element: username_input
        value: "{{config.user.username}}"
      - step: 3
        action: fill
        page: LoginPage
        element: password_input
        value: "{{config.user.password}}"
      - step: 4
        action: click
        page: LoginPage
        element: submit_button
    assertions:
      - type: url
        expected: "{{config.base_url}}/dashboard"
      - type: visible
        page: DashboardPage
        element: welcome_heading

  - id: TC_LOGIN_002
    story: "Invalid login"
    title: "使用错误密码时显示错误提示"
    type: negative
    actions:
      - step: 1
        action: navigate
        target_page: LoginPage
      - step: 2
        action: fill
        page: LoginPage
        element: username_input
        value: "{{config.user.username}}"
      - step: 3
        action: fill
        page: LoginPage
        element: password_input
        value: "wrong_password_intentional"
      - step: 4
        action: click
        page: LoginPage
        element: submit_button
    assertions:
      - type: visible
        page: LoginPage
        element: error_message
      - type: url
        expected: "{{config.base_url}}/login"
        note: "登录失败不应跳转"
```

参数化场景格式见 `references/spec-schema.md`。

---

## 与 playwright-test-generator 的契约

Generator 依赖以下字段，**不得省略**：

| 字段 | Generator 用途 |
|------|----------------|
| `meta.allure_feature` | `@allure.feature` |
| `pages[].class_name` | POM 类名 |
| `pages[].file_path` | POM 文件路径 |
| `pages[].elements[].locator_strategy` | locator 方法选择 |
| `pages[].elements[].locator_value` | locator 参数值 |
| `pages[].elements[].needs_testid` | 生成 TODO 注释 |
| `scenarios[].story` | `@allure.story` |
| `scenarios[].title` | `@allure.title` |
| `scenarios[].actions` | Act 部分 |
| `scenarios[].assertions` | Assert 部分 |