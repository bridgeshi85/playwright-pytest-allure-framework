# GitHub Agentic Workflows：E2E 失败诊断 Demo

## 目标与范围

用 Playwright、pytest、GitHub Actions 和 gh-aw（Copilot 引擎）演示从失败证据到分类、一次重跑或建单的流程。Agent 只提交诊断；普通 Actions job 校验并执行预设动作。修复由工程师完成，流水线不改测试断言、Locator 或产品代码。演示场景可在 runner 内临时注入故障，便于复现。

## 复用诊断 Skill

- 将 `triaging-e2e-failures` 迁入 `.github/skills/`，保留脚本、规则和模板。补齐 `name`、`description`，更新现有调用路径或保留兼容入口。
- 在 gh-aw Markdown 中用顶层 `skills:` 声明目录，要求 Agent 使用 Skill 的 CI 模式。CI 模式只读取当前 attempt 的证据，输出用例 ID、原始分类、CI 分类、证据引用和理由。
- 保留原始分类供排障。自动化分类使用 `flaky`、`real_bug`、`environment`、`unknown`。瞬态证据支持 `flaky`，明确违反产品契约支持 `real_bug`，依赖或配置异常归 `environment`。稳定的测试脚本错误或证据不足归 `unknown`。单个超时、404 或模型自报置信度不足以触发自动动作。

## 工作流与处理规则

1. **E2E Demo** 通过 `workflow_dispatch` 选择场景。每次运行一个测试 job，保留 pytest 退出码，按 run ID 和 attempt 关联 JUnit、用例 ID、日志、trace 摘要和 DOM 等证据。场景名和预设分类不进入 Agent 的诊断输入。
2. **AI Triage** 监听指定 Demo workflow 的 `workflow_run.completed`，核对来源仓库、分支、run ID 和 attempt。仅首次失败进入 Copilot 诊断，重跑结果由测试 workflow 汇总。将 gh-aw Markdown 源文件及 `gh aw compile` 生成的 `.lock.yml` 一同提交。
3. **处理诊断** 使用自定义 safe output。可信 job 校验分类、用例 ID 和证据引用，并用 GitHub 事件提供的 run ID 执行动作。诊断缺失、无效或引擎不可用时保留失败，转人工处理。写权限只授予执行重试或建单的 job。
4. **Flaky** 对已完成且仍为首次尝试的原 run 调用 `POST /repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs`。同一 run 的处理串行化。第二次通过标记 `recovered`，仍失败标记 `needs-human` 并停止。
5. **真实问题** 创建 GitHub Issue，写明预期、实际、证据、用例、SHA 和 Actions 链接。以用例 ID 和归一化失败特征查找未关闭 Issue，重复失败补充运行链接。环境问题和未知问题记录在 Actions Summary，附人工检查建议。

参考 [gh-aw Skill 加载](https://github.github.com/gh-aw/reference/faq/) 和 [自定义 Safe Outputs](https://github.github.com/gh-aw/reference/custom-safe-outputs/)。

## 演示与验收

复用 Shop 页面和现有测试基础设施，用独立的手动 Demo 用例。各场景共用商品价格断言。

| 场景 | 证据 | 预期结果 |
| --- | --- | --- |
| 正常基线 | 页面展示 API 返回的价格 | 首次通过，无模型调用 |
| 瞬态失败后恢复 | 首次请求中断，依赖探测恢复 | 同一 run 第二次通过 |
| 重试仍失败 | 重跑再次中断 | 最终保持失败，标记人工处理 |
| 产品回归 | API 返回正确值，页面稳定展示错误值 | 建 Issue，重复运行不重复开单 |
| 环境异常 | 依赖健康检查和业务请求均失败 | Summary 标记环境问题 |
| 证据不足 | 只有等待超时，缺少可区分根因的证据 | Summary 标记未知并转人工 |

额外验收非法诊断输出。已有固定超时和错误断言样例可用来说明误判，不能作为瞬态恢复或产品回归的验收证据。

## 实施顺序与交付

1. 从 `main` 建独立分支和 worktree。固定 gh-aw 版本、配置 Copilot 凭据，编译并用已知 trace 验证 Skill 加载。
2. 优先打通「瞬态失败后恢复」与「产品回归」。在默认分支包含监听 workflow 的演示仓库完成联调，记录两次 attempt、Issue 和诊断 Summary 链接。
3. 按同一 run ID 关联首次执行与重跑结果。Summary 展示近 30 天可用 artifact 中每个用例的「首败后重跑通过次数 ÷ 首次执行总次数」，同时显示分子、分母和统计窗口。人工注入的数据单独标明，该指标表示观察到的重跑恢复率。
4. 验收其余场景和去重。按仓库规范运行 pylint（至少 8.0）和 pytest，单列已有故意失败样例。交付 PR、复现说明、Actions Summary、重跑记录与 Issue 链接。


建议新增的文件
.github/
├── skills/
│   └── triaging-e2e-failures/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── assets/
│
└── workflows/
    ├── e2e-demo.yml
    ├── ai-e2e-triage.md
    └── ai-e2e-triage.lock.yml

playwright-automation-test/
├── tests/
│   └── test_agentic_e2e_demo.py
├── scripts/
│   ├── collect_demo_evidence.py
│   ├── validate_triage.py
│   └── summarize_demo_runs.py
└── demo/
    └── scenarios.py


此外，在 demo-frontend/ 中新增演示专用的商品 API Mock 或服务端点。尽量不修改现有 Shop 的业务逻辑，以减少对其他测试的影响。