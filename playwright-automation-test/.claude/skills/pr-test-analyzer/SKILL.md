---
name: pr-test-analyzer
description: >
 读取 diff_parser.py 生成的 change_manifest.json，分析 PR 变更影响，新建或增量更新
 specs/{feature}_spec.yaml。触发词："分析变更"、"pr-test-analyzer"、"根据 diff 生成 spec"、
 "分析 PR 影响"。使用场景：CI（pr-auto-test.yml）headless 调用，无用户交互、不做浏览器探索。
 前置条件：change_manifest.json 已存在（由 scripts/diff_parser.py 生成）。
 完成后：spec 交给 playwright-test-generator skill 生成 POM + 测试代码。
---

# PR Test Analyzer Skill

读取 `change_manifest.json` + 现有 `specs/`/`pages/` + 变更源码 → 决定测试策略 →
新建或增量更新 `specs/{feature}_spec.yaml`。

**你不做浏览器探索、不调用 Playwright MCP、不写 POM/测试代码本身**，只产出/更新 spec.yaml。
spec.yaml 的字段格式必须严格遵守
`../playwright-test-planner/references/spec-schema.md`；`change_manifest.json` 字段含义见
`references/manifest-schema.md`（尤其注意其中"已知局限"一节——正则解析有噪音，不能盲信）。

---

## 与 playwright-test-planner 的区别

| 维度 | playwright-test-planner | pr-test-analyzer |
|------|------------------------|-------------------|
| 触发方式 | 人工交互 | CI 自动（headless，无人确认）|
| 输入 | URL + 用户描述 | change_manifest.json |
| 页面探索 | 需要 Playwright MCP 实时快照 | **不做浏览器探索**，基于 diff + 已有代码推断 |
| 覆盖范围 | 全页面/全功能 | 仅本次 diff 影响的范围 |
| 输出 | 全新 spec | 新建 or 对已有 spec 做增量 patch |

---

## 工作流（严格按步骤执行）

### Step 1：读取输入

```bash
cat /tmp/change_manifest.json   # 或调用方指定的路径
ls playwright-automation-test/specs/ 2>/dev/null
```

若 `change_manifest.json` 不存在或 `changed_files` 为空，直接停止并说明原因（不应该发生，
因为 workflow 已在调用前做过 `changed_files | length == 0` 的短路判断）。

### Step 2：按 feature 分组变更

一个 PR 可能触及多个页面/路由。按以下优先级把 `changed_files` 分组成 feature：

1. `affected_routes[].path` 的最后一段（`/todo` → `todo`）
2. 若无对应路由，用 `changed_components[].file` 所在目录下的页面文件名（去掉扩展名，
   转 `snake_case`，如 `Todo.jsx` → `todo`）
3. 仍无法归类的文件，跳过并在摘要中列为"未识别归属，需人工补充 spec"

对每个 feature，读取实际变更源码（`frontend_root` 下对应文件）确认组件结构和真实的
`data-testid` 等属性——`change_manifest.json` 是正则解析产物，可能有遗漏或误报，**必须以
源码为准**。

### Step 3：决定新建还是增量更新

```bash
ls playwright-automation-test/specs/{feature}_spec.yaml 2>/dev/null
```

| spec 状态 | 处理方式 |
|-----------|---------|
| 不存在 | 按 `spec-schema.md` 新建，只覆盖本次 diff 涉及的元素和场景 |
| 已存在 | 读取现有 spec，增量合并（见下） |

**增量合并规则（spec 已存在时）：**

1. `pages[].elements`：diff 中新增的 UI 元素（来自 `affected_ui_elements`，`change: added`）
   追加到对应 page 的 `elements` 末尾；已有元素保留不动，除非其 `locator_value` 在新代码里
   确实变了才更新
2. `scenarios`：为新增/修改的行为（新组件、新函数、新路由）追加新的 `scenario`，不删除
   已有场景；`change_manifest.json` 里被删除的 UI 元素（`change: deleted`）对应场景标记为
   待人工确认，不自动删除
3. 无法确定改动是否影响现有场景语义时，倾向于**新增场景**而不是修改已有场景

### Step 4：置信度与保守策略

- 只为**高置信度**的变更生成场景：`affected_ui_elements` 里有明确 `testid`/`placeholder`，
  或路由 + 组件双重印证的改动
- 无法从 diff 中确定交互流程（例如只看到函数名变了，猜不出对应哪个用户操作）时，不硬造
  场景，而是在输出摘要里注明"变更 X 无法确定测试场景，建议人工用 playwright-test-planner
  补充"
- 幂等性：同一份 diff 重复运行，输出的 spec 应当一致（不要引入随机顺序/命名）

### Step 5：写入 spec.yaml

路径：`playwright-automation-test/specs/{feature}_spec.yaml`

顶部保留/写入来源标记：

```yaml
# 由 pr-test-analyzer 自动生成（PR #{pr_number}）
meta:
  feature: "{feature}"
  allure_feature: "..."
  generated_by: "pr-test-analyzer"
  base_url: "http://localhost:5173"
```

字段格式（`pages`/`scenarios`/`elements`/`locator_strategy`/`assertions` 等）完全遵守
`../playwright-test-planner/references/spec-schema.md`，不得自创字段。

### Step 6：输出变更摘要

在对话最后输出一段摘要（供 workflow 拼进 PR comment），包含：

- 本次识别到的 feature 列表，及每个 feature 是新建还是增量更新
- 新增/更新的场景数量
- 标记为"低置信度，建议人工确认"的项
- 未能归类的文件（如有）

---

## 安全与约束

- 只读 `change_manifest.json`、`specs/`、`pages/`、`frontend_root` 下的变更源码；不访问网络，
  不启动浏览器
- 不修改 `pages/*.py`、`tests/*.py`——那是 `playwright-test-generator` 的职责
- 不确定的内容宁可留空/标注，不臆造 `data-testid` 或断言
