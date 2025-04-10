#!/bin/bash

echo "[INFO] Cleaning Python environment..."

# Remove virtual environment
if [ -d "venv" ]; then
    echo "[INFO] Removing virtual environment folder..."
    rm -rf venv
else
    echo "[INFO] No virtual environment found."
fi

# Remove __pycache__ folders
echo "[INFO] Removing __pycache__ folders..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove .pyc files
echo "[INFO] Removing .pyc files..."
find . -type f -name "*.pyc" -delete

echo "[DONE] Cleanup complete!"
read -p "Press enter to exit..."
