# Playwright Pytest Allure Framework

A comprehensive end-to-end testing framework built with Playwright, Pytest, and Allure reporting, featuring Docker containerization and Jenkins CI/CD integration.

## 📋 Overview

This project provides a complete test automation solution with:
- **Playwright** for browser automation
- **Pytest** as the testing framework
- **Allure** for beautiful test reporting
- **Docker** for containerized execution
- **Jenkins** for continuous integration
- **React demo application** for testing

## 🏗️ Project Structure

```
.
├── demo-frontend/              # React + Vite demo application (test target)
│   ├── src/                   # Frontend source code
│   ├── Dockerfile             # Frontend container configuration
│   └── package.json           # Frontend dependencies
│
├── playwright-automation-test/ # Test automation framework
│   ├── configs/               # Environment configurations
│   │   ├── env.default.yaml   # Default environment config
│   │   └── env.jenkins.yaml   # Jenkins environment config
│   ├── fixtures/              # Pytest fixtures
│   ├── pages/                 # Page Object Model classes
│   │   ├── login_page.py
│   │   └── home_page.py
│   ├── tests/                 # Test cases
│   ├── utils/                 # Utility functions
│   ├── conftest.py            # Pytest configuration
│   ├── pytest.ini             # Pytest settings
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Test agent container
│
├── jenkins/                   # Jenkins CI/CD configuration
│   ├── Dockerfile             # Jenkins container setup
│   ├── Jenkinsfile            # Pipeline definition
│   └── plugins.txt            # Required Jenkins plugins
│
└── docker-compose.yml         # Multi-container orchestration
```

## 🔧 Prerequisites

- **Docker** and **Docker Compose** (for containerized setup)
- **Python 3.11+** (for local development)
- **Node.js 20+** (for frontend development)

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bridgeshi85/playwright-pytest-allure-framework.git
   cd playwright-pytest-allure-framework
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Jenkins server on `http://localhost:8080`
   - Demo frontend on `http://localhost:3000`

3. **Access the services:**
   - Frontend: http://localhost:3000
   - Jenkins: http://localhost:8080

### Option 2: Local Development

#### Setup Demo Frontend

```bash
cd demo-frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

#### Setup Test Framework

```bash
cd playwright-automation-test
pip install -r requirements.txt
playwright install chromium
```

## 🧪 Running Tests

### Local Execution

```bash
cd playwright-automation-test

# Run with specific environment configuration
pytest tests/ --env=default

```

### Docker Execution

```bash
# Build the test agent image
cd playwright-automation-test
docker build -t playwright-test-agent:latest .

# Run tests in container
docker run --rm \
  --network e2e-test \
  -v $(pwd):/workspace \
  playwright-test-agent:latest \
  pytest tests/test_login.py --env=jenkins
```

## ⚙️ Configuration

### Environment Configuration

Configuration files are located in `playwright-automation-test/configs/`:

- `env.default.yaml` - Local development settings
- `env.jenkins.yaml` - CI/CD environment settings

Example configuration:
```yaml
base_url: "http://localhost:3000"
browser: "chromium"
headless: true
slowmo: 0
```

### Pytest Configuration

Settings in `playwright-automation-test/pytest.ini`:
- Test discovery patterns
- Logging configuration
- Default command-line options

## 📊 Test Reports

This framework uses **Allure** for generating detailed test reports with:
- Test execution history
- Screenshots on failure
- Step-by-step test documentation
- Execution trends and statistics

To generate and view Allure reports:

```bash
# Generate report from results
allure generate allure-results --clean -o allure-report

# Open report in browser
allure serve allure-results
```

## 🔄 CI/CD with Jenkins

### Jenkins Pipeline

The `jenkins/Jenkinsfile` defines a pipeline with:
1. **Checkout** - Pulls the latest code
2. **Run UI Tests** - Executes Playwright tests in Docker agent

### Setup Jenkins

1. Access Jenkins at http://localhost:8080
2. Create a new Pipeline job
3. Point to the `jenkins/Jenkinsfile` in this repository
4. Configure webhook or polling for automatic builds

## 🧩 Key Features

- **Page Object Model (POM)**: Organized page classes for maintainable tests
- **Environment-based Configuration**: Easy switching between test environments
- **Parallel Execution**: Support for running tests in parallel with pytest-xdist
- **Retry Mechanism**: Automatic retry on failures with pytest-rerunfailures
- **Detailed Logging**: Comprehensive logging with loguru and pytest logging
- **Docker Isolation**: Containerized execution for consistency
- **CI/CD Ready**: Jenkins pipeline for automated testing

## 🔍 Test Development

### Writing Tests

Tests follow the Page Object Model pattern:

```python
def test_login_success(page, config):
    login_page = LoginPage(page)
    home_page = HomePage(page)
    
    # Navigate and perform actions
    login_page.goto(config["base_url"])
    login_page.login("admin", "123456")
    
    # Assert expected results
    assert home_page.should_show_welcome_text()
```

### Adding New Tests

1. Create test file in `playwright-automation-test/tests/`
2. Implement page objects in `playwright-automation-test/pages/`
3. Use fixtures from `conftest.py`
4. Follow existing naming conventions

## 🤖 AI Skill：E2E 失败根因分析（Triaging E2E Failures）

本项目内置了一个 AI Skill，用于自动分析 Playwright 失败用例的根因，并生成结构化报告。

### 触发方式

在 AI 对话中使用以下任意触发词：

> `分析E2E失败` / `分析trace` / `分析playwright失败` / `生成根因报告` / `请分析测试结果`

### 工作流

| 步骤 | 说明 |
|------|------|
| **Step 1 收集** | 自动读取 `output/traces/`、`output/screenshots/`、`output/logs/test.log`，解析 trace + DOM + 日志 |
| **Step 2 分类** | 参照 `triage_rules.md` 对每个失败用例进行根因分类，输出类别与置信度 |
| **Step 3 报告** | 按标准模板生成汇总表 + 逐条详情，并自动保存为 `e2e-failure-triage-report-<YYYY-MM-DD>.md` |
| **Step 4 修复** | 置信度 ≥ 0.7 的 `flaky_test` 类失败可选择自动修复代码 |

### 失败分类体系

| 分类 | 子类 | 说明 |
|------|------|------|
| `real_bug` | `api_failure` | 后端接口 4xx/5xx 导致页面无法渲染 |
| `real_bug` | `assertion_mismatch` | 断言期望值与实际值不符 |
| `flaky_test` | `selector_renamed` | UI 重构后 testid 已更名，测试代码未同步 |
| `flaky_test` | `element_missing` | 元素延迟渲染或功能已删除 |
| `flaky_data` | `data_contamination` | 测试数据污染，前置条件不满足 |
| `unknown` | — | 证据不足，建议人工使用 `playwright show-trace` 排查 |

### Skill 文件结构

```
.claude/skills/triaging-e2e-failures/
├── SKILL.md                        # Skill 主指令（执行流程）
├── assets/
│   └── report_template.md          # 报告输出模板
├── references/
│   ├── triage_rules.md             # 根因分类规则
│   └── fix_patterns.md             # 自动修复模式库
└── scripts/
    ├── parse_trace.py              # 解析 Playwright trace.zip
    └── extract_dom.py              # 提取失败瞬间 HTML DOM
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
