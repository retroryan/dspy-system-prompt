#!/bin/bash

# Check if an argument was provided
if [ $# -eq 0 ]; then
    echo "Usage: ./sample_html.sh <number>"
    echo "Available color schemes (1-10):"
    echo "  1 - Ocean Depth (Deep blues with professional contrast)"
    echo "  2 - Forest Moss (Natural greens with earthy tones)"
    echo "  3 - Sunset Glow (Warm reds and oranges)"
    echo "  4 - Purple Dusk (Sophisticated purple gradients)"
    echo "  5 - Midnight Blue (Sleek slate blues)"
    echo "  6 - Rose Garden (Elegant rose and pink tones)"
    echo "  7 - Teal Wave (Refreshing aquatic palette)"
    echo "  8 - Amber Glow (Warm amber and golden tones)"
    echo "  9 - Arctic Frost (Cool, crisp icy blues)"
    echo "  10 - Carbon Steel (Minimalist monochrome)"
    exit 1
fi

# Get the number from the first argument
NUMBER=$1

# Validate input
if ! [[ "$NUMBER" =~ ^[1-9]$|^10$ ]]; then
    echo "Error: Please provide a number between 1 and 10"
    exit 1
fi

# Define the base directory
BASE_DIR="$(dirname "$0")/html_samples"

# Map numbers to file names
case $NUMBER in
    1) FILE="scheme_1_ocean_depth.html" ;;
    2) FILE="scheme_2_forest_moss.html" ;;
    3) FILE="scheme_3_sunset_glow.html" ;;
    4) FILE="scheme_4_purple_dusk.html" ;;
    5) FILE="scheme_5_midnight_blue.html" ;;
    6) FILE="scheme_6_rose_garden.html" ;;
    7) FILE="scheme_7_teal_wave.html" ;;
    8) FILE="scheme_8_amber_glow.html" ;;
    9) FILE="scheme_9_arctic_frost.html" ;;
    10) FILE="scheme_10_carbon_steel.html" ;;
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

echo "Opening color scheme $NUMBER: $FILE"