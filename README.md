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

## 🤖 AI Skill: E2E Failure Root Cause Analysis (Triaging E2E Failures)

This project includes a built-in AI Skill that automatically analyzes failed Playwright test cases, identifies root causes, and generates structured triage reports.

### Trigger Phrases

Use any of the following phrases in your AI conversation to activate the skill:

> `analyze E2E failure` / `analyze trace` / `analyze playwright failure` / `generate root cause report` / `triage test results`

### Workflow

| Step | Description |
|------|-------------|
| **Step 1 — Collect** | Automatically reads `output/traces/`, `output/screenshots/`, and `output/logs/test.log`; parses trace, DOM snapshots, and logs |
| **Step 2 — Classify** | Applies rules from `triage_rules.md` to classify each failure by root cause category and confidence score |
| **Step 3 — Report** | Generates a summary table and per-failure details using the standard template; auto-saves as `e2e-failure-triage-report-<YYYY-MM-DD>.md` |
| **Step 4 — Fix** | For `flaky_test` failures with confidence ≥ 0.7, optionally generates an automated code fix |

### Failure Classification System

| Category | Sub-type | Description |
|----------|----------|-------------|
| `real_bug` | `api_failure` | Backend API returned 4xx/5xx, causing page render failure |
| `real_bug` | `assertion_mismatch` | Assertion expected value does not match actual value |
| `flaky_test` | `selector_renamed` | UI refactor changed a test ID but test code was not updated |
| `flaky_test` | `element_missing` | Element renders late or the feature has been removed |
| `flaky_data` | `data_contamination` | Test data polluted; preconditions not satisfied |
| `unknown` | — | Insufficient evidence; recommend manual inspection via `playwright show-trace` |

### Skill File Structure

```
.claude/skills/triaging-e2e-failures/
├── SKILL.md                        # Skill main instruction (execution flow)
├── assets/
│   └── report_template.md          # Report output template
├── references/
│   ├── triage_rules.md             # Root cause classification rules
│   └── fix_patterns.md             # Automated fix pattern library
└── scripts/
    ├── parse_trace.py              # Parse Playwright trace.zip
    └── extract_dom.py              # Extract HTML DOM at point of failure
```

---

## 🤖 AI Skill: Playwright Test Planner

This skill uses **Playwright MCP** (browser automation) to analyze page structure via accessibility snapshots and generate a language-agnostic test specification (`spec.yaml`). The spec is then consumed by the **Playwright Test Generator** skill to produce code.

### Trigger Phrases

> `分析页面` / `生成 spec` / `帮我规划测试` / `探索这个页面` / `写测试前先分析` / `生成测试规格` / `test planner`

### Workflow

| Step | Description |
|------|-------------|
| **Step 1 — Understand Intent** | Extract feature name, base URL, and user intent from input |
| **Step 2 — Explore Page** | Use Playwright MCP to take an accessibility snapshot; extract all interactive elements with locator strategies (priority: `data-testid` > stable id > placeholder > semantic CSS) |
| **Step 3 — Infer Post-action Pages** | Identify elements that appear after interactions (navigation, modals) and mark them as `post_action` |
| **Step 4 — Design Scenarios** | Generate at least 1 positive (happy path) and 1 negative (error case) scenario with actions and assertions |
| **Step 5 — Output spec.yaml** | Write `specs/{feature}_spec.yaml` containing pages, elements, and scenarios |

### Output

```
playwright-automation-test/
└── specs/
    └── {feature}_spec.yaml    # Language-agnostic test specification
```

### Locator Quality Rules

The planner enforces strict locator quality — dynamic classes, style classes, hash-suffixed IDs, and pure numeric indices are prohibited. When no stable locator is available, the element is marked with `needs_testid: true` so the generator outputs a TODO comment.

### Skill File Structure

```
.claude/skills/playwright-test-planner/
├── SKILL.md                    # Skill instruction (execution flow)
└── references/
    └── spec-schema.md          # spec.yaml field reference
```

---

## 🤖 AI Skill: Playwright Test Generator

This skill reads a `spec.yaml` produced by the **Playwright Test Planner** and generates Page Object Model classes and pytest test cases, then validates them by running pytest in a virtual environment.

### Trigger Phrases

> `生成测试代码` / `根据 spec 生成` / `帮我生成 POM` / `生成测试用例` / `test generator` / `从 spec 生成`

### Workflow

| Step | Description |
|------|-------------|
| **Step 1 — Read Spec** | Parse `specs/{feature}_spec.yaml` — the sole authoritative input |
| **Step 2 — Generate Page Object** | Create `pages/{feature}_page.py` with typed locators, URL_PATH, and action methods |
| **Step 3 — Generate Test Cases** | Create `tests/test_{feature}.py` following Arrange/Act/Assert pattern with Allure decorators |
| **Step 4 — Validate** | Run `pytest tests/test_{feature}.py -v` and report results |

### Output

```
playwright-automation-test/
├── pages/
│   └── {feature}_page.py      # Page Object with typed locators
├── tests/
│   └── test_{feature}.py      # Pytest test cases with Allure annotations
└── data/
    └── {feature}/              # Parameterized test data (if applicable)
```

### Key Conventions

- Every locator gets a one-line inline comment from the spec's `note` field
- Elements with `needs_testid: true` get a `# TODO` comment above the locator
- Each test must contain `# Arrange`, `# Act`, `# Assert` section comments
- Parameterized scenarios generate `@pytest.mark.parametrize` with data loaded at module level
- `wait_for_load_state("networkidle")` is prohibited

### Skill File Structure

```
.claude/skills/playwright-test-generator/
└── SKILL.md                    # Skill instruction (code generation rules)
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
