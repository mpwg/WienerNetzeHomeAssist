# Task 01: Development Environment Setup

**Category:** Project Setup  
**Priority:** High  
**Estimated Effort:** 2-3 hours  
**Status:** Not Started

## Description

Set up the development environment for Home Assistant custom integration development, including Python environment, dependencies, and Home Assistant core for testing.

## Prerequisites

- macOS system with Homebrew installed
- Python 3.11 or later
- Git installed
- VS Code or preferred IDE

## Objectives

1. Set up Python virtual environment
2. Install Home Assistant core for development
3. Install development dependencies
4. Configure IDE for Python development
5. Set up Home Assistant test instance

## Deliverables

- [ ] Python virtual environment created and activated
- [ ] Home Assistant core installed in development mode
- [ ] All development dependencies installed
- [ ] IDE configured with Python language server
- [ ] Test Home Assistant instance running locally

## Steps

### 1. Create Python Virtual Environment

```bash
cd /Users/mat/code/WienerNetzeHomeAssist
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Home Assistant Core

```bash
pip install --upgrade pip
pip install homeassistant
```

### 3. Install Development Dependencies

```bash
pip install pytest pytest-homeassistant-custom-component
pip install aiohttp
pip install voluptuous
pip install black flake8 pylint mypy
pip install pre-commit
```

### 4. Create requirements.txt and requirements_dev.txt

**requirements.txt:**

```
aiohttp>=3.8.0
```

**requirements_dev.txt:**

```
pytest>=7.0.0
pytest-homeassistant-custom-component>=0.13.0
black>=23.0.0
flake8>=6.0.0
pylint>=2.17.0
mypy>=1.0.0
pre-commit>=3.0.0
```

### 5. Set Up Home Assistant Configuration Directory

```bash
mkdir -p config/custom_components
```

### 6. Initialize Home Assistant

```bash
hass --config config --script ensure_config
```

### 7. Configure VS Code (if using)

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

### 8. Set Up Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
```

Install pre-commit:

```bash
pre-commit install
```

## Acceptance Criteria

- [ ] Virtual environment activates without errors
- [ ] `python --version` shows Python 3.11+
- [ ] `hass --version` shows Home Assistant version
- [ ] `pytest --version` shows pytest version
- [ ] Home Assistant test instance starts: `hass --config config`
- [ ] Pre-commit hooks run successfully: `pre-commit run --all-files`
- [ ] IDE shows no configuration errors

## Testing

```bash
# Test Python environment
python --version
pip list

# Test Home Assistant
hass --version
hass --config config --script check_config

# Test development tools
pytest --version
black --version
flake8 --version
pylint --version
mypy --version

# Test pre-commit
pre-commit run --all-files
```

## References

- [Home Assistant Developer Docs - Environment Setup](https://developers.home-assistant.io/docs/development_environment)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Pre-commit Framework](https://pre-commit.com/)

## Notes

- Use Python 3.11 or later for best compatibility
- Keep virtual environment outside of custom_components directory
- Home Assistant core is large (~500MB), installation may take time
- Test instance uses `config/` directory, not system Home Assistant

## Next Task

→ **Task 02:** Repository Structure Setup
