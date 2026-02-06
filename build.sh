#!/bin/bash
# Build script for creating FASTVOLT executable

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Building executable..."
pyinstaller build.spec

echo ""
if [ -f "dist/FASTVOLT" ]; then
    echo "Build successful!"
    echo "Executable located at: dist/FASTVOLT"
    ls -lh "dist/FASTVOLT"
else
    echo "Build failed! Executable not found."
    exit 1
fi

echo ""
echo "To run the application, execute: ./dist/FASTVOLT"
