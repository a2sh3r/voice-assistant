#!/usr/bin/env bash
# build.sh — Linux / macOS build script
# Run: chmod +x build.sh && ./build.sh

set -e

echo "=== Building assistant for $(uname -s) ==="

# Install dependencies if needed
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

# Clean previous build
rm -rf dist build

# Run PyInstaller
pyinstaller assistant.spec --noconfirm

echo ""
echo "=== Build successful! ==="
echo "Binary: dist/assistant/assistant"
echo ""
echo "NOTE: Copy your .env file next to the binary before running."
echo "NOTE: Whisper/Silero models will download on first run (~500MB)."

# macOS: fix pynput permissions hint
if [[ "$(uname)" == "Darwin" ]]; then
    echo ""
    echo "macOS: grant Accessibility permission to dist/assistant/assistant"
    echo "  System Preferences → Privacy & Security → Accessibility → add the binary"
fi
