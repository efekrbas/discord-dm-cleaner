#!/usr/bin/env python3
"""
DM Cleaner - Advanced Build Script
Bu script projeyi exe dosyasına çevirir
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Komut çalıştır ve sonucu göster"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} başarılı!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} başarısız!")
        print(f"Hata: {e.stderr}")
        return False

def main():
    print("🚀 DM Cleaner - EXE Build Script")
    print("=" * 50)
    
    # Gerekli dosyaları kontrol et
    required_files = ['main.pyw', 'app_core.py', 'nike.ico']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Eksik dosyalar: {', '.join(missing_files)}")
        return False
    
    print("✅ Tüm gerekli dosyalar mevcut")
    
    # PyInstaller kurulumu
    if not run_command("pip install pyinstaller", "PyInstaller kurulumu"):
        return False
    
    # Eski build dosyalarını temizle
    if os.path.exists("build"):
        print("\n🧹 Eski build dosyaları temizleniyor...")
        shutil.rmtree("build")
    
    if os.path.exists("dist"):
        print("🧹 Eski dist dosyaları temizleniyor...")
        shutil.rmtree("dist")
    
    # EXE oluştur
    build_command = "pyinstaller --onefile --windowed --icon=nike.ico --name=\"DM Cleaner\" main.pyw"
    
    if not run_command(build_command, "EXE dosyası oluşturma"):
        return False
    
    # Sonuçları kontrol et
    exe_path = Path("dist") / "DM Cleaner.exe"
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print(f"\n🎉 Build başarılı!")
        print(f"📁 EXE dosyası: {exe_path}")
        print(f"📊 Dosya boyutu: {file_size:.1f} MB")
        
        # Kopyalama seçeneği
        copy_choice = input("\n📋 EXE dosyasını ana klasöre kopyalamak ister misiniz? (y/n): ")
        if copy_choice.lower() == 'y':
            shutil.copy2(exe_path, "DM Cleaner.exe")
            print("✅ EXE dosyası ana klasöre kopyalandı!")
        
        return True
    else:
        print("❌ EXE dosyası oluşturulamadı!")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 İşlem tamamlandı!")
    else:
        print("\n💥 İşlem başarısız!")
    
    input("\nDevam etmek için Enter'a basın...")

