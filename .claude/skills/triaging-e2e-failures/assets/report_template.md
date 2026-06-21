# E2E 失败根因汇总报告模板

> 每次触发 Skill 后，AI 按以下模板输出一份 Markdown 报告。
> 若本次分析包含多个 trace，每个 trace 占表格一行；单个 trace 同样使用此格式。

---

```markdown
# 🔍 E2E 失败根因汇总报告

> 生成时间：YYYY-MM-DD HH:MM  
> 分析用例数：N

---

## 汇总表

| 用例 | 分类 | 置信度 | 失败原因 | 修复方向 | 代码位置 |
|------|------|--------|----------|----------|----------|
| `<test_name>` | `<category/sub_category>` | 0.xx | <一句话说明为什么失败> | <一句话说明如何修> | `<stack_top>` |

> ⚠️ 置信度 < 0.6 的行，在"分类"列后加注 `（建议人工复核）`

---

## 逐条详情

### `<test_name>`

- **分类**：`<category>` / `<sub_category>`  
- **置信度**：0.xx（命中 `<matched_rule>`）  
- **失败原因**：<中文，≤100 字，说清楚"因为什么导致失败">  
- **关键证据**：
  - `<evidence 1>`
  - `<evidence 2>`
- **修复方向**：<具体的修复操作，针对不同分类填写如下>
  - `flaky_test/selector_renamed`：将 `<old_selector>` 替换为 `<suggested_fix_selector>`
  - `flaky_test/element_missing`：运行 `playwright show-trace <trace.zip>` 确认页面实际内容，检查是否延迟渲染或功能已删除
  - `real_bug/api_failure`：检查 `<METHOD> <STATUS> <URL>` 对应的后端接口，提交缺陷工单
  - `flaky_data`：检查 fixture 的数据清理逻辑，确保测试前置条件满足
  - `unknown`：证据不足，建议人工打开 `playwright show-trace <trace.zip>` 排查
- **代码位置**：`<stack_top>`

---

<!-- 下一条用例重复上述结构 -->

---

*报告由 AI Skill **triaging-e2e-failures** 自动生成 · 置信度 < 0.6 建议人工复核*
```

---

## 填写说明

### 汇总表字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| 用例 | `trace 文件名 / 测试函数名` | 去掉路径前缀，只保留函数名 |
| 分类 | Step 2 triage 结果 `category/sub_category` | 格式如 `real_bug/api_failure` |
| 置信度 | Step 2 triage 结果 `confidence` | 保留两位小数 |
| 失败原因 | Step 2 `reasoning` 浓缩 | 一句话，不超过 30 字 |
| 修复方向 | Step 2 `suggested_fix_selector` 或规则模板 | 可操作的动作描述 |
| 代码位置 | `stack_top` 字段 | 格式：`文件名:行号 函数名` |

### 逐条详情触发条件

- 默认输出汇总表 + 所有用例的逐条详情
- 若用例数 > 5，优先展示汇总表；逐条详情仅展示置信度最高和置信度最低（`unknown`）的各一条，其余省略并注明"如需查看完整详情，请单独分析对应 trace"
