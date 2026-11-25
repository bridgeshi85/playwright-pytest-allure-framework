### Rule 1 — API 失败 → `real_bug(api_failure)`（高置信度）

**触发条件**（同时满足）：
- `network_failures` 中存在 4xx 或 5xx 记录
- 失败 action 是等待某个元素出现（`api_name` 含 `wait_for` 或 `click`/`fill` 超时）
- `console_errors` 中包含 `fetch failed`、`Failed to load`、`net::ERR_`、`API error` 等网络错误

**判断逻辑**：
```
IF network_failures 存在 AND (4xx 或 5xx) AND 失败元素在 API 响应后才渲染
→ 分类: real_bug / 子类: api_failure
→ 置信度: 0.90
```

**典型证据**：
```
❌ [失败 ACTION]
   api_name  : frame.wait_for  selector: [data-testid="product-list"]
   error     : Timeout 5000ms exceeded.
🌐 [Network failures]
   · GET 404 /api/products
🖥  [Console errors]
   · Failed to load products: API error: 404 Not Found
```

**判断理由模板**：
> API `/api/products` 返回 404，页面 API 错误状态下不渲染商品列表，
> 导致 `[data-testid="product-list"]` 永远不出现。这是环境/后端问题，
> 与测试代码无关。

---

### Rule 2 — Selector 已改名 → `flaky_test(selector_renamed)`（高置信度）

**触发条件**（同时满足）：
- 失败 action 是 locator 操作（`frame.click` / `frame.fill` / `frame.wait_for` 等）
- 失败 `selector` 是 `[data-testid="xxx"]` 格式
- `dom_testids` 中**不存在**该 testid
- `dom_testids` 中存在功能相近的**其他** testid（如 `btn-edit` vs `btn-edit-profile`）
- 无网络失败，无 console 报错

**判断逻辑**：
```
IF 失败 的action使用的selector 不在 dom 中
AND dom 中存在名称相似的 元素
AND 无 network_failures
→ 分类: flaky_test(selector_renamed)
→ 置信度: 0.92
```

**典型证据**：
```
❌ [失败 ACTION]
   api_name  : frame.click  selector: [data-testid="btn-edit"]
   error     : Timeout 5000ms exceeded.
🗂  [失败前页面 data-testid 元素表]
   · <span  data-testid="user-name">   → "admin"
   · <span  data-testid="user-email">  → "admin@example.com"
   · <button data-testid="btn-edit-profile"> → "编辑资料"   ← 实际存在
```

**判断理由模板**：
> 失败 selector `[data-testid="btn-edit"]` 在当前页面 DOM 中不存在。
> 页面实际包含 `[data-testid="btn-edit-profile"]`，功能与期望相同。
> 这是典型的 UI 重构后 testid 更名场景，需要同步更新测试代码。
> 修复方案：将 selector 改为 `[data-testid="btn-edit-profile"]`。

---

### Rule 3 — Selector 不存在 → `flaky_test(element_missing)`（中置信度）

**触发条件**：
- 失败 `selector` 对应的 testid / class 在 `dom_testids` 中找不到
- 也找不到名称相似的替代元素
- 无网络失败

**判断逻辑**：
```
IF 失败 selector 不在 dom_testids 中
AND 无相似替代
AND 无 network_failures
→ 分类: flaky_test(element_missing)
→ 置信度: 0.70（需人工确认是页面删除该功能还是延迟渲染）
```

**判断理由模板**：
> 失败 selector 在当前页面 DOM 中不存在，且无功能相近的替代元素。
> 可能原因：① 该功能/按钮已从页面删除；② 测试导航到了错误的页面；③ 页面延迟渲染导致元素未出现
> 建议用 `playwright show-trace` 查看截图确认页面实际内容。

---

### Rule 4 — 数据问题 → `flaky_data`（中置信度）

**触发条件**（满足任一组合）：
- `error` 含 `AssertionError` 且差异涉及数量或列表内容（如 `expected 3 items, got 2`）
- `assertion_detail` 中同时存在 `expected` 和 `actual` 字段（摘要中 `🔎 [断言差异]` 区块）
- 失败 selector 格式类似 `[data-testid="item-{id}"]` 且 id 是动态值
- `console_errors` 含 `unique constraint`、`duplicate key`、`already exists`
- `network_failures` 中存在 `POST /api/` 的 4xx（如 422 Unprocessable Entity、409 Conflict）

**判断逻辑**：
```
IF assertion_detail 中 expected != actual（明确的值对比）
→ 分类: flaky_data / 子类: data_setup_missing
→ 置信度: 0.85

IF 断言数量/内容不符 AND 无明显 selector 错误
OR 后端 422/409 错误（数据校验/冲突）
→ 分类: flaky_data / 子类: data_contamination 或 data_setup_missing
→ 置信度: 0.70
```

**典型证据**：
```
❌ 错误：AssertionError: expected 3 items, got 2
🌐 [Network failures]
   · POST 422 /api/tasks  （任务已存在，唯一性冲突）
```

**判断理由模板**：
> 后端返回 422 冲突错误，提示数据已存在。
> 这是典型的测试数据污染问题：上次测试运行未清理数据，
> 导致本次测试前置条件不满足。需在 fixture 中增加数据清理逻辑。

---

### Rule 5 — 证据不足 → `unknown`

**触发条件**（满足任一）：
- `total_actions` < 3（trace 极短，可能未完整记录）
- `failed_action` 为空（parse_trace 未检测到失败 action）
- `dom_testids` 为空 且 无 `network_failures` 且 `console_errors` 仅为 antd 警告
- 置信度经上述规则计算后 < 0.5

**判断逻辑**：
```
IF 无法对应上述任一规则 OR 置信度 < 0.5
→ 分类: unknown
→ 置信度: N/A
→ 建议: 人工 `playwright show-trace <trace.zip>` 查看截图
```

---

## 置信度降级规则

以下情况自动将置信度降低 0.15：

| 情况 | 原因 |
|------|------|
| `console_errors` 仅含 antd 废弃警告 | 无害噪音，不影响分类但不能忽略 |
| `dom_testids` 为空 | DOM 提取失败，selector 相关判断不可靠 |
| `total_actions` < 5 | trace 可能不完整 |
| `current_page_url` 为空 | 无法确认失败时所在页面 |

---

## 分类后的固定输出格式

```json
{
  "category": "real_bug",
  "sub_category": "selector_renamed",
  "confidence": 0.92,
  "matched_rule": "Rule 2",
  "reasoning": "...",
  "key_evidence": [
    "失败 selector [data-testid='btn-edit'] 不在当前 DOM 中",
    "DOM 中存在 [data-testid='btn-edit-profile']，功能相同"
  ],
  "suggested_fix_selector": "[data-testid='btn-edit-profile']"
}
```

`suggested_fix_selector` 字段：
- Rule 2（selector 改名）：填写 DOM 中找到的近似替代 selector
- 其他规则：留空或填 `null`

---

## 规则优先级速查

```
network_failures (4xx/5xx) → Rule 1（API 失败）
testid 不在 DOM + 有近似   → Rule 2（selector 改名）  ★ 最易误判
testid 不在 DOM + 无近似   → Rule 3（元素不存在）
422/409 + 数量断言失败     → Rule 4（数据问题）
其他                       → Rule 5（未知）
```

> ⚠️ **最常见误判场景（Rule 2 vs Rule 3）**：
> 同样是 Timeout + locator 失败，区别在于 DOM 快照：
> - DOM 中有相似 testid → Rule 2（`flaky_test`，selector 改名）
> - DOM 中完全没有相关元素 → Rule 3（`flaky_test(element_missing)`，延迟渲染或页面未加载）
> - DOM 提取失败（`dom_testids` 为空）→ 需降低置信度，标注"建议人工复核"
