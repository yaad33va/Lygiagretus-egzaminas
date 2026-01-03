@echo off
REM build.bat - Windows build and run script

echo ==========================================
echo Food Processing System - Windows Builder
echo ==========================================
echo.

REM Check for Visual Studio
where cl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Visual Studio C++ compiler not found!
    echo Please run this from "Developer Command Prompt for VS"
    echo Or install Visual Studio with C++ support
    pause
    exit /b 1
)

REM Check for OpenCL
if not exist "%CUDA_PATH%\include\CL\cl.h" (
    if not exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\*\include\CL\cl.h" (
        echo Warning: OpenCL headers not found
        echo Please install OpenCL SDK from your GPU vendor
        echo - NVIDIA: CUDA Toolkit
        echo - AMD: AMD APP SDK
        echo - Intel: Intel SDK for OpenCL
        echo.
    )
)

echo Step 1: Generating data files...
python generate_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Error generating data files
    pause
    exit /b 1
)
echo Data files generated successfully!
echo.

echo Step 2: Compiling C++ program...
cl /EHsc /O2 /W4 main.cpp /link OpenCL.lib ws2_32.lib
if %ERRORLEVEL% NEQ 0 (
    echo Error compiling C++ program
    echo.
    echo Troubleshooting:
    echo 1. Make sure you run this from Developer Command Prompt
    echo 2. Check that OpenCL SDK is installed
    echo 3. Add OpenCL lib path if needed:
    echo    set LIB=%%LIB%%;C:\Path\To\OpenCL\lib
    pause
    exit /b 1
)
echo Compilation successful!
echo.

echo ==========================================
echo Build Complete!
echo ==========================================
echo.
echo To run the program:
echo   1. Open two command prompts
echo   2. In first prompt:  main.exe data1.json
echo   3. In second prompt: python worker.py
echo.
echo Or run: run_test.bat
echo.
pause
