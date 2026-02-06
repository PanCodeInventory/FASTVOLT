@echo off
REM Build script for creating FASTVOLT.exe on Windows

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller build.spec

echo.
if exist "dist\FASTVOLT.exe" (
    echo Build successful!
    echo Executable located at: dist\FASTVOLT.exe
    dir "dist\FASTVOLT.exe"
) else (
    echo Build failed! FASTVOLT.exe not found.
    exit /b 1
)

echo.
echo To run the application, execute: dist\FASTVOLT.exe
pause
