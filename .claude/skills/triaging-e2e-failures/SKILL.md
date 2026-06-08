# Triaging E2E Failures — AI Skill

> **触发词**：`分析E2E失败`、`分析trace`、`分析playwright失败`、`生成根因报告`、`请分析测试结果，trace文件是...`  
> **适用**：本仓库 `playwright-automation-test/` 下的 Playwright + pytest 用例

---

## 目录结构

```
.claude/skills/triaging-e2e-failures/
├── SKILL.md                        ← 本文件：编排器，定义 4 步工作流
├── run.sh                          ← 自定位入口脚本（路径无关）
├── scripts/
│   └── parse_trace.py              ← Step 1：确定性解析 trace.zip → 结构化 JSON
├── references/
│   ├── triage_rules.md             ← Step 2：分类规则（假阳性 / 环境问题等）
│   └── fix_patterns.md             ← Step 3：修复建议规则（selector 失效 / 元素不存在等）
└── assets/
    └── report_template.md          ← Step 4：报告模板标准化
```

---

## 工作流总览

| 步骤 | 执行者 | 工具/参考 | 输出 |
|------|--------|-----------|------|
| **Step 1** 解析 | Python 脚本（确定性） | `.claude/skills/triaging-e2e-failures/scripts/parse_trace.py` | 结构化 JSON + 文本摘要 |
| **Step 2** 分类 | AI 推理 | `.claude/skills/triaging-e2e-failures/references/triage_rules.md` | 类别 + 置信度 + 关键证据 |
| **Step 3** 修复 | AI 推理 | `.claude/skills/triaging-e2e-failures/references/fix_patterns.md` | 可执行修复代码（仅 flaky_element） |
| **Step 4** 报告 | AI 生成 | `.claude/skills/triaging-e2e-failures/assets/report_template.md` | 标准化 Markdown 根因报告 |

> 脚本只做纯机械解析，AI 完成所有推理和输出。

---

## 执行流程

### 场景 A：用户给出 trace 路径

**触发示例**：`"请分析测试结果，trace文件是 playwright-automation-test/output/traces/2026-05-26-1/test_login.zip"`

#### Step 1：运行解析脚本（工具调用）

```bash
# 输出文本摘要（供 AI Step 2/3/4 推理）
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py \
    <trace路径> \
    --out playwright-automation-test/output/reports/<name>_summary.txt

# 可选：输出结构化 JSON
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py \
    <trace路径> --json \
    --out playwright-automation-test/output/reports/<name>_trace.json

# 可选：包含 DOM 快照（元素类失败推荐）
python .claude/skills/triaging-e2e-failures/scripts/parse_trace.py \
    <trace路径> --dom \
    --out playwright-automation-test/output/reports/<name>_summary.txt
```

> **路径说明**：上述命令从项目根（`pw-pytest-allure/`）执行，trace 路径和输出路径均相对于项目根。

#### Step 2：读取摘要 → 参照 `references/triage_rules.md` 分类

读取 `.claude/skills/triaging-e2e-failures/references/triage_rules.md`，对上一步生成的摘要判断：
- 失败类别（`real_bug` / `flaky_test` / `flaky_data` / `unknown`）
- 子类别（`api_failure` / `selector_renamed` / `element_missing` / `data_contamination` / `data_setup_missing`）
- 置信度（0.0 ~ 1.0）
- 关键证据列表

**内部推理格式（不直接展示给用户）**：
```json
{
  "category": "flaky_test",
  "sub_category": "element_missing",
  "confidence": 0.87,
  "matched_rule": "Rule 3",
  "reasoning": "失败 action 为 locator.click，错误为 TimeoutError，DOM 快照中未见目标元素且无相似替代",
  "key_evidence": [
    "action: locator.click selector='#submit-btn'",
    "error: Timeout 30000ms exceeded",
    "dom_testids 中不存在 submit-btn 及近似元素"
  ],
  "suggested_fix_selector": null
}
```

**置信度 < 0.5 时**：自动分类为 `unknown`。  
**置信度 0.5 ~ 0.6 时**：保留分类结论，但报告中标注"建议人工复核"。

#### Step 3：按 `assets/report_template.md` 输出报告

严格遵循 `.claude/skills/triaging-e2e-failures/assets/report_template.md` 模板结构，不省略任何一级标题，根据 category 只填写对应的"修复建议"分支。


#### Step 4: 自动修复（可选，需用户确认）
报告输出完毕后，询问用户：

"是否需要自动修复？"

判断逻辑：
- 置信度 >= 0.7 AND category == "flaky_test" AND sub_category == "selector_renamed"
  → 主动建议自动修复，并说明将修改哪个文件的哪一行
- 置信度 >= 0.7 AND category 为其他可修复类型
  → 询问是否需要自动修复，并列出将要执行的操作
- 置信度 < 0.7
  → 说明"当前置信度（0.xx）低于建议阈值 0.7，不建议自动修复，建议人工复核后再决定"
  → 仍然提供修复方案供参考，但不主动执行

**询问话术模板**：

> 报告已生成。
>
> **是否需要自动修复？**
>
> - 分类：`<category>(<sub_category>)`，置信度：**0.xx**
> - 修复内容：将 `<文件路径>` 第 N 行的 `<原 selector>` 替换为 `<新 selector>`
>
> ✅ 置信度 >= 0.7，建议执行自动修复。回复"是"或"执行修复"即可。

若用户确认，执行修复并输出 diff；若用户拒绝或置信度不足，输出修复代码供用户手动应用。

---

## 注意事项

- `build_summary()` 默认不含 DOM（`include_dom=False`），节省 token；元素类失败建议加 `--dom`。
- trace.zip 由测试失败时自动生成，路径格式：`playwright-automation-test/output/traces/<YYYY-MM-DD-序号>/<test_name>.zip`。
- 若 trace 中无明确失败 action，摘要会标注"⚠️ 未检测到明确失败 action"，AI 依赖 console/network 信息推断。
- 编程调用示例：
  ```python
  import sys
  sys.path.insert(0, ".claude/skills/triaging-e2e-failures")
  from scripts.parse_trace import parse_trace, build_summary

  parsed = parse_trace("playwright-automation-test/output/traces/2026-05-26-1/test_login.zip")
  summary = build_summary(parsed, include_dom=True)
  print(summary)
  ```
