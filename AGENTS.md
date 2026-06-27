# playwright-pytest-allure-framework

> 此仓库的工程规范集中定义在 `playwright-automation-test/CLAUDE.md`。操作子项目时请优先读取该文件。

---

## 仓库结构

```
playwright-pytest-allure-framework/
├── playwright-automation-test/   ← 主测试项目
│   ├── CLAUDE.md                 ← 编码规范、测试规范、Skills 使用方式
│   ├── configs/                  ← 环境配置
│   ├── fixtures/                 ← pytest fixtures
│   ├── pages/                    ← Page Object Model
│   ├── tests/                    ← 测试用例
│   ├── utils/                    ← 工具函数
│   ├── data/                     ← 参数化数据
│   ├── .claude/skills/           ← Claude Code Skills（triaging / planner / generator）
│   └── conftest.py
├── demo-frontend/                ← 被测前端 demo
├── jenkins/                      ← Jenkins pipeline 配置
├── docker-compose.yml
└── README.md
```

## 核心约束

- 主测试项目为 `playwright-automation-test/`，所有开发工作在该目录下进行
- 编码风格、Python 规范、Playwright 测试规范、Locator 优先级等 **全部定义在 `playwright-automation-test/CLAUDE.md`**，操作前必须读取
- `demo-frontend/`、`jenkins/`、`docker-compose.yml` 为辅助基础设施，不染指非相关变更
- commit message 遵循 conventional commits（`fix:` / `feat:` / `chore:`）
- 代码变更必须附带对应测试
- 不做 spec 范围外的假设性改动，有疑问先确认

## 分支策略

- **禁止直接提交 main 分支**
- 所有修改必须按以下流程：
  1. 从 main 创建新分支（`fix/`、`feat/`、`chore/` 开头）
  2. 完成修改并提交
  3. 推送到 GitHub 后创建 PR
  4. 回复消息告知改动内容并附 PR 链接
- **例外**：如果当前已在其他非 main 分支上工作，可以直接在该分支上提交，无需新建分支或 PR
