# E2E 失败根因分析报告模板

> Step 4 报告模板：AI 填写以下结构并输出 Markdown，禁止省略任何一级标题。

---

```markdown
# 🔍 E2E 失败根因分析报告

> **生成时间**: YYYY-MM-DD HH:MM  
> **Skill 版本**: triaging-e2e-failures v2

---

## 基本信息

| 字段 | 值 |
|------|----|
| **Trace 文件** | `<路径>` |
| **失败 API** | `<api_name>` |
| **失败 Selector** | `<selector>` |
| **错误信息** | `<error message>` |
| **用户代码位置** | `<stack_top>` |
| **总 Action 数** | `<total_actions>` |

---

## 1. 分类结论

- **类别**: `<category>`
- **置信度**: **0.xx**
- **判断依据**: <一句话说明依据来自哪个规则>
- **关键证据**:
  - `<evidence 1>`
  - `<evidence 2>`
  - `<evidence 3（可选）>`

> ⚠️ 置信度 < 0.6 时：请在此处补充"建议人工复核，不确定点：..."

---

## 2. 关键证据

### Console Errors
<!-- 无则填写：无 -->
- `<console error 1>`

### Network Failures
<!-- 无则填写：无 -->
- `<METHOD> <STATUS> <URL>`

### 截图
<!-- 无则填写：无（trace 中未包含截图） -->
- `<trace 内部截图路径>`

### 失败前操作序列（最近 N 步）
<!-- 列出失败前的关键 actions，帮助理解操作上下文 -->
1. `<api_name>` — `<selector>`
2. `<api_name>` — `<selector>`
3. ❌ `<failed_api_name>` — `<selector>` ← 失败点

---

## 3. 根因分析

<!-- 中文，150 字以内，解释"为什么会失败" -->

<根因说明>

---

## 4. 修复建议 / 下一步

<!-- 根据 category 填写对应内容 -->

### flaky_element → 修复代码

**问题所在文件**: `<pages/xxx_page.py 或 tests/xxx.py>`

**原代码**:
```python
# 原来的写法
<original_code_line>
```

**推荐 Selector**（若原 selector 可优化）:
```
<new_selector>
```

**修复代码**:
```python
# 修复后的写法
<fixed_code>
```

**补充说明**（可选）:
> <额外背景说明>

---

### real_bug → 提交缺陷工单

- **现象**: <描述实际行为>
- **预期**: <描述期望行为>
- **复现步骤**: 运行 `pytest <test_path> --env=default`
- **建议优先级**: P<1/2/3>

---

### flaky_data → 数据修复

- **缺失/脏数据**: <描述>
- **修复方案**: <初始化脚本 / 手动配置 / 前置 fixture>

---

### flaky_env → 运维检查

- **疑似原因**: <服务不可用 / 网络超时 / 配置错误>
- **建议**: 检查 `<服务名>` 运行状态，查看 `<日志路径>`

---

### unknown → 人工复核

- **可疑证据**: <列出所有疑点>
- **建议下一步**: 手动打开 trace 文件，执行 `playwright show-trace <trace.zip>`

---

## 5. 预防建议（可选）

<!-- 如果有通用改进建议，在此列出 -->
- [ ] <建议 1>
- [ ] <建议 2>

---

*报告由 AI Skill **triaging-e2e-failures** 自动生成 · 如有疑问请人工复核*
```

