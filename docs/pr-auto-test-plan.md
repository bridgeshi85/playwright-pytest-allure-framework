# PR Auto-Test：基于 Diff 的自动化测试生成

> 状态：**Draft / Plan**
> 创建：2026-07-29
> 分支：`feat/pr-diff-auto-test-workflow`

---

## 1. 目标

在**前端 PR 创建/更新**时，自动完成：

1. 提取 PR diff → 结构化变更描述（哪些组件/函数/路由/UI 元素被改动）
2. 分析变更对已有测试的影响 → 生成或更新 `specs/{feature}_spec.yaml`
3. 基于 spec 生成/更新 POM + 测试代码
4. 运行 pytest 验证 → 将结果评论到 PR
5. 若测试通过，提交代码到 PR 分支（或开新 PR）

**核心价值**：PR 创建后即刻拥有针对本次变更的回归测试，缩短"代码→测试"反馈环。

---

## 2. 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Action Workflow (pr-auto-test.yml)                      │
│  trigger: pull_request (opened / synchronize / reopened)        │
│  filter: paths → demo-frontend/**                               │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 1: 获取 Diff                │
│  gh pr diff $PR_NUMBER            │
│  → /tmp/pr.diff                   │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 2: diff_parser.py           │  ← 确定性脚本（Python）
│  输入: pr.diff                    │
│  输出: change_manifest.json       │
│  - changed_files[]                │
│  - changed_components[]           │
│  - changed_functions[]            │
│  - affected_routes[]              │
│  - affected_ui_elements[]         │
│  - impact_summary (text)          │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 3: claude -p (Skill A)      │  ← headless Claude Code
│  "pr-test-analyzer"               │
│  输入: change_manifest.json       │
│       + 现有 specs/ 目录          │
│       + pages/ 目录               │
│  输出: specs/{feature}_spec.yaml  │
│       (新建 or 增量更新)          │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 4: claude -p (Skill B)      │  ← headless Claude Code
│  "playwright-test-generator"      │  ← 复用现有 Skill
│  输入: specs/{feature}_spec.yaml  │
│  输出: pages/*.py + tests/*.py    │
│       + data/*.json               │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 5: pytest 验证              │
│  venv/bin/python -m pytest        │
│  结果 → PR comment (gh pr comment)│
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Step 6: 提交代码                 │
│  git add / commit / push          │
│  → 推送到 PR 源分支               │
│  或: gh pr create (新 PR)         │
└───────────────────────────────────┘
```

---

## 3. 组件设计

### 3.1 diff_parser.py（确定性脚本）

**位置**：`scripts/diff_parser.py`

**职责**：解析 unified diff，提取结构化变更信息。**不做任何 AI 推理**，纯正则/AST 解析。

**输入**：
- `--diff-file /tmp/pr.diff`（或 stdin）
- `--project-root demo-frontend/`（限定解析范围）

**输出**：`change_manifest.json`

```json
{
  "pr_number": 42,
  "base_branch": "main",
  "changed_files": [
    {
      "path": "demo-frontend/src/components/LoginForm.tsx",
      "change_type": "modified",
      "additions": 15,
      "deletions": 3
    }
  ],
  "changed_components": ["LoginForm", "ErrorMessage"],
  "changed_functions": [
    {
      "file": "src/components/LoginForm.tsx",
      "name": "handleSubmit",
      "change_type": "modified"
    }
  ],
  "affected_routes": ["/login"],
  "affected_ui_elements": [
    {
      "component": "LoginForm",
      "element_type": "form",
      "testid": "input-username",
      "change": "validation logic modified"
    }
  ],
  "impact_summary": "登录表单的提交逻辑和错误提示组件被修改，影响 /login 路由"
}
```

**解析策略**：
- 文件级：从 diff header 提取路径和变更类型
- 组件级：正则匹配 React 组件声明（`function Xxx` / `const Xxx =` / `export default`）
- 函数级：正则匹配函数/方法定义，结合 hunk header (`@@ ... @@`) 定位变更所在函数
- 路由级：扫描 `router` / `routes` 配置文件中的路径变更
- UI 元素级：正则匹配 `data-testid`、`placeholder`、`aria-label` 属性的增删改

**复用**：此脚本同时服务于：
- 本 workflow（CI 环境）
- 本地评测 Python agent（`python scripts/diff_parser.py < pr.diff`）

---

### 3.2 Skill A: pr-test-analyzer（新建）

**位置**：`playwright-automation-test/.claude/skills/pr-test-analyzer/SKILL.md`

**职责**：读取 `change_manifest.json` + 现有代码上下文 → 决定测试策略 → 输出/更新 spec.yaml

**工作流**：

```
Step 1: 读取 change_manifest.json
Step 2: 扫描现有 specs/ 目录，匹配受影响的 feature
Step 3: 对每个受影响的 feature：
        - 已有 spec → 增量更新（新增/修改受影响的 scenarios）
        - 无 spec → 基于变更范围新建（仅覆盖变更涉及的功能）
Step 4: 输出 specs/{feature}_spec.yaml
Step 5: 输出变更摘要（供 PR comment 使用）
```

**与现有 planner skill 的区别**：

| 维度 | playwright-test-planner | pr-test-analyzer |
|------|------------------------|------------------|
| 触发方式 | 人工交互 | CI 自动（headless） |
| 输入 | URL + 用户描述 | change_manifest.json |
| 页面探索 | 需要 Playwright MCP 实时快照 | **不做浏览器探索**，基于 diff + 已有代码推断 |
| 覆盖范围 | 全页面/全功能 | 仅变更影响范围 |
| 交互确认 | 需要用户确认场景 | 无交互，自动决策 |
| 输出 | 全新 spec | 新建 or 增量 patch |

**关键设计决策**：
- **不做浏览器探索**：CI 环境没有运行中的前端（或可选择启动），analyzer 基于 diff 语义 + 已有 POM/spec 推断测试场景
- **保守策略**：只生成高置信度的测试场景；不确定的标记为 `confidence: low`，在 PR comment 中提示人工 review
- **幂等性**：同一 diff 多次运行，spec 输出一致

**可选增强（Phase 2）**：
- 在 CI 中启动 demo-frontend，让 analyzer 调用 Playwright MCP 做真实快照验证
- 结合 git blame 分析变更频率，对高频变更区域增加测试密度

---

### 3.3 Skill B: playwright-test-generator（复用现有）

**无需修改**，直接复用。CI 中通过 `claude -p` 触发：

```bash
claude -p "读取 specs/{feature}_spec.yaml，使用 playwright-test-generator skill 生成代码" \
  --allowedTools "Read,Write,Bash" \
  --max-turns 20
```

现有 generator 已支持：
- 增量合并（文件已存在时不覆盖）
- pytest 验证
- 参数化数据文件生成

---

### 3.4 GitHub Action Workflow

**位置**：`.github/workflows/pr-auto-test.yml`

**触发条件**：

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
    paths:
      - 'demo-frontend/**'  # 仅前端变更触发
```

**权限**：

```yaml
permissions:
  contents: write      # push 代码到 PR 分支
  pull-requests: write # 评论 PR
  id-token: write
```

**Jobs 设计**：

```yaml
jobs:
  analyze-and-generate:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      # 1. Checkout（完整历史，用于 diff）
      # 2. Setup Python + Node
      # 3. 获取 PR diff → /tmp/pr.diff
      # 4. 运行 diff_parser.py → change_manifest.json
      # 5. 判断是否有可测试变更（无则提前退出）
      # 6. claude -p: pr-test-analyzer → spec.yaml
      # 7. claude -p: playwright-test-generator → code
      # 8. pytest 验证
      # 9. gh pr comment（结果摘要）
      # 10. git commit + push（若测试通过）
```

**Claude CLI 调用方式**：

```bash
# Step 6: 分析变更 → 生成 spec
claude -p "$(cat <<'EOF'
你是 pr-test-analyzer。请读取 change_manifest.json，分析变更影响，
按照 .claude/skills/pr-test-analyzer/SKILL.md 的流程生成/更新 spec。
EOF
)" \
  --allowedTools "Read,Write,Bash" \
  --max-turns 15 \
  --output-format json

# Step 7: spec → 代码
claude -p "读取 specs/ 下本次变更的 spec 文件，使用 playwright-test-generator 生成代码" \
  --allowedTools "Read,Write,Bash" \
  --max-turns 20 \
  --output-format json
```

**Secrets**：

| Secret | 用途 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude CLI 认证 |
| `GITHUB_TOKEN` | 自动注入，用于 gh 命令 |

---

## 4. 数据流

```
PR opened/synchronize
       │
       ▼
gh pr diff → pr.diff (unified diff text)
       │
       ▼
diff_parser.py → change_manifest.json (structured)
       │
       ▼
pr-test-analyzer (claude -p)
  reads: change_manifest.json
  reads: specs/*.yaml (existing)
  reads: pages/*.py (existing POM)
  reads: demo-frontend/src/** (changed source)
  writes: specs/{feature}_spec.yaml (new/updated)
       │
       ▼
playwright-test-generator (claude -p)
  reads: specs/{feature}_spec.yaml
  writes: pages/{feature}_page.py
  writes: tests/test_{feature}.py
  writes: data/{feature}/*.json
       │
       ▼
pytest → pass/fail
       │
       ├── pass → git push to PR branch + PR comment ✅
       └── fail → PR comment ❌ (不推送，附失败详情)
```

---

## 5. 安全与约束

### 5.1 权限最小化

- Claude CLI `--allowedTools` 仅开放 `Read,Write,Bash`
- Bash 工具通过 `--disallowedTools` 禁止网络访问（除 pytest 需要的本地服务）
- Workflow 的 `GITHUB_TOKEN` 权限限定为 `contents:write` + `pull-requests:write`

### 5.2 防止无限循环

- Workflow 触发条件排除 bot 自身的 commit：
  ```yaml
  # 在 step 中检查
  if: github.actor != 'github-actions[bot]'
  ```
- 或使用 `[skip ci]` / `[auto-test]` commit message 标记

### 5.3 成本控制

- `--max-turns` 限制 Claude 对话轮数
- diff_parser 预过滤：纯样式/文档变更直接跳过，不触发 AI
- 单次 workflow 最多处理 3 个 feature 的 spec（超出则截断 + 提示）

### 5.4 代码质量门禁

- 生成的代码必须通过 pylint（≥8.0）
- pytest 全部通过才推送
- PR comment 中标注"此代码由 AI 生成，需人工 review"

---

## 6. 与现有 CI 的关系

| Workflow | 触发 | 职责 |
|----------|------|------|
| `pr-test-and-report.yml`（已有） | PR + push main | 运行**已有**测试 + Allure 报告 |
| `pylint-check.yml`（已有） | PR | 代码风格检查 |
| `pr-auto-test.yml`（新增） | PR（前端路径） | **生成新测试** + 提交 |

执行顺序：`pr-auto-test` 先跑（生成测试）→ 推送后自动触发 `pr-test-and-report`（验证全部测试）。

---

## 7. 实施阶段

### Phase 1: 基础设施（本 PR）
- [x] 创建分支 + plan 文件
- [ ] `scripts/diff_parser.py` — 基础版（文件级 + 组件级解析）
- [ ] `.github/workflows/pr-auto-test.yml` — 骨架（diff → parse → 输出 manifest）
- [ ] 验证：手动 PR 触发，确认 manifest 输出正确

### Phase 2: Skill A 开发
- [ ] `pr-test-analyzer` SKILL.md 编写
- [ ] 本地用 `claude -p` 验证：给定 manifest → 输出合理 spec
- [ ] 增量更新逻辑：已有 spec 的 merge 策略
- [ ] 评测：用历史 PR diff 做回归测试

### Phase 3: 端到端集成
- [ ] Workflow 完整串联（diff → parse → analyze → generate → test → push）
- [ ] PR comment 格式化（变更摘要 + 测试结果 + 生成文件列表）
- [ ] 防循环 + 成本控制机制
- [ ] 文档更新（README + CLAUDE.md）

### Phase 4: 增强（可选）
- [ ] CI 中启动 demo-frontend，analyzer 做真实快照验证
- [ ] 支持多前端项目（不限于 demo-frontend）
- [ ] 测试覆盖率 diff 报告
- [ ] 失败自动重试 + triaging skill 联动

---

## 8. 开放问题

| # | 问题 | 当前倾向 | 备注 |
|---|------|---------|------|
| 1 | analyzer 是否需要浏览器探索？ | Phase 1 不需要，Phase 4 可选 | CI 启动前端增加 ~30s |
| 2 | 生成的代码推送到 PR 源分支 vs 开新 PR？ | 推送到源分支（减少 PR 噪音） | 需要 fork 场景下不可行 |
| 3 | 多个 feature 受影响时并行 vs 串行？ | 串行（简单可靠） | 并行需处理 spec 冲突 |
| 4 | diff_parser 是否需要 AST 解析（ts-morph）？ | Phase 1 正则够用 | 复杂重构场景再引入 |
| 5 | Claude CLI 版本锁定？ | 锁定 major version | 避免 breaking change |
| 6 | 是否需要人工审批门（environment protection）？ | Phase 1 不需要 | 信任度建立后可移除 |

---

## 9. 文件清单（预期最终状态）

```
playwright-pytest-allure-framework/
├── .github/workflows/
│   ├── pr-auto-test.yml          ← 新增
│   ├── pr-test-and-report.yml    ← 已有
│   └── pylint-check.yml          ← 已有
├── scripts/
│   └── diff_parser.py            ← 新增
├── docs/
│   └── pr-auto-test-plan.md      ← 本文件
├── playwright-automation-test/
│   ├── .claude/skills/
│   │   ├── pr-test-analyzer/     ← 新增 Skill A
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   │       └── manifest-schema.md
│   │   ├── playwright-test-generator/  ← 已有，复用
│   │   ├── playwright-test-planner/    ← 已有，不变
│   │   └── triaging-e2e-failures/      ← 已有，不变
│   ├── specs/                    ← analyzer 输出目标
│   ├── pages/                    ← generator 输出目标
│   ├── tests/                    ← generator 输出目标
│   └── data/                     ← generator 输出目标
└── demo-frontend/                ← 被测前端（PR diff 来源）
```

---

## 10. 设计原则

1. **确定性优先**：能用脚本做的（diff 解析、文件匹配）不用 AI
2. **AI 做判断**：影响分析、场景设计、代码生成交给 Claude
3. **复用 > 重写**：generator skill 原样复用，不造新轮子
4. **可观测**：每步输出中间产物（manifest、spec、test result），失败可定位
5. **保守生成**：宁可少生成、不生成错误测试；不确定的交给人
6. **幂等安全**：同一 PR 多次触发不产生重复代码