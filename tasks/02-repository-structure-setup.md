# Task 02: Repository Structure Setup

**Category:** Project Setup  
**Priority:** High  
**Estimated Effort:** 1-2 hours  
**Status:** Not Started

## Description

Create the proper directory structure for the Home Assistant custom integration following HA conventions and HACS requirements.

## Prerequisites

- **Task 01** completed (Development Environment Setup)
- Git repository initialized

## Objectives

1. Create custom_components directory structure
2. Set up test directory structure
3. Create configuration files
4. Set up documentation structure
5. Configure .gitignore

## Deliverables

- [ ] `custom_components/wiener_netze/` directory created
- [ ] Test directory structure created
- [ ] `.gitignore` configured
- [ ] `LICENSE` file added
- [ ] Basic `README.md` created

## Steps

### 1. Create Custom Components Directory

```bash
mkdir -p custom_components/wiener_netze
```

### 2. Create Test Directory

```bash
mkdir -p tests
touch tests/__init__.py
touch tests/conftest.py
```

### 3. Create Documentation Directory (if not exists)

```bash
mkdir -p dokumentation
```

### 4. Create Initial Files

Create empty placeholder files:

```bash
# Integration files
touch custom_components/wiener_netze/__init__.py
touch custom_components/wiener_netze/manifest.json
touch custom_components/wiener_netze/const.py
touch custom_components/wiener_netze/config_flow.py
touch custom_components/wiener_netze/coordinator.py
touch custom_components/wiener_netze/api.py
touch custom_components/wiener_netze/sensor.py
touch custom_components/wiener_netze/strings.json

# Translation directory
mkdir -p custom_components/wiener_netze/translations
touch custom_components/wiener_netze/translations/en.json
touch custom_components/wiener_netze/translations/de.json

# Test files
touch tests/test_init.py
touch tests/test_config_flow.py
touch tests/test_coordinator.py
touch tests/test_api.py
touch tests/test_sensor.py
```

### 5. Create .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/
dist/
build/

# Home Assistant
config/
.HA_VERSION
home-assistant.log
home-assistant_v2.db
*.db-shm
*.db-wal

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Environment
.env
.env.local

# Temporary files
*.tmp
*.bak
*~
```

### 6. Create LICENSE File

Add AGPL-3.0 license:

```bash
# License already exists in repository
# Verify it's AGPL-3.0
cat LICENSE.md
```

### 7. Create Basic README.md

Create a comprehensive README:

```markdown
# Wiener Netze Smart Meter - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Home Assistant integration for Wiener Netze Smart Meters, providing real-time energy consumption monitoring.

## Features

- Real-time energy consumption data
- 15-minute interval readings
- Daily and meter reading aggregation
- OAuth2 authentication with Wiener Netze API
- Multiple smart meter support
- Device registry integration

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Wiener Netze Smart Meter"
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/wiener_netze` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ ADD INTEGRATION"
3. Search for "Wiener Netze Smart Meter"
4. Follow the configuration steps

## Setup Requirements

- Wiener Netze Smart Meter account
- API credentials from WSTW API Portal
- Active smart meter (Zählpunkt)

For detailed setup instructions, see [SETUP.md](dokumentation/SETUP.md)

## Sensors

The integration provides the following sensors:

- **Current Consumption** - Latest 15-minute reading
- **Daily Consumption** - Daily total consumption
- **Meter Reading** - Current meter reading

## Development

See [DEVELOPMENT_GUIDE.md](dokumentation/HOME_ASSISTANT_PLUGIN_DEVELOPMENT.md) for development documentation.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

The Wiener Netze Smart Meter API is licensed under CC BY-NC-ND 4.0.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/mpwg/WienerNetzeHomeAssist/issues).
```

### 8. Create pyproject.toml for Python Project Configuration

```toml
[tool.black]
target-version = ["py311"]
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | \.mypy_cache
  | \.pytest_cache
  | build
  | dist
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
follow_imports = "silent"
warn_redundant_casts = true
warn_unused_ignores = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = false

[tool.pylint.MASTER]
ignore = [
    "tests",
]

[tool.pylint.BASIC]
good-names = [
    "_",
    "ex",
    "fp",
    "i",
    "id",
    "j",
    "k",
    "Run",
]

[tool.pylint."MESSAGES CONTROL"]
disable = [
    "too-few-public-methods",
    "duplicate-code",
    "format",
    "unsubscriptable-object",
]

[tool.pylint.SIMILARITIES]
ignore-imports = true

[tool.pylint.FORMAT]
max-line-length = 88
```

## Directory Structure

After completion, the structure should look like:

```
WienerNetzeHomeAssist/
├── .git/
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements_dev.txt
├── venv/
├── custom_components/
│   └── wiener_netze/
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── api.py
│       ├── sensor.py
│       ├── strings.json
│       └── translations/
│           ├── en.json
│           └── de.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_init.py
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   ├── test_api.py
│   └── test_sensor.py
├── dokumentation/
│   ├── Export_WN_SMART_METER_API.yaml
│   ├── HOME_ASSISTANT_PLUGIN_DEVELOPMENT.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── ...
└── tasks/
    ├── 00-overview.md
    ├── 01-development-environment-setup.md
    ├── 02-repository-structure-setup.md
    └── ...
```

## Acceptance Criteria

- [ ] All directories created successfully
- [ ] All placeholder files exist
- [ ] `.gitignore` excludes appropriate files
- [ ] README.md contains basic project information
- [ ] `pyproject.toml` configured for Python tools
- [ ] Directory structure matches HA conventions
- [ ] Git status shows only tracked files

## Testing

```bash
# Verify directory structure
tree -L 3 custom_components/
tree -L 2 tests/

# Check .gitignore works
git status

# Verify Python configuration
black --check custom_components/
pylint --version
```

## References

- [Home Assistant Integration Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure)
- [HACS Requirements](https://hacs.xyz/docs/publish/integration/)

## Notes

- Keep custom_components/ directory clean (only integration files)
- Don't commit config/ directory or venv/
- Placeholder files will be populated in subsequent tasks
- pyproject.toml provides IDE and tool configuration

## Next Task

→ **Task 03:** Testing Framework Setup
