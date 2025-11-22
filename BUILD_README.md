# DM Cleaner - EXE Build Rehberi

Bu rehber DM Cleaner projesini exe dosyasına çevirmek için kullanılır.

## 🚀 Hızlı Başlangıç

### Yöntem 1: Basit Build (Önerilen)
```bash
build_simple.bat
```
Bu dosyayı çift tıklayın ve işlem otomatik olarak tamamlanacak.

### Yöntem 2: Gelişmiş Build
```bash
python build_advanced.py
```
Bu script daha detaylı bilgi verir ve hata kontrolü yapar.

### Yöntem 3: Manuel Build
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=nike.ico --name="DM Cleaner" main.pyw
```

## 📋 Gereksinimler

- Python 3.8+
- Windows 10/11
- İnternet bağlantısı (paket kurulumu için)

## 📁 Dosya Yapısı

```
dm-cleaner/
├── main.pyw              # Ana uygulama dosyası
├── app_core.py           # Uygulama çekirdeği
├── nike.ico              # Uygulama ikonu
├── requirements.txt      # Python paketleri
├── build_simple.bat      # Basit build script
├── build_advanced.py     # Gelişmiş build script
├── dm_cleaner.spec       # PyInstaller konfigürasyonu
└── BUILD_README.md       # Bu dosya
```

## 🔧 Build Parametreleri

- `--onefile`: Tek exe dosyası oluştur
- `--windowed`: Konsol penceresi gösterme
- `--icon=nike.ico`: Uygulama ikonu
- `--name="DM Cleaner"`: Exe dosya adı

## 📊 Çıktı

Build tamamlandıktan sonra:
- `dist/DM Cleaner.exe` - Ana exe dosyası
- `DM Cleaner.exe` - Kopyalanmış exe dosyası (ana klasörde)

## ⚠️ Sorun Giderme

### PyInstaller kurulum hatası
```bash
pip install --upgrade pip
pip install pyinstaller
```

### Modül bulunamadı hatası
```bash
pip install -r requirements.txt
```

### EXE çalışmıyor
- Windows Defender'ı kontrol edin
- Antivirus yazılımını geçici olarak kapatın
- Yönetici olarak çalıştırmayı deneyin

## 🎯 Sonuç

Build başarılı olduğunda `DM Cleaner.exe` dosyasını çift tıklayarak uygulamayı çalıştırabilirsiniz. Bu exe dosyası bağımsız olarak çalışır ve Python kurulumu gerektirmez.

