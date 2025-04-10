@echo off

REM Check if venv exists
IF NOT EXIST "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv

    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate

    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
) ELSE (
    echo [INFO] Virtual environment already exists.
    call venv\Scripts\activate
)

REM Run the main script
echo [INFO] Running main.py...
python main.py

REM Pause in case of crash
pause
