#!/bin/bash
set -e

echo "Running tests..."
pytest tests/ -v --cov=custom_components.wiener_netze --cov-report=term-missing

echo ""
echo "Running linters..."
black --check custom_components/ tests/
flake8 custom_components/ tests/
pylint custom_components/wiener_netze/

echo ""
echo "Running type checker..."
mypy custom_components/wiener_netze/

echo ""
echo "All checks passed!"
