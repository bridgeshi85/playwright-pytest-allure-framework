# Triaging E2E Failures — AI Skill

> **触发词**：`分析E2E失败`、`分析trace`、`分析playwright失败`、`生成根因报告`、`请分析测试结果`
> **适用**：本仓库 `playwright-automation-test/` 下的 Playwright + pytest 用例

---

## 输入数据目录

测试运行后，失败证据自动保存在以下三个目录（路径均相对于 `playwright-automation-test/`）：

| 目录 | 内容 | 说明 |
|------|------|------|
| `output/logs/test.log` | pytest 日志，含所有用例的 TEST START/END 及自定义日志 | 单文件，累积追加；按用例名筛选片段 |
| `output/traces/<YYYY-MM-DD-序号>/` | Playwright trace.zip，含 action 序列 + console errors | 每次运行一个子目录，每用例一个 zip |
| `output/screenshots/<YYYY-MM-DD-序号>/` | 失败时的 HTML + PNG | 与 traces 目录编号一一对应 |

> 三类数据分工互补：日志提供测试级上下文，trace 提供 Playwright action 序列，HTML 提供失败瞬间真实 DOM。

---

## 工作流总览

| 步骤 | 执行者 | 工具/参考 | 输出 |
|------|--------|-----------|------|
| **Step 1** 收集 | Python 脚本+ 日志读取 | `parse_trace.py` + `extract_dom.py` + `test.log` | 文本摘要（trace）+ 清洁 DOM（HTML）+ 日志片段 |
| **Step 2** 分类 | AI 推理 | `references/triage_rules.md` | 类别 + 置信度 + 关键证据 |
| **Step 3** 报告 | AI 生成 | `assets/report_template.md` | 标准化 Markdown 根因报告（汇总表） |
| **Step 4** 修复 | AI 推理（可选） | `references/fix_patterns.md` | 可执行修复代码（仅 flaky_element） |

> 脚本只做纯机械解析，AI 完成所有推理和输出。

---

## 执行流程

### Step 1：收集失败证据（工具调用）

**1a. 枚举所有失败目录**

```bash
ls playwright-automation-test/output/traces/
ls playwright-automation-test/output/screenshots/
```

**默认分析全部目录中的全部失败用例**，不限于最新一次运行。
若用户指定了范围（如"只看今天"或"只看 2026-06-08-3"），按指定范围过滤；否则遍历所有子目录。

**1b. 解析 trace → 提取 action 序列 + console errors**

对每个失败用例（traces 目录下每个 .zip）执行（从项目根 `pw-pytest-allure/` 运行）：

```bash
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py \
    playwright-automation-test/output/traces/<YYYY-MM-DD-序号>/<test_name>.zip
```

输出包含：
- 总 action 数 + 当前页面 URL
- 失败 action（api_name、selector、error message）
- 失败前最后 N 个 actions
- Browser console errors

**1c. 提取 HTML → 清洁 DOM（去除 CSS/JS 噪音）**

对应 screenshots 目录下的同名 .html 文件：

```bash
python .claude/skills/triaging-e2e-failures/scripts/extract_dom.py \
    playwright-automation-test/output/screenshots/<YYYY-MM-DD-序号>/<test_name>.html
```

输出 `#root` div 内容（或 `<body>` fallback），保留 `data-testid` 属性，去除所有 `<style>` / `<script>`。

**1d. 从日志中筛选对应用例片段**

日志文件固定为 `output/logs/test.log`，包含所有用例的连续日志。
按用例名从 `=== TEST START: <name> ===` 到 `=== TEST END: <name> [FAILED] ===` 截取片段：

```bash
# 示例：提取单个用例的日志片段
grep -A 50 "TEST START: test_profile_edit_button_not_found" \
    playwright-automation-test/output/logs/test.log | \
    grep -B 0 -m 1 "TEST END: test_profile_edit_button_not_found" -A 0
```

---

### Step 2：读取摘要 → 参照 `references/triage_rules.md` 分类

读取 `.claude/skills/triaging-e2e-failures/references/triage_rules.md`，综合以下三类信息判断：

| 信息来源 | 主要用途 |
|----------|----------|
| trace action 序列 | 确定失败 action 类型（locator / assertion / network）和 selector |
| DOM（extract_dom） | 判断目标元素是否存在、是否延迟渲染、实际 testid 列表 |
| 日志片段 | 补充 Python 级断言错误、实际值/期望值、自定义上下文 |

分类输出：
- 失败类别（`real_bug` / `flaky_test` / `flaky_data` / `unknown`）
- 子类别（`api_failure` / `selector_renamed` / `element_missing` / `delayed_render` / `data_contamination` / `data_setup_missing`）
- 置信度（0.0 ~ 1.0）
- 关键证据列表

**内部推理格式（不直接展示给用户）**：
```json
{
  "category": "flaky_test",
  "sub_category": "element_missing",
  "confidence": 0.87,
  "matched_rule": "Rule 3",
  "reasoning": "失败 action 为 frame.click，selector=[data-testid='btn-edit']，DOM 中仅有 btn-edit-profile 而无 btn-edit",
  "key_evidence": [
    "action: frame.click selector='[data-testid=\"btn-edit\"]' ",
    "error: Timeout 5000ms exceeded",
    "DOM 中存在 data-testid=\"btn-edit-profile\"，不存在 btn-edit"
  ],
  "suggested_fix_selector": "[data-testid=\"btn-edit-profile\"]"
}
```

**置信度 < 0.5 时**：自动分类为 `unknown`。
**置信度 0.5 ~ 0.6 时**：保留分类结论，报告中标注"建议人工复核"。

---

### Step 3：按 `assets/report_template.md` 输出报告

严格遵循 `.claude/skills/triaging-e2e-failures/assets/report_template.md` 模板结构，输出汇总表（每个失败用例一行）。

---

### Step 4：自动修复（可选，需用户确认）

报告输出完毕后，询问用户："是否需要自动修复？"

判断逻辑：
- 置信度 >= 0.7 AND category == `flaky_test` AND sub_category == `selector_renamed`
  → 主动建议自动修复，说明将修改哪个文件的哪一行
- 置信度 >= 0.7 AND category 为其他可修复类型
  → 询问是否需要自动修复，列出将要执行的操作
- 置信度 < 0.7
  → 说明置信度不足，提供修复方案供参考，不主动执行

**询问话术模板**：

> 报告已生成。
>
> **是否需要自动修复？**
> - 分类：`<category>(<sub_category>)`，置信度：**0.xx**
> - 修复内容：将 `<文件路径>` 第 N 行的 `<原 selector>` 替换为 `<新 selector>`
>
> ✅ 置信度 >= 0.7，建议执行自动修复。回复"是"或"执行修复"即可。

若用户确认，执行修复并输出 diff；若用户拒绝或置信度不足，输出修复代码供用户手动应用。

---

## 脚本说明

### `parse_trace.py`

解析 Playwright trace.zip，提取 action 序列 + console errors。

```bash
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py <trace.zip>
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py <trace.zip> --json
```

### `extract_dom.py`

从 `page.content()` 保存的 HTML 中提取 `#root` div，去除 Ant Design CSS-in-JS 注入的样式噪音。

```bash
python .claude/skills/triaging-e2e-failures/scripts/extract_dom.py <html_file>
python .claude/skills/triaging-e2e-failures/scripts/extract_dom.py <html_file> --out clean.html
```

---

## 注意事项

- **默认分析全部失败**：traces 目录下所有子目录中的 .zip 均视为待分析对象，除非用户指定范围。
- trace 目录编号与 screenshots 目录编号一一对应，同一次运行编号相同。
- 日志文件 `output/logs/test.log` 为累积文件，包含所有历史运行；通过 `=== TEST START/END: <name> ===` 定位具体用例片段。
- 若某个用例只有 trace 没有 HTML（测试在 goto 之前失败），直接依赖 trace action 推断，无需调用 extract_dom.py。
- 若 trace 中无明确失败 action，摘要会标注"⚠️ 未检测到明确失败 action"，AI 依赖 console errors 和 HTML DOM 推断。
