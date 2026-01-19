#!/bin/bash
# Legacy wrapper script for backward compatibility
# This provides a simple way to run the new Python script with default settings

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import internetarchive" &> /dev/null; then
    echo "Installing required dependencies..."
    pip3 install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies."
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# Run the Python script with default settings
echo "Running Crunchy Archive Downloader..."
python3 crunchy.py "$@"
