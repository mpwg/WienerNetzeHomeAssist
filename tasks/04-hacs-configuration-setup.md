# Task 04: HACS Configuration Setup

**Category:** Project Setup  
**Priority:** Medium  
**Estimated Effort:** 1 hour  
**Status:** Not Started

## Description

Configure the repository for HACS (Home Assistant Community Store) compatibility, enabling easy installation and updates for users.

## Prerequisites

- **Task 02** completed (Repository Structure Setup)
- GitHub repository created and accessible

## Objectives

1. Create hacs.json configuration file
2. Add HACS badge to README
3. Validate HACS requirements
4. Prepare for HACS submission

## Deliverables

- [ ] `hacs.json` file created
- [ ] `.github/` workflows configured (optional)
- [ ] HACS requirements validated
- [ ] Documentation updated with HACS installation instructions

## Steps

### 1. Create hacs.json

```json
{
  "name": "Wiener Netze Smart Meter",
  "render_readme": true,
  "domains": ["sensor"],
  "iot_class": "cloud_polling",
  "homeassistant": "2024.1.0",
  "zip_release": false,
  "filename": false
}
```

Place in repository root: `/Users/mat/code/WienerNetzeHomeAssist/hacs.json`

### 2. Verify HACS Requirements Checklist

Ensure repository meets HACS requirements:

**Repository Structure:**

- ✅ Custom integration in `custom_components/<domain>/`
- ✅ manifest.json with required fields
- ✅ One integration per repository
- ✅ Clear README.md
- ✅ LICENSE file (AGPL-3.0)

**manifest.json Requirements:**

- ✅ `domain` field
- ✅ `name` field
- ✅ `version` field (semantic versioning)
- ✅ `documentation` URL
- ✅ `issue_tracker` URL
- ✅ `codeowners` list

**GitHub Requirements:**

- ✅ Public repository
- ✅ Tagged releases (will be created in Task 35)
- ✅ Repository topics: `home-assistant`, `hacs`

### 3. Add GitHub Repository Topics

```bash
# Via GitHub web interface:
# Settings → General → Topics
# Add: home-assistant, hacs, wiener-netze, smart-meter, home-automation
```

Or via GitHub CLI:

```bash
gh repo edit --add-topic home-assistant,hacs,wiener-netze,smart-meter,home-automation
```

### 4. Create GitHub Issue Templates

**.github/ISSUE_TEMPLATE/bug_report.yml:**

```yaml
name: Bug Report
description: Report a bug with the Wiener Netze Smart Meter integration
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug!

  - type: textarea
    id: description
    attributes:
      label: Describe the bug
      description: A clear and concise description of what the bug is.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: What you expected to happen
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output
      render: shell

  - type: input
    id: ha-version
    attributes:
      label: Home Assistant Version
      placeholder: "2024.11.0"
    validations:
      required: true

  - type: input
    id: integration-version
    attributes:
      label: Integration Version
      placeholder: "1.0.0"
    validations:
      required: true
```

**.github/ISSUE_TEMPLATE/feature_request.yml:**

```yaml
name: Feature Request
description: Suggest a new feature for the integration
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a new feature!

  - type: textarea
    id: description
    attributes:
      label: Feature description
      description: A clear description of the feature you'd like to see
    validations:
      required: true

  - type: textarea
    id: use-case
    attributes:
      label: Use case
      description: Describe your use case for this feature
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Any alternative solutions you've considered
```

### 5. Create Pull Request Template

**.github/pull_request_template.md:**

```markdown
## Description

Please include a summary of the changes and which issue is fixed.

Fixes # (issue)

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### 6. Update README.md with HACS Installation

Add to README.md:

```markdown
## Installation

### Prerequisites

Before installing this integration, you need:

1. **Wiener Netze Smart Meter** installed and active
2. **API Credentials** from [WSTW API Portal](https://test-api.wienerstadwerke.at/portal/)
3. **HACS** installed in Home Assistant ([HACS Installation Guide](https://hacs.xyz/docs/setup/download))

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mpwg/WienerNetzeHomeAssist`
6. Select category: "Integration"
7. Click "Add"
8. Find "Wiener Netze Smart Meter" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/mpwg/WienerNetzeHomeAssist/releases)
2. Extract the `custom_components/wiener_netze` directory
3. Copy it to your Home Assistant `custom_components` directory
4. Restart Home Assistant

### Configuration

After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Wiener Netze Smart Meter"**
4. Follow the configuration wizard
```

### 7. Validate HACS Compatibility

Create validation script:

**scripts/validate_hacs.py:**

```python
"""Validate HACS compatibility."""
import json
import sys
from pathlib import Path

def validate_hacs():
    """Validate HACS requirements."""
    errors = []

    # Check hacs.json exists
    hacs_json = Path("hacs.json")
    if not hacs_json.exists():
        errors.append("hacs.json not found")
        return errors

    # Check hacs.json format
    try:
        hacs_config = json.loads(hacs_json.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"hacs.json invalid JSON: {e}")
        return errors

    # Check required fields
    required_fields = ["name", "domains", "iot_class"]
    for field in required_fields:
        if field not in hacs_config:
            errors.append(f"hacs.json missing required field: {field}")

    # Check manifest.json
    manifest = Path("custom_components/wiener_netze/manifest.json")
    if not manifest.exists():
        errors.append("manifest.json not found")
        return errors

    try:
        manifest_data = json.loads(manifest.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"manifest.json invalid JSON: {e}")
        return errors

    # Check manifest required fields
    manifest_required = [
        "domain", "name", "version", "documentation",
        "issue_tracker", "codeowners"
    ]
    for field in manifest_required:
        if field not in manifest_data:
            errors.append(f"manifest.json missing required field: {field}")

    # Check version format (semantic versioning)
    version = manifest_data.get("version", "")
    if not version or len(version.split(".")) != 3:
        errors.append("manifest.json version must be semantic (X.Y.Z)")

    return errors

if __name__ == "__main__":
    errors = validate_hacs()
    if errors:
        print("HACS Validation Errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✓ HACS validation passed")
        sys.exit(0)
```

Run validation:

```bash
python scripts/validate_hacs.py
```

## Acceptance Criteria

- [ ] `hacs.json` file created with correct format
- [ ] Repository has appropriate GitHub topics
- [ ] Issue templates created
- [ ] Pull request template created
- [ ] README.md includes HACS installation instructions
- [ ] HACS validation script passes
- [ ] All HACS requirements met

## Testing

```bash
# Validate hacs.json format
cat hacs.json | python -m json.tool

# Validate HACS compatibility
python scripts/validate_hacs.py

# Check manifest.json
cat custom_components/wiener_netze/manifest.json | python -m json.tool

# Verify GitHub topics (via GitHub CLI)
gh repo view --json repositoryTopics
```

## References

- [HACS Documentation](https://hacs.xyz/)
- [HACS Integration Requirements](https://hacs.xyz/docs/publish/integration/)
- [HACS Action Validation](https://github.com/hacs/action)

## Notes

- HACS requires semantic versioning (MAJOR.MINOR.PATCH)
- Repository must be public for HACS discovery
- After first release, submit to HACS default repository (optional)
- Users can add as custom repository before official HACS approval

## Next Task

→ **Task 05:** API Client - Basic Structure
