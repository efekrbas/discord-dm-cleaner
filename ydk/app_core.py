import asyncio
import json
import aiohttp
import sys
import os
import base64
import re
import win32crypt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QListWidget, QLabel, 
                            QProgressBar, QMessageBox, QFrame, QStyle, QLineEdit,
                            QListWidgetItem)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt6.QtGui import QPalette, QColor, QIcon, QPixmap, QImage, QFont
from Crypto.Cipher import AES

# --- DiscordMessageManager and get_discord_token moved from main.pyw ---
# (Copy the full class DiscordMessageManager and the get_discord_token function here)

# --- Begin DiscordMessageManager and get_discord_token ---

class TokenWorker(QThread):
    token_ready = pyqtSignal(str)
    
    def run(self):
        asyncio.run(self.get_and_save_token())
    
    async def get_and_save_token(self):
        try:
            tokens = await get_discord_token()
            if tokens:
                self.token_ready.emit(tokens[0])
            else:
                pass
        except Exception as e:
            pass

class DiscordWorker(QThread):
    dm_list_ready = pyqtSignal(list)
    message_deleted = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)
    dm_loading_progress = pyqtSignal(int, int)
    finished_deletion = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_channel = None
        self.delete_all = False
        self._is_running = True
        self._session = None
        self.token = None
        self.deleted_count = 0
        self.total_deleted = 0
        self.current_dm_index = 0
        self.total_dm_count = 0
        self.current_username = ""
        self.completed_dms = 0
        
    def set_token(self, token):
        self.token = token
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        asyncio.run(self.main())

    async def get_token(self):
        return self.token

    async def get_avatar(self, user_id, avatar_id):
        if not avatar_id or not self._session:
            return None
        
        url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png?size=32"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            pass
        return None

    async def get_dm_channels(self):
        headers = {
            "Authorization": await self.get_token(),
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            self._session = session
            try:
                async with session.get("https://discord.com/api/v9/users/@me/channels", headers=headers) as resp:
                    if resp.status != 200:
                        self.error_occurred.emit(f"DM listesi alınamadı: HTTP {resp.status}")
                        return
                    
                    channels = await resp.json()
                    
                    # Tüm DM türlerini dahil et: birebir DM'ler, grup sohbetleri ve diğer özel kanallar
                    dm_channels = []
                    for channel in channels:
                        channel_type = channel.get("type", 0)
                        # Type 1: Birebir DM, Type 3: Grup DM, Type 0: Text channel (bazı özel durumlar için)
                        if channel_type in [1, 3] or (channel_type == 0 and "recipients" in channel):
                            dm_channels.append(channel)
                    
                    total_channels = len(dm_channels)
                    
                    dm_list = []
                    for idx, channel in enumerate(dm_channels, 1):
                        # Kanal tipine göre kullanıcı adını belirle
                        if channel["type"] == 1:  # Birebir DM
                            if "recipients" in channel and len(channel["recipients"]) > 0:
                                recipient = channel["recipients"][0]
                                username = recipient.get('global_name') or recipient.get("username", "Bilinmeyen Kullanıcı")
                                user_id = recipient["id"]
                                avatar = recipient.get("avatar")
                            else:
                                username = "Bilinmeyen Kullanıcı"
                                user_id = "unknown"
                                avatar = None
                        elif channel["type"] == 3:  # Grup sohbeti
                            username = channel.get("name", "Bilinmeyen Grup")
                            user_id = channel["id"]
                            avatar = None
                        elif channel["type"] == 0 and "recipients" in channel:  # Özel DM kanalı
                            if len(channel["recipients"]) == 1:
                                recipient = channel["recipients"][0]
                                username = recipient.get('global_name') or recipient.get("username", "Bilinmeyen Kullanıcı")
                                user_id = recipient["id"]
                                avatar = recipient.get("avatar")
                            else:
                                username = channel.get("name", "Grup Sohbeti")
                                user_id = channel["id"]
                                avatar = None
                        else:
                            username = "Bilinmeyen Kanal"
                            user_id = "unknown"
                            avatar = None
                        
                        self.dm_loading_progress.emit(idx, total_channels)
                        
                        avatar_task = asyncio.create_task(
                            self.get_avatar(user_id, avatar)
                        )
                        
                        dm_list.append({
                            'username': username,
                            'id': channel['id'],
                            'avatar': await avatar_task
                        })
                    
                    self.dm_list_ready.emit(sorted(dm_list, key=lambda x: x['username'].lower()))
                    
            except Exception as e:
                self.error_occurred.emit(f"DM listesi alınırken hata: {str(e)}")
            finally:
                self._session = None

    async def delete_message(self, session, channel_id, message_id):
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
        headers = {
            "Authorization": await self.get_token(),
            "Content-Type": "application/json"
        }
        
        try:
            async with session.delete(url, headers=headers) as resp:
                if resp.status == 204:
                    return True
                elif resp.status == 429:
                    retry_after = float((await resp.json()).get('retry_after', 1))
                    self.message_deleted.emit(f"Rate limit aşıldı, {retry_after:.1f} saniye bekleniyor...")
                    await asyncio.sleep(retry_after + 1.1)
                    return await self.delete_message(session, channel_id, message_id)
                elif resp.status == 403:
                    self.message_deleted.emit(f"Mesaj silinemedi: Yetki yok (403) - Mesaj ID: {message_id}")
                    return False
                elif resp.status == 404:
                    self.message_deleted.emit(f"Mesaj bulunamadı (404) - Mesaj ID: {message_id}")
                    return False
                elif resp.status == 400:
                    error_text = await resp.text()
                    self.message_deleted.emit(f"Geçersiz istek (400) - Mesaj ID: {message_id} - Hata: {error_text}")
                    return False
                else:
                    error_text = await resp.text()
                    self.message_deleted.emit(f"Mesaj silinemedi: HTTP {resp.status} - Mesaj ID: {message_id} - Hata: {error_text}")
                    return False
        except Exception as e:
            self.message_deleted.emit(f"Mesaj silinirken hata oluştu: {str(e)} - Mesaj ID: {message_id}")
            return False

    async def delete_all_dms(self):
        headers = {
            "Authorization": await self.get_token(),
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://discord.com/api/v9/users/@me/channels", headers=headers) as resp:
                    if resp.status != 200:
                        self.error_occurred.emit(f"DM listesi alınamadı: HTTP {resp.status}")
                        return
                    
                    channels = await resp.json()
                    
                    # Tüm DM türlerini dahil et: birebir DM'ler, grup sohbetleri ve diğer özel kanallar
                    dm_channels = []
                    for channel in channels:
                        channel_type = channel.get("type", 0)
                        # Type 1: Birebir DM, Type 3: Grup DM, Type 0: Text channel (bazı özel durumlar için)
                        if channel_type in [1, 3] or (channel_type == 0 and "recipients" in channel):
                            dm_channels.append(channel)
                    
                    self.total_dm_count = len(dm_channels)
                    self.message_deleted.emit(f"Toplam {self.total_dm_count} DM kutusu bulundu. Silme işlemi başlıyor...")
                    
                    for i, channel in enumerate(dm_channels, 1):
                        if not self._is_running:
                            self.message_deleted.emit(
                                f"İşlem durduruldu!\n"
                                f"Son işlem: {self.current_username} ile olan DM'de kaldınız.\n"
                                f"Toplam {self.completed_dms}/{self.total_dm_count} DM kutusu temizlendi.\n"
                                f"Toplam {self.total_deleted} mesaj silindi."
                            )
                            self.finished_deletion.emit()
                            return
                        
                        # Kanal tipine göre kullanıcı adını belirle
                        if channel["type"] == 1:  # Birebir DM
                            if "recipients" in channel and len(channel["recipients"]) > 0:
                                recipient = channel["recipients"][0]
                                self.current_username = recipient.get('global_name') or recipient.get("username", "Bilinmeyen Kullanıcı")
                            else:
                                self.current_username = "Bilinmeyen Kullanıcı"
                        elif channel["type"] == 3:  # Grup sohbeti
                            self.current_username = channel.get("name", "Bilinmeyen Grup")
                        elif channel["type"] == 0 and "recipients" in channel:  # Özel DM kanalı
                            if len(channel["recipients"]) == 1:
                                recipient = channel["recipients"][0]
                                self.current_username = recipient.get('global_name') or recipient.get("username", "Bilinmeyen Kullanıcı")
                            else:
                                self.current_username = channel.get("name", "Grup Sohbeti")
                        else:
                            self.current_username = "Bilinmeyen Kanal"
                        self.current_dm_index = i
                        self.message_deleted.emit(f"DM Kutusu {i}/{self.total_dm_count} - {self.current_username} ile olan mesajlar siliniyor...")
                        
                        # Bu DM'deki mesaj sayısını kaydet
                        messages_before = self.deleted_count
                        await self.delete_messages(channel["id"])
                        messages_deleted_in_this_dm = self.deleted_count - messages_before
                        self.completed_dms += 1
                        self.message_deleted.emit(f"✓ {self.current_username} ile olan {messages_deleted_in_this_dm} mesaj silindi.")
                        
                        if not self._is_running:
                            break
                    
                    self.message_deleted.emit(
                        f"🎉 Tüm DM'ler temizlendi!\n"
                        f"✓ İşlenen DM kutusu: {self.completed_dms}/{self.total_dm_count}\n"
                        f"✓ Toplam silinen mesaj: {self.total_deleted}\n"
                        f"✓ İşlem başarıyla tamamlandı!"
                    )
                    self.finished_deletion.emit()
                    
            except Exception as e:
                self.error_occurred.emit(f"DM silme işleminde hata: {str(e)}")
                self.finished_deletion.emit()

    async def delete_messages(self, channel_id):
        headers = {
            "Authorization": await self.get_token(),
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as resp:
                if resp.status != 200:
                    self.error_occurred.emit("Kullanıcı bilgileri alınamadı")
                    self.finished_deletion.emit()
                    return
                user_data = await resp.json()
                user_id = user_data["id"]

            self.deleted_count = 0
            last_message_id = None
            
            while True and self._is_running:
                url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=100"
                if last_message_id:
                    url += f"&before={last_message_id}"
                
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            break
                        
                        messages = await resp.json()
                        if not messages:
                            break
                        
                        total_messages = len([m for m in messages if m["author"]["id"] == user_id])
                        current_progress = 0
                        
                        for msg in messages:
                            if not self._is_running:
                                self.message_deleted.emit(f"İşlem durduruldu! Toplam {self.deleted_count} mesaj silindi.")
                                self.finished_deletion.emit()
                                return
                                
                            last_message_id = msg["id"]
                            if msg["author"]["id"] == user_id:
                                # Mesaj silme işlemini dene
                                success = await self.delete_message(session, channel_id, msg["id"])
                                if success:
                                    self.deleted_count += 1
                                    self.total_deleted += 1
                                    current_progress += 1
                                    self.message_deleted.emit(f"✓ Silinen mesaj: {msg['content'][:50]}...")
                                    self.progress_update.emit(current_progress, total_messages)
                                else:
                                    # Mesaj silinemedi, hata mesajı zaten delete_message'da gönderildi
                                    self.message_deleted.emit(f"✗ Silinemedi: {msg['content'][:50]}...")
                                    current_progress += 1
                                    self.progress_update.emit(current_progress, total_messages)
                                await asyncio.sleep(1.3)
                
                except Exception as e:
                    self.error_occurred.emit(f"Mesaj silinirken hata: {str(e)}")
                    await asyncio.sleep(1.5)

            if not self.delete_all:
                self.message_deleted.emit(f"DM silme işlemi tamamlandı!\n✓ Başarıyla silinen: {self.deleted_count} mesaj")
                self.finished_deletion.emit()

    async def main(self):
        if not await self.get_token():
            return
        
        if not self.selected_channel and not self.delete_all:
            await self.get_dm_channels()
        elif self.delete_all:
            await self.delete_all_dms()
        else:
            await self.delete_messages(self.selected_channel)

class DiscordMessageManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CECEN DM Cleaner")
        self.setMinimumSize(1000, 700)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None
        self.dm_channels = {}
        self.all_users = []
        self.token = None
        # Worker'ları başlat
        self.token_worker = TokenWorker()
        self.token_worker.token_ready.connect(self.on_token_ready)
        self.worker = DiscordWorker(self)
        self.worker.dm_list_ready.connect(self.update_dm_list)
        self.worker.message_deleted.connect(self.log_message)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.dm_loading_progress.connect(self.update_loading_progress)
        self.worker.finished_deletion.connect(self.on_deletion_finished)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #23272A;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.init_ui()
        self.initialize_app()

    def initialize_app(self):
        self.token_worker.start()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralwidget")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        # Custom Title Bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet('''
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #181828, stop:1 #232336);
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
        ''')
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(16, 0, 8, 0)
        title_bar_layout.setSpacing(0)
        self.title_label = QLabel("CECEN DM Cleaner")
        self.title_label.setStyleSheet("color: #7289DA; font-size: 24px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        self.min_btn = QPushButton("–")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setStyleSheet('''
            QPushButton {
                color: #7289DA;
                background: transparent;
                border: none;
                font-size: 20px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #232336;
            }
        ''')
        self.min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(self.min_btn)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet('''
            QPushButton {
                color: #7289DA;
                background: transparent;
                border: none;
                font-size: 20px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #e94560;
            }
        ''')
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn)
        layout.addWidget(self.title_bar)
        # Main Title (no card)
        self.main_title = QLabel("CECEN DM Cleaner")
        self.main_title.setStyleSheet("color: #7289DA; font-size: 32px; font-weight: bold; padding: 10px 0 20px 0; font-family: 'Segoe UI', Arial;")
        self.main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.main_title)
        # Set main window and cards to the same semi-transparent dark gray, remove all shadows
        self.setStyleSheet(self.styleSheet() + """
            QMainWindow, QWidget#centralwidget {
                background: rgba(30,30,30,0.75);
            }
            QFrame, QListWidget, QLineEdit, QProgressBar, QLabel {
                background-color: rgba(30,30,30,0.75);
                border: none;
                border-radius: 0px;
                box-shadow: none;
            }
            QListWidget::item:selected {
                background: #3B185F;
                color: #fff;
            }
        """)
        # Ana Container
        main_container = QHBoxLayout()
        main_container.setSpacing(15)
        # Sol Panel - DM Listesi Frame
        dm_frame = ModernFrame()
        dm_layout = QVBoxLayout(dm_frame)
        dm_layout.setSpacing(8)
        dm_layout.setContentsMargins(10, 10, 10, 10)
        # Başlık ve Arama Kutusu
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        dm_label = QLabel("DM List:")
        dm_label.setStyleSheet("""
            QLabel {
                color: #7289DA;
                font-size: 18px;
                margin-bottom: 5px;
            }
        """)
        header_layout.addWidget(dm_label)
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #43B581;
                font-size: 12px;
                font-weight: normal;
                margin: 0;
            }
        """)
        header_layout.addWidget(self.loading_label)
        self.search_box = ModernSearchBox()
        self.search_box.setFixedHeight(40)
        self.search_box.textChanged.connect(self.filter_dm_list)
        header_layout.addWidget(self.search_box)
        search_container = QHBoxLayout()
        search_container.setContentsMargins(0, 5, 0, 5)
        search_container.addWidget(self.search_box)
        header_layout.addLayout(search_container)
        dm_layout.addLayout(header_layout, 0)
        self.dm_list = ModernListWidget()
        self.dm_list.setMinimumWidth(300)
        dm_layout.addWidget(self.dm_list, 1)
        main_container.addWidget(dm_frame, 40)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        button_frame = ModernFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 10, 10, 10)
        self.delete_selected_btn = ModernButton("Sil", QStyle.StandardPixmap.SP_DialogOkButton)
        self.delete_all_btn = ModernButton("Tüm DM'leri Sil", QStyle.StandardPixmap.SP_DialogYesButton)
        self.refresh_btn = ModernButton("Yenile", QStyle.StandardPixmap.SP_BrowserReload)
        self.stop_btn = ModernButton("Durdur", QStyle.StandardPixmap.SP_DialogCancelButton)
        for btn in [self.delete_selected_btn, self.delete_all_btn, self.refresh_btn, self.stop_btn]:
            btn.setFixedHeight(40)
            btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.delete_selected_btn)
        button_layout.addWidget(self.delete_all_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.stop_btn)
        right_panel.addWidget(button_frame, 0)
        progress_frame = ModernFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        right_panel.addWidget(progress_frame, 0)
        log_frame = ModernFrame()
        log_layout = QVBoxLayout(log_frame)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_label = QLabel("Log")
        log_label.setStyleSheet("""
            QLabel {
                color: #7289DA;
                font-size: 18px;
                margin-bottom: 5px;
            }
        """)
        log_layout.addWidget(log_label, 0)
        self.log_list = ModernListWidget(is_log=True)
        log_layout.addWidget(self.log_list, 1)
        right_panel.addWidget(log_frame, 1)
        main_container.addLayout(right_panel, 60)
        layout.addLayout(main_container, 1)
        copyright_container = QHBoxLayout()
        copyright_label = QLabel("Copyright © 2025 - Developed by copief")
        copyright_label.setStyleSheet("""
            QLabel {
                color: rgba(114, 137, 218, 0.5);
                font-size: 12px;
                font-family: 'Segoe UI', Arial;
                font-weight: 500;
                padding: 5px 10px;
                background-color: rgba(44, 47, 51, 0.7);
                border-radius: 15px;
                border: 1px solid rgba(114, 137, 218, 0.2);
            }
        """)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        copyright_container.addStretch()
        copyright_container.addWidget(copyright_label)
        layout.addLayout(copyright_container, 0)
        self.delete_selected_btn.clicked.connect(self.delete_selected_messages)
        self.delete_all_btn.clicked.connect(self.delete_all_messages)
        self.refresh_btn.clicked.connect(self.load_dm_list)
        self.stop_btn.clicked.connect(self.stop_deletion)

    def load_dm_list(self):
        if not self.token:
            self.show_error("Token bulunamadı!")
            return
        self.dm_list.clear()
        self.log_list.clear()
        self.progress_bar.setVisible(False)
        self.worker.selected_channel = None
        self.worker.delete_all = False
        self.worker._is_running = True
        self.worker.start()

    def update_dm_list(self, dm_list):
        self.dm_channels = {}
        self.all_users = []
        self.dm_list.clear()
        for dm in dm_list:
            self.dm_channels[dm['username']] = dm['id']
            self.all_users.append(dm['username'])
            item = QListWidgetItem()
            user_widget = UserListItem(dm['username'], dm['avatar'])
            item.setSizeHint(user_widget.sizeHint())
            self.dm_list.addItem(item)
            self.dm_list.setItemWidget(item, user_widget)

    def filter_dm_list(self, search_text):
        search_text = search_text.lower()
        for i in range(self.dm_list.count()):
            item = self.dm_list.item(i)
            widget = self.dm_list.itemWidget(item)
            username = widget.username_label.text()
            item.setHidden(search_text not in username.lower())
        visible_items = [i for i in range(self.dm_list.count()) if not self.dm_list.item(i).isHidden()]
        if len(visible_items) == 1:
            self.dm_list.setCurrentRow(visible_items[0])

    def delete_selected_messages(self):
        current_item = self.dm_list.currentItem()
        if not current_item:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Uyarı")
            dialog.setText("Lütfen bir DM seçin!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("Tamam")
            dialog.exec()
            return
        widget = self.dm_list.itemWidget(current_item)
        if not widget:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Uyarı")
            dialog.setText("Seçili kullanıcı bulunamadı!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("Tamam")
            dialog.exec()
            return
        username = widget.username_label.text()
        if not username or username not in self.dm_channels:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Uyarı")
            dialog.setText("Seçili kullanıcının DM kanalı bulunamadı!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("Tamam")
            dialog.exec()
            return
        channel_id = self.dm_channels[username]
        reply = show_confirmation_dialog(self, "Onay", f"{username} ile olan tüm mesajlarınız silinecek. Emin misiniz?")
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message("Bekleyin, işlem başlatılıyor...")
            self.start_deletion(channel_id)

    def delete_all_messages(self):
        if not self.token:
            self.show_error("Token bulunamadı! Lütfen Discord'u yeniden başlatın.")
            return
        reply = show_confirmation_dialog(self, "Onay", "Tüm DM'lerdeki mesajlarınız silinecek. Emin misiniz?")
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message("Bekleyin, işlem başlatılıyor...")
            self.start_deletion(None, delete_all=True)

    def start_deletion(self, channel_id=None, delete_all=False):
        self.progress_bar.setVisible(True)
        self.log_list.clear()
        self.worker.selected_channel = channel_id
        self.worker.delete_all = delete_all
        self.worker._is_running = True
        self.worker.start()
        self.delete_selected_btn.setEnabled(False)
        self.delete_all_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_deletion(self):
        self.worker.stop()
        self.stop_btn.setEnabled(False)

    def log_message(self, message):
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def show_error(self, error_message):
        dialog = ModernMessageBox(self)
        dialog.setWindowTitle("Hata")
        dialog.setText(error_message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText("Tamam")
        dialog.exec()

    def update_loading_progress(self, current, total):
        self.loading_label.setText(f"DM'ler yükleniyor... ({current}/{total})")
        if current == total:
            self.loading_label.setText("DM'ler yüklendi!")
            QTimer.singleShot(2000, lambda: self.loading_label.setText(""))

    def on_token_ready(self, token):
        self.token = token
        self.worker.set_token(token)
        self.load_dm_list()

    def on_deletion_finished(self):
        self.delete_selected_btn.setEnabled(True)
        self.delete_all_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self._drag_pos = None

async def get_discord_token():
    ROAMING = os.getenv('APPDATA')
    DISCORD_PATHS = [
        os.path.join(ROAMING, "Discord"),
        os.path.join(ROAMING, "discordcanary"),
        os.path.join(ROAMING, "discordptb")
    ]
    tokens = []
    try:
        for DISCORD_PATH in DISCORD_PATHS:
            if os.path.exists(DISCORD_PATH):
                # Local State'den şifreleme anahtarını al
                local_state_path = os.path.join(DISCORD_PATH, "Local State")
                if os.path.exists(local_state_path):
                    with open(local_state_path, "r", encoding="utf-8") as file:
                        key = json.loads(file.read())["os_crypt"]["encrypted_key"]
                        key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
                else:
                    continue
                leveldb_path = os.path.join(DISCORD_PATH, "Local Storage", "leveldb")
                if os.path.exists(leveldb_path):
                    for file_name in os.listdir(leveldb_path):
                        if file_name.endswith(".log") or file_name.endswith(".ldb"):
                            try:
                                with open(os.path.join(leveldb_path, file_name), "r", errors="ignore") as file:
                                    for line in file.readlines():
                                        for token in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                                            try:
                                                token = base64.b64decode(token.split('dQw4w9WgXcQ:')[1].encode())
                                                cipher = AES.new(key, AES.MODE_GCM, token[3:15])
                                                decrypted_token = cipher.decrypt(token[15:])[:-16].decode()
                                                if decrypted_token not in [t["token"] for t in tokens] and await validate_token(decrypted_token):
                                                    tokens.append({"token": decrypted_token, "source": "browser"})
                                            except Exception as e:
                                                continue
                                        for token in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}", line):
                                            if token not in [t["token"] for t in tokens] and await validate_token(token):
                                                tokens.append({"token": token, "source": "browser"})
                            except Exception as e:
                                continue
                else:
                    pass
            else:
                pass
    except Exception as e:
        pass
    return [t["token"] for t in tokens]

async def validate_token(token):
    try:
        headers = {"Authorization": token}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as response:
                return response.status == 200
    except:
        return False

# --- End DiscordMessageManager and get_discord_token --- 

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ModernFrame {
                background-color: #2C2F33;
                border-radius: 15px;
                padding: 15px;
                margin: 8px;
                border: 1px solid rgba(114, 137, 218, 0.3);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2C2F33, 
                    stop:0.5 #2F3136, 
                    stop:1 #2C2F33
                );
            }
        """)

class ModernButton(QPushButton):
    def __init__(self, text, icon_name=None, parent=None):
        QPushButton.__init__(self, text, parent)
        self.setStyleSheet("""
            QPushButton {
                background: #3B185F;
                color: #fff;
                border: none;
                padding: 10px 22px;
                border-radius: 6px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 15px;
                letter-spacing: 0.2px;
                margin: 2px;
                transition: background 0.15s;
            }
            QPushButton:hover {
                background: #5B21B6;
                color: #fff;
            }
            QPushButton:pressed {
                background: #2A1242;
                color: #fff;
            }
            QPushButton:disabled {
                background: #444851;
                color: #bbb;
                opacity: 0.7;
            }
        """)
        if icon_name:
            self.setIcon(self.style().standardIcon(icon_name))
            self.setIconSize(QSize(20, 20))

class UserListItem(QWidget):
    def __init__(self, username, avatar_url=None, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 6px;
            }
        """)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        self.selection_indicator = QLabel(self)
        self.selection_indicator.setFixedSize(4, 30)
        self.selection_indicator.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: 2px;
            }
        """)
        container_layout.addWidget(self.selection_indicator)
        self.avatar_label = QLabel(self)
        self.avatar_label.setFixedSize(36, 36)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #40444B;
                border-radius: 18px;
                border: 2px solid #202225;
            }
        """)
        if avatar_url:
            self.load_avatar(avatar_url)
        container_layout.addWidget(self.avatar_label)
        self.username_label = QLabel(username, self)
        self.username_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
                font-weight: 500;
                letter-spacing: 0.3px;
            }
        """)
        container_layout.addWidget(self.username_label)
        container_layout.addStretch()
        layout.addWidget(self.container)
        self.setLayout(layout)
    def load_avatar(self, avatar_url):
        try:
            image = QImage()
            image.loadFromData(avatar_url)
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label.setPixmap(scaled_pixmap)
        except Exception as e:
            pass
    def setSelected(self, selected):
        if selected:
            self.container.setStyleSheet("""
                QFrame {
                    background-color: #3B185F;
                    border-radius: 6px;
                }
            """)
            self.selection_indicator.setStyleSheet("""
                QLabel {
                    background-color: #43B581;
                    border-radius: 2px;
                }
            """)
            self.username_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 14px;
                    font-family: 'Segoe UI', Arial;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                }
            """)
        else:
            self.container.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 6px;
                }
            """)
            self.selection_indicator.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border-radius: 2px;
                }
            """)
            self.username_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 14px;
                    font-family: 'Segoe UI', Arial;
                    font-weight: 500;
                    letter-spacing: 0.3px;
                }
            """)

class ModernListWidget(QListWidget):
    def __init__(self, is_log=False, parent=None):
        QListWidget.__init__(self, parent)
        base_style = """
            QListWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #36393F, stop:1 #2F3136);
                border: 1px solid rgba(114, 137, 218, 0.3);
                border-radius: 10px;
                padding: 5px;
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 2px;
                border-radius: 6px;
                margin: 1px;
                background-color: transparent;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(114, 137, 218, 0.1);
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(47, 49, 54, 0.8);
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #202225, stop:1 #2F3136);
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #18191c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """
        if is_log:
            base_style += """
                QListWidget::item {
                    background-color: rgba(44, 47, 51, 0.8);
                    border-left: 4px solid #43B581;
                    padding: 12px;
                    margin: 5px 2px;
                    font-family: 'Segoe UI', Arial;
                    font-size: 13px;
                    letter-spacing: 0.2px;
                    border-radius: 4px;
                }
                QListWidget::item:contains("hata") {
                    border-left-color: #F04747;
                    background-color: rgba(240, 71, 71, 0.1);
                }
                QListWidget::item:contains("durduruldu") {
                    border-left-color: #FAA61A;
                    background-color: rgba(250, 166, 26, 0.1);
                }
                QListWidget::item:contains("Toplam") {
                    border-left-color: #7289DA;
                    background-color: rgba(114, 137, 218, 0.1);
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                QListWidget::item:contains("Bekleyin") {
                    border-left-color: #FAA61A;
                    background-color: rgba(250, 166, 26, 0.1);
                    font-weight: bold;
                }
            """
        self.setStyleSheet(base_style)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWordWrap(True)
        if not is_log:
            self.setIconSize(QSize(40, 40))
            self.setSpacing(2)
            self.itemSelectionChanged.connect(self.updateSelection)
    def updateSelection(self):
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, UserListItem):
                widget.setSelected(item.isSelected())

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        QProgressBar.__init__(self, parent)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #40444B,
                    stop:0.5 #3B3F45,
                    stop:1 #36393F
                );
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #43B581,
                    stop:0.5 #40A877,
                    stop:1 #3CA374
                );
                border-radius: 5px;
            }
        """)

class ModernSearchBox(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #40444B, 
                    stop:0.5 #3B3F45, 
                    stop:1 #36393F
                );
                border: 2px solid #202225;
                border-radius: 8px;
                padding: 8px 12px 8px 36px;
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                letter-spacing: 0.3px;
                margin: 2px;
                selection-background-color: #7289DA;
            }
            QLineEdit:focus {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4A4D57, 
                    stop:0.5 #454852, 
                    stop:1 #40444B
                );
                border: 2px solid #7289DA;
                margin: 0px;
                padding: 10px 14px 10px 38px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.setPlaceholderText("Kullanıcı ara...")
        self.search_icon = QLabel(self)
        self.search_icon.setStyleSheet("""
            QLabel {
                padding: 0;
                margin: 0;
            }
        """)
        self.search_icon.setText("🔍")
        self.search_icon.setFixedSize(20, 20)
    def resizeEvent(self, event):
        padding = 12
        self.search_icon.move(padding, (self.height() - self.search_icon.height()) // 2)
        super().resizeEvent(event)

class ModernMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QMessageBox {
                background-color: #36393F;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #7289DA;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5B73C7;
            }
            QPushButton:pressed {
                background-color: #4A5F9E;
            }
            QPushButton[text="Hayır"] {
                background-color: #d83c3e;
            }
            QPushButton[text="Hayır"]:hover {
                background-color: #b33436;
            }
        """) 

def show_confirmation_dialog(parent, title, message):
    dialog = ModernMessageBox(parent)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    dialog.button(QMessageBox.StandardButton.Yes).setText("Evet")
    dialog.button(QMessageBox.StandardButton.No).setText("Hayır")
    return dialog.exec() 