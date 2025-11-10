"""Test utilities for Wiener Netze Smart Meter integration."""

import json
from pathlib import Path


def load_fixture(filename: str) -> str:
    """Load a fixture file.

    Args:
        filename: Name of the fixture file to load.

    Returns:
        Contents of the fixture file as a string.
    """
    path = Path(__file__).parent / "fixtures" / filename
    return path.read_text()


def load_json_fixture(filename: str) -> dict:
    """Load a JSON fixture file.

    Args:
        filename: Name of the JSON fixture file to load.

    Returns:
        Parsed JSON content as a dictionary.
    """
    return json.loads(load_fixture(filename))
