#!/bin/bash
echo "Installing Python packages..."
pip install -r requirements.txt

echo "Installing Playwright Chromium..."
playwright install chromium
