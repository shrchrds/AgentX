@echo off
REM ===================================================
REM   AgentX Launcher for Windows
REM ===================================================

echo ===================================================
echo   Starting AgentX Multi-Agent Legal Framework
echo ===================================================
echo.

IF EXIST ".venv\Scripts\python.exe" (
    SET "PY_CMD=.venv\Scripts\python.exe"
) ELSE (
    SET "PY_CMD=python"
)

echo [1] Launch Full Stack (Backend + Frontend)
echo [2] Launch Backend API Server (http://localhost:8000)
echo [3] Launch Frontend (http://localhost:5173)
echo [4] Run CLI Demo (Terminal Multi-Agent Review)
echo [5] Run All Tests (Pytest)
echo.

SET /P choice="Select option (1-5, default 1): "

IF "%choice%"=="2" (
    %PY_CMD% run.py --server
) ELSE IF "%choice%"=="3" (
    %PY_CMD% run.py --frontend
) ELSE IF "%choice%"=="4" (
    %PY_CMD% run.py --demo
) ELSE IF "%choice%"=="5" (
    %PY_CMD% run.py --test
) ELSE (
    %PY_CMD% run.py --all
)

pause
