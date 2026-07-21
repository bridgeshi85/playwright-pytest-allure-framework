---
name: playwright-test-generator
description: >
 读取 playwright-test-planner 生成的 spec.yaml，生成 POM 和测试用例，并通过 venv 执行 pytest 验证。
 触发词："生成测试代码"、"根据 spec 生成"、"帮我生成 POM"、"生成测试用例"、"test generator"、"从 spec 生成"。
 前置条件：必须已存在对应的 specs/{feature}_spec.yaml，否则先运行 playwright-test-planner skill。
 输出：pages/{feature}_page.py + tests/test_{feature}.py，并用 venv pytest 验证。
---

# Playwright Test Generator Skill

读取 `specs/{feature}_spec.yaml` → 生成 Page Object + 测试用例 → 用 venv pytest 验证。

**输入来源只有 spec.yaml，不允许在没有 spec 的情况下直接生成代码。**

---

## 工作流

### Step 1：读取 spec.yaml

```bash
cat specs/{feature}_spec.yaml
```

解析所有字段：`meta`、`pages`、`scenarios`。这是唯一权威输入，不得自行修改场景设计。

---

### Step 2：生成 Page Object

路径：`pages/{feature}_page.py`

按 `locator_strategy` 字段映射生成 locator 代码：

| `locator_strategy` | 生成代码 | TODO 注释 |
|--------------------|---------|----------|
| `get_by_test_id` | `page.get_by_test_id("{value}")` | 无 |
| `css_id` | `page.locator("#{value}")` | 无 |
| `get_by_placeholder` | `page.get_by_placeholder("{value}")` | 无 |
| `css_combo` | `page.locator("{value}")` | 若 `needs_testid: true`，上一行加 `# TODO: 请开发添加 data-testid="{name}"` |
| `get_by_text` | `page.get_by_text("{value}", exact=True)` | 同上 |

注释规则（强制）：
- 每个 locator 只写**一行行内注释**，内容为 spec 的 `note` 字段
- `needs_testid: true` 的元素在 locator 行**上方**加一行 TODO
- 禁止在注释中写优先级标签、定位策略选择理由

#### Page Object 模板

```python
# pages/login_page.py
import logging

from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)


class LoginPage:
    """登录页面 Page Object。

    封装所有登录页面的定位器与操作，不包含断言逻辑。
    """

 URL_PATH = "/login"

 def __init__(self, page: Page) -> None:
 self.page = page
 # --- 表单区域 ---
 self.username_input: Locator = page.get_by_test_id("input-username") # 用户名输入框
 self.password_input: Locator = page.get_by_test_id("input-password") # 密码输入框
 self.submit_button: Locator = page.get_by_test_id("btn-login") # 登录按钮
 # --- 反馈区域 ---
 # TODO: 请开发添加 data-testid="login-error"
 self.error_message: Locator = page.locator("[role='alert'].login-error") # 错误提示

 def open(self, base_url: str) -> None:
 """导航到登录页。"""
 logger.info(f"Navigating to login page: {base_url}{self.URL_PATH}")
 self.page.goto(self.URL_PATH)
 self.page.wait_for_url(f"**{self.URL_PATH}")

 def login(self, username: str, password: str) -> None:
 """执行完整登录操作。"""
 logger.info(f"Performing login with username: {username}")
 self.username_input.fill(username)
 self.password_input.fill(password)
 self.submit_button.click()
```

Page Object 规则：
- `__init__` 只声明定位器，不执行操作
- 定位器按 UI 区域用注释分组
- 方法代表用户意图（`login`、`search`），而非技术动作（`click_button`）
- 操作后 URL 变化：`self.page.wait_for_url("**pattern*")`
- 操作后特定元素出现：`self.result_locator.wait_for(state="visible")`
- **禁止** `wait_for_load_state("networkidle")`

---

### Step 3：生成测试用例

路径：`tests/test_{feature}.py`

占位符解析：

| spec 中的值 | 生成代码 |
|------------|---------|
| `{{config.base_url}}` | `config["base_url"]` |
| `{{config.user.username}}` | `config["user"]["username"]` |
| `{{data.field}}` | `case["field"]` |

#### 普通测试模板（positive / negative）

```python
# tests/test_login.py
import allure
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


@allure.feature("User Authentication")
class TestLogin:
 """登录功能测试集。"""

 @allure.story("Valid login")
 @allure.title("使用有效凭据登录成功")
 def test_tc_login_001(self, page: Page, config: dict) -> None:
 """验证合法用户可成功登录并跳转到 Dashboard。"""
 # Arrange
 login_page = LoginPage(page)
 login_page.open(config["base_url"])

 # Act
 login_page.login(
 username=config["user"]["username"],
 password=config…d"],
 )

 # Assert
 expect(page).to_have_url(f"{config['base_url']}/dashboard")
 dashboard_page = DashboardPage(page)
 expect(dashboard_page.welcome_heading).to_be_visible()

 @allure.story("Invalid login")
 @allure.title("使用错误密码时显示错误提示")
 def test_tc_login_002(self, page: Page, config: dict) -> None:
 """验证错误密码触发错误提示且不跳转。"""
 # Arrange
 login_page = LoginPage(page)
 login_page.open(config["base_url"])

 # Act
 login_page.login(username=config["user"]["username"], password="wrong…al")

 # Assert
 expect(login_page.error_message).to_be_visible()
 expect(page).to_have_url(f"{config['base_url']}/login")
```

#### 参数化测试模板（type: parametrize）

spec 中 `type: parametrize` 的场景必须带 `test_data` 字段：

```yaml
# spec.yaml 示例（参数化场景）
- id: TC_LOGIN_INVALID
  story: "Invalid login"
  title: "无效凭据登录失败停留在登录页"
  type: parametrize
  test_data:
    filename: "invalid_login_cases.json"
    sample_data:
      - { username: "valid@test.com", password: "wrong_pass", description: "密码错误" }
      - { username: "", password: "valid_pass", description: "用户名为空" }
      - { username: "valid@test.com", password: "", description: "密码为空" }
  actions:
    - { step: 1, action: navigate, target_page: LoginPage }
    - { step: 2, action: fill, page: LoginPage, element: username_input, value: "{{data.username}}" }
    - { step: 3, action: fill, page: LoginPage, element: password_input, value: "{{data.password}}" }
    - { step: 4, action: click, page: LoginPage, element: submit_button }
  assertions:
    - { type: url, expected: "{{config.base_url}}/", note: "登录失败不应跳转" }
```

**生成数据文件**：从 `sample_data` 提取内容写入 `data/{feature}/{filename}`：

```json
[
  { "username": "valid@test.com", "password": "wrong_pass", "description": "密码错误" },
  { "username": "", "password": "valid_pass", "description": "用户名为空" },
  { "username": "valid@test.com", "password": "", "description": "密码为空" }
]
```

**生成测试代码**：用 `description` 字段作为 pytest `ids` 参数，让测试名称可读：

```python
from utils.test_data_loader import load_test_data

_INVALID_LOGIN_CASES = load_test_data("login", "invalid_login_cases.json")


@allure.feature("User Authentication")
class TestLogin:

 @allure.story("Invalid login")
 @allure.title("无效凭据登录失败停留在登录页")
 @pytest.mark.parametrize(
 "case",
 _INVALID_LOGIN_CASES,
 ids=[c["description"] for c in _INVALID_LOGIN_CASES],
 )
 def test_tc_login_invalid(self, page: Page, config: dict, case: dict) -> None:
 # Arrange
 login_page = LoginPage(page)
 login_page.open(config["base_url"])

 # Act
 login_page.login(username=case["username"], password=case["password"])

 # Assert
 expect(page).to_have_url(f"{config['base_url']}/")
```

测试规则：
- 每个测试必须有 `# Arrange`、`# Act`、`# Assert` 三段注释
- 一个测试只验证一个行为
- 参数化数据在模块级加载（pytest 收集阶段执行）

---

### Step 4：测试运行验证

```bash
# macOS / Linux（本项目环境）
venv/bin/python -m pytest tests/test_{feature}.py -v
```

测试结果处理：
- **全部通过** → 展示成功消息，列出生成的文件路径
- **有失败** → 汇总给用户：失败用例名 + 断言错误（期望 vs 实际）+ 相关 locator 代码行

---

## 注意事项

### 关于现有 Page Object 的兼容

生成前先检查目标文件是否已存在：

```bash
# Step 2 执行前检查
ls pages/{feature}_page.py 2>/dev/null
```

| 文件状态 | 处理方式 |
|---------|---------|
| **文件不存在** | 按模板新建 |
| **文件已存在** | 读取现有文件，执行增量合并（见下方规则） |

**增量合并规则（文件已存在时）：**

1. **新增元素**：spec 中有、现有 POM 中无的元素 → 追加到 `__init__` 对应区域末尾
2. **保留现有元素**：现有 POM 中已有的元素（按属性名匹配） → 原样保留，不覆盖 locator 实现
3. **新增方法**：spec 中涉及、现有 POM 中无对应方法 → 追加到类末尾
4. **保留现有方法**：现有方法原样保留，不重写
5. **不删除任何现有内容**：现有元素/方法可能被其他测试引用

合并完成后，在输出摘要中列出：
- 新增的元素名（`+ element_name`）
- 新增的方法名（`+ method_name`）
- 跳过的已有元素（`= element_name (kept)`）

### test_data_loader 不存在时
若 `utils/test_data_loader.py` 不存在，先生成该文件：

```python
# utils/test_data_loader.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def load_test_data(feature: str, filename: str) -> list[dict]:
 """从 data/{feature}/{filename} 加载测试数据。"""
 path = DATA_DIR / feature / filename
 logger.info(f"Loading test data from {path}")
 with path.open(encoding="utf-8") as f:
 return json.load(f)
```

### spec 中 `test_data` 字段存在时

**`data/` 目录和 JSON 数据文件由 Generator 独占创建，Planner 不写数据文件。**

读取 spec 中场景的 `test_data.sample_data`，写入 `data/{feature}/{filename}`：

```bash
mkdir -p data/{feature}/
```

- 若 spec 包含 `sample_data`：直接提取内容写入 JSON 文件
- 若 spec 无 `sample_data`：生成含 2 条占位数据的空模板，提示用户补充