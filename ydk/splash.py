from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
import os
from login import LoginWindow  # Yeni login.py dosyasından LoginWindow'u import et

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Ana layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Arka plan frame'i
        self.container = QFrame()
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(15)
        
        # Logo ve başlık
        title_label = QLabel("Copief DM Cleaner")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setObjectName("progressBar")
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setValue(0)
        self.progress.setMaximum(100)
        
        # Yükleniyor metni
        self.loading_label = QLabel("Yükleniyor...")
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Widget'ları layout'a ekle
        container_layout.addWidget(title_label)
        container_layout.addWidget(self.progress)
        container_layout.addWidget(self.loading_label)
        
        # Ana layout'a container'ı ekle
        layout.addWidget(self.container)
        self.setLayout(layout)
        
        # Stil
        self.setStyleSheet("""
            QFrame#container {
                background-color: #0a0a1a;
                border: 2px solid #1f1f35;
                border-radius: 15px;
            }
            
            QLabel#titleLabel {
                color: #ff2e63;
                font-size: 24px;
                font-weight: bold;
                margin: 10px;
            }
            
            QLabel#loadingLabel {
                color: #e94560;
                font-size: 14px;
                margin-bottom: 10px;
            }
            
            QProgressBar {
                background-color: #151525;
                border: none;
                border-radius: 10px;
                text-align: center;
                color: #e94560;
                font-weight: bold;
                height: 20px;
                margin: 0px 20px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f3460, stop:1 #533483);
                border-radius: 10px;
            }
        """)
        
        # Pencere boyutu
        self.resize(400, 200)
        
        # Ekranın ortasına konumlandır
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
        
        # Timer ile progress bar'ı güncelle
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)
        self.progress_value = 0
        
        # Login penceresi referansı
        self.login_window = None
    
    def update_progress(self):
        """Progress bar'ı güncelle ve login penceresini aç"""
        self.progress_value += 1
        self.progress.setValue(self.progress_value)
        
        # Yükleme mesajlarını güncelle
        if self.progress_value <= 30:
            self.loading_label.setText("Arayüz hazırlanıyor...")
        elif self.progress_value <= 60:
            self.loading_label.setText("Bileşenler yükleniyor...")
        elif self.progress_value <= 90:
            self.loading_label.setText("Son hazırlıklar yapılıyor...")
        else:
            self.loading_label.setText("Başlatılıyor...")
        
        # Yükleme tamamlandığında
        if self.progress_value >= 100:
            self.timer.stop()
            # Splash'ı kapatmadan önce LoginWindow'u QTimer.singleShot ile aç
            def show_login():
                self.login_window = LoginWindow()
                self.login_window.show()
            QTimer.singleShot(0, show_login)
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Splash screen'i göster
    splash = SplashScreen()
    splash.show()
    
    sys.exit(app.exec()) 