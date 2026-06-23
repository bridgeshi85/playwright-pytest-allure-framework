# CLAUDE.md — Playwright Automation Test Project

> Claude Code 自动加载此文件作为本子项目的全局约束。

---

## 项目结构

```
playwright-automation-test/
├── configs/ # 环境配置（env.default.yaml 等）
├── fixtures/ # pytest fixtures（browser_fixture, report_fixture）
├── pages/ # Page Object Model 类
├── tests/ # 测试用例
├── utils/ # 工具函数
├── data/ # 参数化测试数据（JSON）
├── specs/ # planner 生成的 spec.yaml（中间产物）
├── .claude/skills/ # Claude Code Skills
│ ├── triaging-e2e-failures/ # E2E 失败根因分析
│ ├── playwright-test-planner/ # 页面探索 → spec.yaml
│ └── playwright-test-generator/ # spec.yaml → POM + 测试代码
└── conftest.py
```

---

## Python 编码规范（强制）

### 风格（PEP 8）
- 4 个空格缩进；禁止混用 tab 和空格；每行最长 79 字符
- 函数/方法/变量用 `snake_case`；类用 `PascalCase`；模块级常量用 `UPPER_CASE`
- 方法之间空 1 行；顶层定义之间空 2 行

### Pythonic 写法
- 文件 I/O 和资源管理必须用 `with`
- 优先使用 f-string，不用 `%` 或 `.format()`
- 真值判断：`if items:` 不写 `if len(items) > 0:`；`if x is None:` 不写 `if x == None:`
- 简单单行转换用列表推导式；逻辑超过一行改用普通 for 循环
- 魔法数字必须命名为常量

### 类型注解与安全
- 所有函数签名必须注解参数和返回类型
- 使用内置泛型（`list[dict]`、`dict[str, str]`），不用 `typing.List` / `typing.Dict`（Python 3.9+）
- 禁止裸 `except:`，必须指定异常类型
- 诊断输出使用 `logging`，库代码和测试代码禁止 `print()`
- 脚本入口必须用 `if __name__ == "__main__":`

---

## Playwright 测试规范（强制）

### 框架约定
- 测试框架：`pytest`
- 报告：`allure`（`@allure.feature` / `@allure.story` / `@allure.title` 必须有）
- Playwright API：仅用 `playwright.sync_api`；**禁止 `async`**
- 执行测试：`venv/bin/python -m pytest ...`（使用项目 venv，不用全局 Python）

### Locator 优先级（严格遵守）

| 优先级 | 策略 | 代码 |
|--------|------|------|
| 1 | `data-testid` | `page.get_by_test_id("value")` |
| 2 | 稳定 `id` | `page.locator("#stable-id")` |
| 3 | `placeholder` | `page.get_by_placeholder("value")` |
| 4 | 语义 CSS 组合 | `page.locator("tag[attr=val]")`（≤3 层，≤3 属性）|
| 5 | 文本（仅表格单元格）| `page.get_by_text("value", exact=True)` |

### 绝对禁止项
- ❌ XPath
- ❌ `time.sleep()` 等硬等待
- ❌ `page.wait_for_load_state("networkidle")`
- ❌ `assert locator.is_visible()`，必须用 `expect(locator).to_be_visible()`
- ❌ Page Object 中使用 `expect`（断言只属于测试层）
- ❌ 测试文件中直接操作 `page.locator()`（定位器封装在 Page Object）
- ❌ 动态 class（哈希后缀）、样式类（`btn-primary`）、动态 id（含数字后缀）

### 测试结构
- 每个测试必须有 `# Arrange`、`# Act`、`# Assert` 三段注释
- 一个测试只验证一个行为；测试间完全独立
- 环境配置通过 `config` fixture 获取（来自 `configs/env.{env}.yaml`）

---

## Skills 使用

本目录包含三个 Claude Code Skills，按以下场景触发：

| 场景 | Skill |
|------|-------|
| 分析 E2E 失败、trace、生成根因报告 | `triaging-e2e-failures` |
| 探索页面结构、生成 spec.yaml | `playwright-test-planner` |
| 读 spec.yaml、生成 POM + 测试代码 | `playwright-test-generator` |

典型工作流：`playwright-test-planner` → 确认 spec → `playwright-test-generator`