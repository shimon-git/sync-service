#!/bin/bash

echo "[INFO] Checking virtual environment..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate

    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt
else
    echo "[INFO] Virtual environment already exists."
    source venv/bin/activate
fi

# Run the main script
echo "[INFO] Running main.py..."
python main.py

# Keep the terminal open on exit
read -p "[DONE] Press enter to exit..."
