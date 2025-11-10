#!/bin/bash
# Activate the development environment
source venv/bin/activate
echo "✅ Virtual environment activated"
echo "Python: $(python --version)"
echo "Home Assistant: $(hass --version)"
echo ""
echo "Ready to develop! 🚀"
