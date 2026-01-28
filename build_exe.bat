@echo off
echo Building Icecast Streamer EXE...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Install PyInstaller if needed
pip install pyinstaller

REM Build the EXE
pyinstaller --onefile --windowed --name "IcecastStreamer" --icon=icon.ico streamer.py

echo.
echo Build complete! The EXE is in the 'dist' folder.
echo.
echo IMPORTANT: Copy ffmpeg.exe to the same folder as IcecastStreamer.exe
pause
