#!/bin/bash

# KiloBuddy Installer for macOS
echo "Starting KiloBuddy installation for macOS..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 from https://python.org"
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Check if Installer.py exists
if [ ! -f "Installer.py" ]; then
    echo "Error: Installer.py not found in current directory."
    echo "Make sure you're running this from the KiloBuddy folder."
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Run the Python installer
echo "Launching Python installer..."
python3 Installer.py

# Keep terminal open so user can see any messages
echo "Press Enter to close this window..."
read