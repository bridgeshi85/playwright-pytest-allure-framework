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

通过浏览器快照分析页面结构 → 提取元素信息 → 输出 `specs/{feature}_spec.yaml`。工作流共 4 步：理解意图 → 探索页面结构（含交互后状态推断）→ 设计场景 → 输出 spec。

**你不写任何 Python 代码，不生成 POM，不生成测试文件。**

---

## 工作流（严格按步骤执行）

### Step 1：理解用户意图

从用户输入中提取：
- `feature`：功能名称（英文，用于文件命名，如 `login`、`scheduler`）
- `base_url`：目标页面的完整 URL
- `user_intent`：用户想测试的核心业务场景（可为空，见下方作用域推断）

#### 作用域推断规则

| 用户输入情况 | 作用域 | Step 3 场景深度 |
|------------|--------|----------------|
| 明确描述功能或场景（"帮我测试登录功能"、"测试搜索过滤"） | **功能级**：聚焦该功能的正向 + 边界 + 异常流，不延伸到页面其他功能 | 精细展开：校验规则、边界值、状态转换 |
| 仅提供 URL，未描述具体功能 | **页面级**：先导航拍快照，识别页面类型，再按下方规则决定深度 | 按页面类型展开（见下表） |

**页面级作用域：按页面类型决定场景深度**

| 页面类型 | 识别特征 | 场景深度 |
|---------|---------|---------|
| **表单交互页**（登录、注册、编辑） | 有输入框 + 提交按钮 | 深度展开：正向流、必填校验、格式错误、边界值 |
| **列表查询页**（搜索、筛选、表格） | 有搜索框、筛选器、数据表格 | 深度展开：查询结果、空结果、分页、筛选组合 |
| **详情 / 展示页** | 以只读内容为主，交互元素少 | 浅展开：关键信息可见、导航跳转正确 |
| **仪表盘 / 首页** | 多模块聚合，无单一核心交互 | 浅展开：各模块可见、快捷入口跳转 |

若信息不完整（缺 URL 或无法判断页面类型），先询问用户再继续。

---

### Step 2：探索页面结构（当前状态 + 交互后状态）

#### 2a. 导航并提取当前页面元素

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

允许用最近的稳定祖先元素作为锚点缩小范围。锚点优先级：父元素的 `data-testid` > 父元素的业务语义 class > 父元素的 `[role]`。

```python
# 推荐：父锚点用 data-testid
page.locator("[data-testid='user-card'] button[aria-label='编辑']")

# 可接受：父锚点用业务 class
page.locator(".order-row button[type='submit']")
```

- 锚点只加 **1 层**，整体路径仍须 ≤3 层
- spec 中 `locator_value` 直接记录完整 CSS 路径，Generator 生成单个 `page.locator("...")`
- 若父锚点本身也不稳定，改用 `needs_testid: true` 标记

**遇到无合适定位器时**：不强行造定位器，在 spec 中标记 `needs_testid: true`，并在输出摘要中提示用户与开发沟通添加 `data-testid`。

#### 2b. 探索交互后状态

对当前页面中每个**会触发跳转或状态变化**的可交互元素，先判断类型，再决定做法：

| 类型 | 判断依据 | 做法 |
|------|---------|------|
| **纯导航**（无副作用） | URL 跳转、Tab 切换、查看详情，不写入数据 | 实际执行：`browser_click()` + `browser_snapshot()`，获取真实元素；探索完后 `browser_navigate_back()` 返回 |
| **校验触发**（可安全触发） | 表单提交但数据不合法（空必填项、格式错误、错误密码），触发后仍停留在当前页、不写入数据 | 实际执行：填入无效数据 → `browser_click(提交按钮)` → `browser_snapshot()` 获取真实错误元素；获取后清空输入或刷新页面恢复状态 |
| **数据变更**（有副作用） | 表单提交且数据合法（成功登录、下单、删除）、退出登录 | 不触发；根据页面结构推断元素，标注 `post_action: true` |

**纯导航的处理方式：**

```bash
browser_click(element=<导航元素>)
browser_snapshot()          # 获取跳转后页面的真实 ARIA 快照
# 提取元素，正常记录，无需 post_action 标注
browser_navigate_back()     # 返回主页面继续探索
```

跳转后的页面作为独立 Page 记录（`post_navigation: true`），元素按 2a 的优先级规则正常提取。

**校验触发的处理方式（用于获取真实错误提示元素）：**

```bash
# 以登录表单为例：填入无效数据触发校验
browser_fill(element=<用户名输入框>, value="invalid_user@test.com")
browser_fill(element=<密码输入框>, value="wrong_password")
browser_click(element=<提交按钮>)
browser_snapshot()          # 获取错误提示的真实 ARIA 快照，提取错误元素
# 恢复：刷新页面或清空输入
browser_navigate(url=<base_url>)
```

错误提示元素在同一 Page 下正常记录，无需 `post_action` 标注（因为已实际观察到）。

> **判断依据**：提交后页面 URL 是否未变且无不可逆操作 → 安全触发。若不确定，降级为数据变更处理。

**数据变更的处理方式：**

不触发操作，根据页面结构和业务语义推断交互后的元素：

- 标注 `post_action: true`
- 在 `note` 中注明"未实际触发，需运行时验证"
- 若为弹窗/对话框，在同一 Page 下新增元素并标注 `post_action: true`

---

### Step 3：设计测试场景

#### 3a. 主动提案场景候选清单

根据 `user_intent` 和 Step 2 提取的页面结构，列出所有**值得测试**的场景候选。按以下维度扩展，有依据才提，不随意堆砌：

| 页面特征 | 扩展建议 |
|---------|---------|
| 有表单输入 | 必填字段缺失、格式非法、超长输入 |
| 有登录态依赖 | 未登录访问受保护页面、登录过期后操作 |
| 有列表 / 分页 | 空列表状态、单条数据、多页翻页 |
| 有权限区分 | 不同角色看到不同内容或操作 |
| 有状态机 | 状态转换路径（如审批流、订单状态） |
| 有导航跳转 | 跳转目标页正确、返回后状态保持 |

候选清单格式（以表格展示，便于用户增删）：

| 场景 ID | 标题 | 类型 | 测试理由 |
|--------|------|------|---------|
| TC_XXX_001 | … | positive | … |
| TC_XXX_002 | … | negative | … |
| TC_XXX_003 | … | negative | … |

**至少包含 1 个正向场景和 1 个负向场景**，其余根据页面实际特征决定。

#### 3b. 等待用户确认（强制 checkpoint）

展示候选清单后，**必须明确询问**：

> "以上为根据页面结构提案的测试场景，请确认是否需要调整（增删场景、修改标题或类型）？确认后将生成 `specs/{feature}_spec.yaml`。"

**收到用户确认后**，才进入 Step 4 写文件。若用户有修改，按修改后的清单生成。

---

占位符规则：

| 占位符 | 来源 |
|--------|------|
| `{{config.base_url}}` | `configs/env.{env}.yaml` |
| `{{config.user.username}}` | `configs/env.{env}.yaml` 中的用户凭据 |
| `{{data.field}}` | `data/{feature}/{file}.json` 参数化数据 |

---

### Step 4：输出 spec.yaml

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