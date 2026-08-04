# change_manifest.json Schema Reference

由 `scripts/diff_parser.py` 生成，路径经 workflow 以 `--diff-file` 传入，默认写到
`/tmp/change_manifest.json`。**不做 AI 推理，纯正则解析**，字段可能有噪音（如把非组件
函数误识别为组件），分析时需结合已有代码校验，不能盲信。

## 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `pr_number` | int \| null | PR 编号 |
| `base_branch` | string | 目标分支，默认 `main` |
| `frontend_root` | string | 自动检测的前端项目根目录（相对仓库根，可能为空字符串表示仓库根即前端项目）|
| `is_fork` | bool | 是否来自 fork PR |
| `changed_files` | ChangedFile[] | 变更的前端文件列表 |
| `changed_components` | ChangedComponent[] | 从 diff 中正则提取的组件 |
| `changed_functions` | ChangedFunction[] | 从 diff 中正则提取的函数/方法 |
| `affected_routes` | AffectedRoute[] | 从路由配置文件变更中提取的路径 |
| `affected_ui_elements` | AffectedUIElement[] | `data-testid` / `placeholder` / `aria-label` / `role` 等属性的增删改 |
| `impact_summary` | string | 人类可读的一句话摘要 |

## ChangedFile

```json
{ "path": "demo-frontend/src/pages/Todo.jsx", "change_type": "added", "additions": 151, "deletions": 0 }
```

`change_type`: `added` \| `modified` \| `deleted`（脚本当前不生成 `renamed`）。

## ChangedComponent

```json
{ "name": "Todo", "file": "demo-frontend/src/pages/Todo.jsx", "change_type": "added" }
```

只覆盖 React（`function X(`、`const X = () =>`、`class X extends`、`export default function X`）
和 Vue SFC（文件名首字母大写、`defineComponent({ name: '...' })`）、Svelte（文件名首字母大写）。
不保证覆盖所有真实组件，也可能把非组件的大写标识符误判为组件。

## ChangedFunction

```json
{ "file": "demo-frontend/src/pages/Todo.jsx", "name": "addItem", "change_type": "added", "line_start": 21 }
```

## AffectedRoute

```json
{ "path": "/todo", "file": "demo-frontend/src/App.jsx", "change": "route added or modified" }
```

只在文件名匹配 `router`/`routes`/`App.tsx`/`App.jsx`/`main.tsx`/`main.jsx` 等的文件里扫描
`path="..."` / `path: '...'`，不做真正的路由树解析。

## AffectedUIElement

```json
{ "component": "Todo", "element_type": "testid", "value": "input-todo", "change": "added" }
```

`element_type`: `testid` \| `placeholder` \| `aria-label` \| `role`。
`component` 是从文件名猜的（不一定准确），仅作参考，不要直接当作 spec 里的 `pages` 名称使用——
以 `file` 路径实际读取源码确认组件名。

## 已知局限（分析时必须注意）

- 组件/函数提取基于正则，**不是 AST**，会有漏报和误报（例如把 `if (...)` 之类的模式误判需已在代码里过滤，但仍可能有其他噪音）。
- `affected_ui_elements` 只统计**属性的增删**，不代表元素本身被删除或新增了整个 DOM 节点。
- 一个 PR 可能涉及多个 feature（多个页面/路由），需要按 `changed_files` 的目录/组件分组，
  分别对应到不同的 `specs/{feature}_spec.yaml`。
