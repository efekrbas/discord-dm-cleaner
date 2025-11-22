#!/usr/bin/env python3
"""
Debug version of main.pyw to see console output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DiscordMessageManager

def main():
    print("=== DM Cleaner Debug Mode ===")
    print("Discord RPC test başlatılıyor...")
    
    # Create the main window
    app = QApplication(sys.argv)
    window = DiscordMessageManager()
    
    print("Ana pencere oluşturuldu")
    print("Discord RPC durumu:", window.rpc_connected)
    
    window.show()
    
    print("Uygulama başlatıldı - Discord'da aktiviteyi kontrol edin")
    print("Uygulamayı kapatmak için pencereyi kapatın")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    main()
