#!/bin/sh
set -e

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python3 -m venv .venv' first." >&2
    exit 1
fi

# Activate virtual environment
if [ "$(uname)" = "Darwin" ] || [ "$(uname)" = "Linux" ]; then
    . .venv/bin/activate
elif [ "$(uname -s)" = "MINGW64_NT" ] || [ "$(uname -s)" = "MSYS_NT" ]; then
    . .venv/Scripts/activate
else
    echo "Error: Unsupported platform. Please activate the virtual environment manually." >&2
    exit 1
fi

# Run migrator
python3 migrator.py "$@"