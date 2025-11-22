# DM Cleaner - EXE Build Guide

This guide is used to convert the DM Cleaner project into an exe file.

## 🚀 Quick Start

### Method 1: Simple Build (Recommended)
```bash
build_simple.bat
```
Double-click this file and the process will complete automatically.

### Method 2: Advanced Build
```bash
python build_advanced.py
```
This script provides more detailed information and performs error checking.

### Method 3: Manual Build
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=nike.ico --name="DM Cleaner" main.pyw
```

## 📋 Requirements

- Python 3.8+
- Windows 10/11
- Internet connection (for package installation)

## 📁 File Structure

```
dm-cleaner/
├── main.pyw              # Main application file
├── app_core.py           # Application core
├── nike.ico              # Application icon
├── requirements.txt      # Python packages
├── build_simple.bat      # Simple build script
├── build_advanced.py     # Advanced build script
├── dm_cleaner.spec       # PyInstaller configuration
└── BUILD_README.md       # This file
```

## 🔧 Build Parameters

- `--onefile`: Create a single exe file
- `--windowed`: Don't show console window
- `--icon=nike.ico`: Application icon
- `--name="DM Cleaner"`: Exe file name

## 📊 Output

After build completion:
- `dist/DM Cleaner.exe` - Main exe file
- `DM Cleaner.exe` - Copied exe file (in main folder)

## ⚠️ Troubleshooting

### PyInstaller installation error
```bash
pip install --upgrade pip
pip install pyinstaller
```

### Module not found error
```bash
pip install -r requirements.txt
```

### EXE not working
- Check Windows Defender
- Temporarily disable antivirus software
- Try running as administrator

## 🎯 Result

When the build is successful, you can run the application by double-clicking the `DM Cleaner.exe` file. This exe file runs independently and does not require Python installation.
