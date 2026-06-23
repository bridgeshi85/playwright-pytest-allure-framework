# spec.yaml Schema Reference

## locator_strategy 枚举

| 值 | 生成代码 | 适用条件 |
|----|---------|---------|
| `get_by_test_id` | `page.get_by_test_id("{value}")` | 有 `data-testid` / `testid` |
| `css_id` | `page.locator("#{value}")` | 有稳定、非动态 id |
| `get_by_placeholder` | `page.get_by_placeholder("{value}")` | 输入框有 placeholder |
| `css_combo` | `page.locator("{value}")` | 语义 CSS 组合，≤3 层 |
| `get_by_text` | `page.get_by_text("{value}", exact=True)` | 仅限表格 td/tr 内容定位 |

## scenario type 枚举

| 值 | 说明 | Generator 生成 |
|----|------|---------------|
| `positive` | 正向场景（happy path）| 普通测试函数 |
| `negative` | 负向场景（error case）| 普通测试函数 |
| `parametrize` | 多组数据验证同一功能 | `@pytest.mark.parametrize` |

## 参数化场景完整格式

```yaml
- id: TC_PRODUCT_SEARCH
 story: "Search by name"
 title: "按名称搜索产品"
 type: parametrize
 test_data:
 feature: "product" # 对应 data/product/ 目录
 filename: "search_cases.json" # 数据文件名
 actions:
 - step: 1
 action: navigate
 target_page: ProductListPage
 - step: 2
 action: fill
 page: ProductListPage
 element: name_input
 value: "{{data.keyword}}" # 引用 JSON 中每条的 keyword 字段
 - step: 3
 action: click
 page: ProductListPage
 element: search_button
 assertions:
 - type: conditional # 条件断言：根据数据字段分支
 condition: "{{data.expect_results}}"
 if_true:
 type: not_empty
 page: ProductListPage
 element: table_rows
 if_false:
 type: visible
 page: ProductListPage
 element: table_empty_placeholder
```

## 测试数据文件格式（data/{feature}/{name}_cases.json）

```json
[
 {
 "id": "SEARCH_001",
 "description": "精确匹配已存在产品",
 "keyword": "iPhone",
 "expect_results": true
 },
 {
 "id": "SEARCH_002",
 "description": "搜索不存在的产品返回空",
 "keyword": "xyznotexist",
 "expect_results": false
 }
]
```

每条数据必须包含 `id`（Allure 追溯）和 `description`（可中文）。

## assertion type 枚举

| 值 | 说明 | Generator 生成 |
|----|------|---------------|
| `url` | 页面 URL 断言 | `expect(page).to_have_url(...)` |
| `visible` | 元素可见 | `expect(locator).to_be_visible()` |
| `not_empty` | 元素数量不为 0 | `expect(locator).not_to_have_count(0)` |
| `conditional` | 根据数据字段分支 | `if case["field"]: ... else: ...` |