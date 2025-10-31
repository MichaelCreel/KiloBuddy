#!/bin/bash

# KiloBuddy Installer for Linux
echo "Starting KiloBuddy installation for Linux..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Installer.py exists
if [ ! -f "Installer.py" ]; then
    echo "Error: Installer.py not found in current directory."
    echo "Current directory: $(pwd)"
    echo "Make sure you're running this from the KiloBuddy folder."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Checking for required system packages..."

# Check for audio development libraries (needed for PyAudio)
if ! pkg-config --exists portaudio-2.0 2>/dev/null; then
    echo "Warning: PortAudio development libraries not found."
    echo "PyAudio installation may fail."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the Python installer
echo "Launching Python installer..."
python3 Installer.py

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Installation completed!"
else
    echo ""
    echo "Installation encountered errors."
fi

# Keep terminal open so user can see any messages
echo ""
read -p "Press Enter to close this window..."