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

# Run all tests with default environment
pytest tests/

# Run specific test file
pytest tests/test_login.py

# Run with specific environment configuration
pytest tests/ --env=default

# Run with Allure report generation
pytest tests/ --alluredir=allure-results
allure serve allure-results
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

## 📦 Dependencies

### Python Packages (Test Framework)
- playwright - Browser automation
- pytest - Testing framework
- pytest-playwright - Playwright plugin for pytest
- allure-pytest - Allure reporting integration
- pytest-xdist - Parallel test execution
- pytest-rerunfailures - Retry failed tests
- loguru - Advanced logging
- pyyaml - YAML configuration parsing
- rich - Terminal output formatting
- requests - HTTP client library

### Frontend Dependencies
- React 19 - UI library
- Ant Design - UI components
- Vite - Build tool
- React Router DOM - Routing

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🐛 Troubleshooting

### Common Issues

**Issue**: Tests fail with "browser not found"
```bash
# Solution: Install Playwright browsers
playwright install chromium
```

**Issue**: Cannot connect to frontend in Docker
```bash
# Solution: Ensure containers are on the same network
docker network ls
# Check that e2e-test network exists
```

**Issue**: Permission denied on docker.sock
```bash
# Solution: Add user to docker group (Linux/Mac)
sudo usermod -aG docker $USER
# Then log out and back in
```

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ using Playwright, Pytest, and Allure**
