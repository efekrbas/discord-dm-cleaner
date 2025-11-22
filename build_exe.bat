@echo off
echo DM Cleaner - EXE Build Script
echo ================================

echo.
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building EXE file...
pyinstaller dm_cleaner.spec

echo.
echo Build completed!
echo EXE file location: dist\DM Cleaner.exe
echo.
pause

