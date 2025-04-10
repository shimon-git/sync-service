@echo off
echo [INFO] Cleaning Python environment...

REM Delete the virtual environment folder
if exist venv (
    echo [INFO] Removing virtual environment folder...
    rmdir /s /q venv
) else (
    echo [INFO] No virtual environment found.
)

REM Remove __pycache__ folders
echo [INFO] Removing __pycache__ folders...
for /d /r %%d in (__pycache__) do (
    rmdir /s /q "%%d"
)

REM Remove .pyc files
echo [INFO] Removing .pyc files...
for /r %%f in (*.pyc) do (
    del /q "%%f"
)

echo [DONE] Cleanup complete!
pause
