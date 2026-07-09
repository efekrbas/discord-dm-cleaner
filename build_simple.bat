@echo off
title DM Cleaner - EXE Builder
color 0A

echo.
echo  ██████╗ ███╗   ███╗     ██████╗██╗     ███████╗ █████╗ ███╗   ██╗██╗     ███████╗██████╗ 
echo ██╔═══██╗████╗  ██║    ██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║██║     ██╔════╝██╔══██╗
echo ██║   ██║██╔██╗ ██║    ██║     ██║     █████╗  ███████║██╔██╗ ██║██║     █████╗  ██████╔╝
echo ██║   ██║██║╚██╗██║    ██║     ██║     ██╔══╝  ██╔══██║██║╚██╗██║██║     ██╔══╝  ██╔══██╗
echo ╚██████╔╝██║ ╚████║    ╚██████╗███████╗███████╗██║  ██║██║ ╚████║███████╗███████╗██║  ██║
echo  ╚═════╝ ╚═╝  ╚═══╝     ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═╝
echo.
echo ================================================================================
echo                           EXE BUILD SCRIPT
echo ================================================================================
echo.

echo [1/4] Gerekli paketler kuruluyor...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo HATA: Paket kurulumu başarısız!
    pause
    exit /b 1
)

echo.
echo [2/4] Eski build dosyaları temizleniyor...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo [3/4] EXE dosyası oluşturuluyor...
pyinstaller --onefile --windowed --icon=app_icon.ico --add-data="images;images" --name="DM Cleaner" main.pyw
if %errorlevel% neq 0 (
    echo HATA: EXE oluşturma başarısız!
    pause
    exit /b 1
)

echo.
echo [4/4] EXE dosyası kopyalanıyor...
if exist "dist\DM Cleaner.exe" (
    copy "dist\DM Cleaner.exe" "DM Cleaner.exe"
    echo.
    echo ================================================================================
    echo                           BUILD BAŞARILI!
    echo ================================================================================
    echo.
    echo EXE dosyası: DM Cleaner.exe
    echo Konum: %cd%
    echo.
    echo Artık DM Cleaner.exe dosyasını çalıştırabilirsiniz!
    echo.
) else (
    echo HATA: EXE dosyası bulunamadı!
)

echo.
pause

