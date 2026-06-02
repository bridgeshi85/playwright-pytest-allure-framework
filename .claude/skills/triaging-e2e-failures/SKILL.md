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
- 失败类别（`real_bug` / `flaky_element` / `flaky_data` / `flaky_env` / `unknown`）
- 置信度（0.0 ~ 1.0）
- 关键证据列表

**内部推理格式（不直接展示给用户）**：
```json
{
  "category": "flaky_element",
  "confidence": 0.87,
  "reasoning": "失败 action 为 locator.click，错误为 TimeoutError，DOM 快照中未见目标元素",
  "key_evidence": [
    "action: locator.click selector='#submit-btn'",
    "error: Timeout 30000ms exceeded"
  ]
}
```

**置信度 < 0.6 时**：报告中标注"建议人工复核"。

#### Step 3：生成修复建议（仅 `flaky_element`）

参照 `.claude/skills/triaging-e2e-failures/references/fix_patterns.md`，结合：
- 失败 action 的 `api_name` + `selector`
- 失败前操作序列
- DOM 快照中实际存在的元素（若有）

输出：
1. 根因（中文，≤150 字）
2. 推荐 selector（若原 selector 可优化）
3. 修复代码片段（可直接替换原行）
4. 补充说明（可选）

#### Step 4：按 `assets/report_template.md` 输出报告

严格遵循 `.claude/skills/triaging-e2e-failures/assets/report_template.md` 模板结构，不省略任何一级标题，根据 category 只填写对应的"修复建议"分支。

---

### 场景 B：用户尚未运行测试

先引导运行测试以生成 trace：

```bash
cd playwright-automation-test
pytest tests/<failing_test>.py --env=default
# 失败后 trace 自动保存到 output/traces/<日期-序号>/<test_name>.zip
```

然后走场景 A，trace 路径填写 `playwright-automation-test/output/traces/<日期-序号>/<test_name>.zip`。

---

## 相关文件（项目集成）

```
pw-pytest-allure/
├── .claude/
│   └── skills/
│       └── triaging-e2e-failures/  ← 本 Skill 目录（项目级，随 git 分发）
└── playwright-automation-test/
    ├── output/
    │   ├── traces/                 ← trace.zip 自动生成位置
    │   └── reports/                ← 根因报告输出位置
    ├── utils/
    │   ├── trace_parser.py         ← 兼容垫片（重新导出 skill 实现）
    │   └── ai_failure_analyzer.py  ← 旧 CLI 入口（兼容保留）
    └── fixtures/
        └── browser_fixture.py      ← 测试失败时自动保存 trace.zip
```

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
