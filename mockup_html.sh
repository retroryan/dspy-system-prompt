#!/bin/bash

# Check if an argument was provided
if [ $# -eq 0 ]; then
    echo "Usage: ./mockup_html.sh <page>"
    echo "Available pages:"
    echo "  1 - Dashboard (Main overview page)"
    echo "  2 - Demos (Run Demo Scripts)"
    echo "  3 - Admin Settings (System health and configuration)"
    echo "  4 - Advanced Chatbot (Interactive agent with loop visualization)"
    echo "  5 - About (System information and documentation)"
    exit 1
fi

# Get the page number from the first argument
PAGE=$1

# Validate input
if ! [[ "$PAGE" =~ ^[1-5]$ ]]; then
    echo "Error: Please provide a number between 1 and 5"
    exit 1
fi

# Define the base directory
BASE_DIR="$(dirname "$0")/html_samples"

# Map numbers to file names
case $PAGE in
    1) FILE="mockup_dashboard.html" ;;
    2) FILE="mockup_demos.html" ;;
    3) FILE="mockup_admin.html" ;;
    4) FILE="mockup_advanced.html" ;;
    5) FILE="mockup_about.html" ;;
esac

# Full path to the HTML file
FULL_PATH="$BASE_DIR/$FILE"

# Check if file exists
if [ ! -f "$FULL_PATH" ]; then
    echo "Error: File $FULL_PATH not found"
    exit 1
fi

# Detect the operating system and open the file accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$FULL_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &> /dev/null; then
        xdg-open "$FULL_PATH"
    elif command -v gnome-open &> /dev/null; then
        gnome-open "$FULL_PATH"
    else
        echo "Error: Could not find a command to open the browser"
        echo "Please open manually: $FULL_PATH"
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    start "$FULL_PATH"
else
    echo "Error: Unsupported operating system"
    echo "Please open manually: $FULL_PATH"
    exit 1
fi

echo "Opening page: $FILE"