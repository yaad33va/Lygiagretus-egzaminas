@echo off
REM run_test.bat - Windows automated test runner

echo ==========================================
echo Food Processing System - Test Runner
echo ==========================================
echo.

if not exist main.exe (
    echo Error: main.exe not found
    echo Please run build.bat first
    pause
    exit /b 1
)

if not exist data1.json (
    echo Generating data files...
    python generate_data.py
)

echo Select test to run:
echo 1. Test data1.json (all items match filters)
echo 2. Test data2.json (0 items match - fail filter1)
echo 3. Test data3.json (0 items match - fail filter2)
echo 4. Test data4.json (partial items match)
echo.

set /p choice="Enter choice [1-4]: "

if "%choice%"=="1" set datafile=data1.json
if "%choice%"=="2" set datafile=data2.json
if "%choice%"=="3" set datafile=data3.json
if "%choice%"=="4" set datafile=data4.json

if "%datafile%"=="" (
    echo Invalid choice
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Running test with %datafile%
echo ==========================================
echo.
echo Starting C++ program...
start "C++ Program" cmd /k main.exe %datafile%

echo Waiting for C++ to initialize...
timeout /t 2 /nobreak >nul

echo Starting Python program...
start "Python Program" cmd /k python worker.py

echo.
echo Both programs started in separate windows
echo Wait for them to complete, then check results_%datafile%
echo.
pause
