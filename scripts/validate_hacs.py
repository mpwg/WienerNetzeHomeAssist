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
        "domain",
        "name",
        "version",
        "documentation",
        "issue_tracker",
        "codeowners",
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
