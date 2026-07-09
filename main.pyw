import asyncio
import json
import aiohttp
import sys
import os
import base64
import re
import win32crypt
import time
import struct
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QListWidget, QLabel, 
                            QProgressBar, QMessageBox, QFrame, QStyle, QLineEdit,
                            QListWidgetItem)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt6.QtGui import QPalette, QColor, QIcon, QPixmap, QImage, QFont
from Crypto.Cipher import AES
from splash import SplashScreen
from app_core import DiscordMessageManager, get_discord_token
from Crypto.Cipher import AES


class DiscordRichPresence:
    def __init__(self, client_id="1417869289922232330"):  # Replace with your Discord application ID
        # To get a Discord application ID:
        # 1. Go to https://discord.com/developers/applications
        # 2. Create a new application or select existing one
        # 3. Copy the Application ID from the General Information tab
        # 4. Replace the client_id above with your application ID
        self.client_id = client_id
        self.is_connected = False
        self.rpc = None
        
    def connect(self):
        """Connect to Discord RPC using pypresence"""
        try:
            from pypresence import Presence
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.is_connected = True
            print("Discord RPC connection successful!")
            return True
        except Exception as e:
            print(f"Discord RPC connection failed: {e}")
            print("Please check if Discord is open!")
            self.is_connected = False
            return False
    
    def set_activity(self, details="Cleaning DMs", state="Deleting messages...", large_image="cover", large_text="DM Cleaner"):
        """Set Discord Rich Presence activity"""
        if not self.is_connected or not self.rpc:
            return False
            
        try:
            # Rate limiting - wait minimum 1 second
            current_time = time.time()
            if hasattr(self, 'last_activity_time'):
                time_diff = current_time - self.last_activity_time
                if time_diff < 1.0:  # Wait if less than 1 second has passed
                    time.sleep(1.0 - time_diff)
            
            self.last_activity_time = time.time()
            
            # Set activity with pypresence
            self.rpc.update(
                details=details,
                state=state,
                large_image=large_image,
                large_text=large_text,
                start=int(time.time())
            )
            return True
        except Exception as e:
            print(f"Failed to set Discord activity: {e}")
            return False
    
    def clear_activity(self):
        """Clear Discord Rich Presence activity"""
        if not self.is_connected or not self.rpc:
            return False
            
        try:
            self.rpc.clear()
            return True
        except Exception as e:
            print(f"Failed to clear Discord activity: {e}")
            return False
    
    def close(self):
        """Close Discord RPC connection"""
        if self.rpc:
            try:
                self.rpc.close()
            except:
                pass
            self.rpc = None
        self.is_connected = False


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
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #7289DA, 
                    stop:0.5 #6981D0, 
                    stop:1 #5B73C7
                );
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                letter-spacing: 0.5px;
                margin: 2px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #5B73C7, 
                    stop:0.5 #526BBF, 
                    stop:1 #4A5F9E
                );
                margin: 0px;
                padding: 12px 22px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4A5F9E, 
                    stop:0.5 #435696, 
                    stop:1 #3B4F8E
                );
                padding: 10px 20px;
                margin: 2px;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
            QPushButton:disabled {
                background-color: #4F545C;
                opacity: 0.7;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        if icon_name:
            self.setIcon(self.style().standardIcon(icon_name))
            self.setIconSize(QSize(18, 18))

class UserListItem(QWidget):
    def __init__(self, username, avatar_url=None, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        # Container widget for background
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

        # Selection indicator
        self.selection_indicator = QLabel(self)
        self.selection_indicator.setFixedSize(4, 30)
        self.selection_indicator.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: 2px;
            }
        """)
        container_layout.addWidget(self.selection_indicator)
        
        # Avatar Label
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
        
        # Username Label
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
            pass#print(f"Avatar yükleme hatası: {e}")

    def setSelected(self, selected):
        if selected:
            self.container.setStyleSheet("""
                QFrame {
                    background-color: #7289DA;
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
        self.setPlaceholderText("Search user...")
        
        # Add search icon
        self.search_icon = QLabel(self)
        self.search_icon.setStyleSheet("""
            QLabel {
                padding: 0;
                margin: 0;
            }
        """)
        # Unicode magnifying glass icon
        self.search_icon.setText("🔍")
        self.search_icon.setFixedSize(20, 20)
        
    def resizeEvent(self, event):
        # Position the icon
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
            QPushButton[text="No"] {
                background-color: #d83c3e;
            }
            QPushButton[text="No"]:hover {
                background-color: #b33436;
            }
        """)

class TokenWorker(QThread):
    token_ready = pyqtSignal(str)
    
    def run(self):
        asyncio.run(self.get_and_save_token())
    
    async def get_and_save_token(self):
        try:
            tokens = await get_discord_token()
            if tokens:
                #print("Token bulundu ve enjekte ediliyor...")
                self.token_ready.emit(tokens[0])
            else:
                pass#print("Token bulunamadı!")
        except Exception as e:
            pass#print(f"Token işlemi hatası: {str(e)}")

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
        
        # Eğer user_id varsa kullanıcı avatarı, yoksa grup ikonu
        if user_id:
            url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png?size=32"
        else:
            # Grup sohbeti ikonu için farklı URL formatı
            url = f"https://cdn.discordapp.com/icons/{avatar_id}.png?size=32"
        
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            print(f"Avatar indirme hatası: {e}")
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
                        self.error_occurred.emit(f"Could not get DM list: HTTP {resp.status}")
                        return
                    
                    channels = await resp.json()
                    
                    # Include all DM types: one-on-one DMs, group chats and other private channels
                    dm_channels = []
                    for channel in channels:
                        channel_type = channel.get("type", 0)
                        # Type 1: One-on-one DM, Type 3: Group DM, Type 0: Text channel (for some special cases)
                        if channel_type in [1, 3] or (channel_type == 0 and "recipients" in channel):
                            dm_channels.append(channel)
                    
                    total_channels = len(dm_channels)
                    
                    dm_list = []
                    for idx, channel in enumerate(dm_channels, 1):
                        self.dm_loading_progress.emit(idx, total_channels)
                        
                        # Determine username based on channel type
                        username = None
                        user_id = None
                        avatar_id = None
                        
                        if channel["type"] == 1:  # One-on-one DM
                            if "recipients" in channel and len(channel["recipients"]) > 0:
                                recipient = channel["recipients"][0]
                                username = recipient.get('global_name') or recipient.get('username', 'Unknown User')
                                user_id = recipient.get("id")
                                avatar_id = recipient.get("avatar")
                        elif channel["type"] == 3:  # Group chat
                            # Check name field for group chat
                            username = channel.get("name")
                            if not username:
                                # If name doesn't exist, create group name from recipients
                                if "recipients" in channel and len(channel["recipients"]) > 0:
                                    recipient_names = [r.get('global_name') or r.get('username', 'Unknown') for r in channel["recipients"][:3]]
                                    username = f"Group: {', '.join(recipient_names)}"
                                    if len(channel["recipients"]) > 3:
                                        username += f" +{len(channel['recipients']) - 3} more"
                                else:
                                    username = "Unknown Group"
                            user_id = None
                            avatar_id = channel.get("icon")
                        elif channel["type"] == 0 and "recipients" in channel:  # Private DM channel
                            if len(channel["recipients"]) == 1:
                                recipient = channel["recipients"][0]
                                username = recipient.get('global_name') or recipient.get('username', 'Unknown User')
                                user_id = recipient.get("id")
                                avatar_id = recipient.get("avatar")
                            else:
                                username = channel.get("name", "Group Chat")
                                user_id = None
                                avatar_id = channel.get("icon")
                        
                        # Assign default value if username is None
                        if username is None:
                            username = "Unknown Channel"
                        
                        avatar_task = asyncio.create_task(
                            self.get_avatar(user_id, avatar_id) if user_id and avatar_id else asyncio.sleep(0)
                        )
                        
                        dm_list.append({
                            'username': username,
                            'id': channel['id'],
                            'user_id': user_id,  # Also save user ID
                            'avatar': await avatar_task if user_id and avatar_id else None,
                            'type': channel["type"]
                        })
                    
                    # Sort usernames safely
                    sorted_dm_list = sorted(dm_list, key=lambda x: x['username'].lower() if x['username'] else '')
                    self.dm_list_ready.emit(sorted_dm_list)
                    
            except Exception as e:
                self.error_occurred.emit(f"Error occurred while getting DM list: {str(e)}")
            finally:
                self._session = None

    async def delete_message(self, session, channel_id, message_id, is_call_message=False):
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
                    self.message_deleted.emit(f"Rate limit exceeded, waiting {retry_after:.1f} seconds...")
                    await asyncio.sleep(retry_after + 1.1)
                    return await self.delete_message(session, channel_id, message_id, is_call_message)
                elif resp.status == 403:
                    if not is_call_message:
                        self.message_deleted.emit(f"Message could not be deleted: No permission (403) - Message ID: {message_id}")
                    return False
                elif resp.status == 404:
                    if not is_call_message:
                        self.message_deleted.emit(f"Message not found (404) - Message ID: {message_id}")
                    return False
                elif resp.status == 400:
                    if not is_call_message:
                        error_text = await resp.text()
                        self.message_deleted.emit(f"Invalid request (400) - Message ID: {message_id} - Error: {error_text}")
                    return False
                else:
                    if not is_call_message:
                        error_text = await resp.text()
                        self.message_deleted.emit(f"Message could not be deleted: HTTP {resp.status} - Message ID: {message_id} - Error: {error_text}")
                    return False
        except Exception as e:
            if not is_call_message:
                self.message_deleted.emit(f"Error occurred while deleting message: {str(e)} - Message ID: {message_id}")
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
                        self.error_occurred.emit(f"Could not get DM list: HTTP {resp.status}")
                        return
                    
                    channels = await resp.json()
                    
                    # Include all DM types
                    dm_channels = []
                    for channel in channels:
                        channel_type = channel.get("type", 0)
                        if channel_type in [1, 3] or (channel_type == 0 and "recipients" in channel):
                            dm_channels.append(channel)
                    
                    self.total_dm_count = len(dm_channels)
                    self.message_deleted.emit(f"Found {self.total_dm_count} DM boxes. Deletion process starting...")
                    
                    for i, channel in enumerate(dm_channels, 1):
                        if not self._is_running:
                            self.message_deleted.emit(
                                f"Process stopped!\n"
                                f"Last operation: Stopped at DM with {self.current_username}.\n"
                                f"Total {self.completed_dms}/{self.total_dm_count} DM boxes cleaned.\n"
                                f"Total {self.total_deleted} messages deleted."
                            )
                            self.finished_deletion.emit()
                            return
                        
                        # Determine username based on channel type
                        if channel["type"] == 1:  # One-on-one DM
                            if "recipients" in channel and len(channel["recipients"]) > 0:
                                self.current_username = channel["recipients"][0].get("username", "Unknown User")
                            else:
                                self.current_username = "Unknown User"
                        elif channel["type"] == 3:  # Group chat
                            self.current_username = channel.get("name", "Unknown Group")
                        elif channel["type"] == 0 and "recipients" in channel:  # Private DM channel
                            if len(channel["recipients"]) == 1:
                                self.current_username = channel["recipients"][0].get("username", "Unknown User")
                            else:
                                self.current_username = channel.get("name", "Group Chat")
                        else:
                            self.current_username = "Unknown Channel"
                        
                        self.current_dm_index = i
                        self.message_deleted.emit(f"DM Box {i}/{self.total_dm_count} - Deleting messages with {self.current_username}...")
                        
                        # Save message count in this DM
                        messages_before = self.deleted_count
                        await self.delete_messages(channel["id"])
                        messages_deleted_in_this_dm = self.deleted_count - messages_before
                        self.completed_dms += 1
                        self.message_deleted.emit(f"✓ {messages_deleted_in_this_dm} messages deleted with {self.current_username}.")
                        
                        if not self._is_running:
                            break
                    
                    self.message_deleted.emit(
                        f"🎉 All DMs cleaned!\n"
                        f"✓ Processed DM boxes: {self.completed_dms}/{self.total_dm_count}\n"
                        f"✓ Total deleted messages: {self.total_deleted}\n"
                        f"✓ Process completed successfully!"
                    )
                    self.finished_deletion.emit()
                    
            except Exception as e:
                self.error_occurred.emit(f"Error in DM deletion process: {str(e)}")
                self.finished_deletion.emit()

    async def delete_messages(self, channel_id):
        headers = {
            "Authorization": await self.get_token(),
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as resp:
                if resp.status != 200:
                    self.error_occurred.emit("Could not get user information")
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
                            self.message_deleted.emit(f"Could not get messages: HTTP {resp.status}")
                            break
                        
                        messages = await resp.json()
                        if not messages:
                            self.message_deleted.emit("No more messages found in this DM.")
                            break
                        
                        # Calculate total message count
                        total_messages = len([m for m in messages if m["author"]["id"] == user_id])
                        current_progress = 0
                        
                        for msg in messages:
                            if not self._is_running:
                                self.message_deleted.emit(f"Process stopped! Total {self.deleted_count} messages deleted.")
                                self.finished_deletion.emit()
                                return
                                
                            last_message_id = msg["id"]
                            if msg["author"]["id"] == user_id:
                                # Check message type
                                content = msg.get("content", "")
                                message_type = msg.get("type", 0)
                                
                                # Check for call messages
                                is_call_message = any(keyword in content.lower() for keyword in [
                                    "started a call", "missed call", "ongoing call", 
                                    "incoming call from", "call", "call"
                                ])
                                
                                # Check for poll messages (comprehensive)
                                is_poll_message = (
                                    # Messages containing embeds
                                    (msg.get("embeds") and len(msg.get("embeds", [])) > 0) or
                                    # Messages containing poll texts
                                    ("Select a response" in content or 
                                     "Show results" in content or
                                     "Vote" in content or
                                     "vote" in content.lower() or
                                     "left" in content.lower()) or
                                    # Messages that are not type 0 but are deletable
                                    (message_type == 0 and not content.strip() and not msg.get("attachments") and not msg.get("sticker_items"))
                                )
                                
                                # Check for system messages
                                is_system_message = (
                                    message_type != 0 or  # Not a normal message
                                    (not content.strip() and not msg.get("attachments") and not msg.get("embeds") and not msg.get("sticker_items")) or  # Empty content, no file, embed or sticker
                                    msg.get("activity") or  # Has activity
                                    msg.get("application") or  # Application message
                                    is_call_message  # Call message
                                )
                                
                                # Poll messages are deletable
                                if is_poll_message:
                                    is_system_message = False
                                
                                if is_system_message:
                                    # Silently skip system messages
                                    current_progress += 1
                                    self.progress_update.emit(current_progress, total_messages)
                                    continue
                                
                                # Delete normal messages
                                success = await self.delete_message(session, channel_id, msg["id"], False)
                                if success:
                                    self.deleted_count += 1
                                    self.total_deleted += 1
                                    current_progress += 1
                                    self.message_deleted.emit(f"✓ Deleted message: {msg['content'][:50]}...")
                                    self.progress_update.emit(current_progress, total_messages)
                                else:
                                    # Message could not be deleted, error message already sent in delete_message
                                    self.message_deleted.emit(f"✗ Could not delete: {msg['content'][:50]}...")
                                    current_progress += 1
                                    self.progress_update.emit(current_progress, total_messages)
                                await asyncio.sleep(1.3)
                
                except Exception as e:
                    self.error_occurred.emit(f"Error while deleting message: {str(e)}")
                    await asyncio.sleep(1.5)

            # When process is completed
            if not self.delete_all:  # If deleting single user DM
                self.message_deleted.emit(f"DM deletion process completed!\n✓ Successfully deleted: {self.deleted_count} messages")
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
        self.setWindowTitle("DM Cleaner")
        self.setMinimumSize(1000, 700)
        
        # Set Application Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.dm_channels = {}
        self.all_users = []
        self.token = None
        
        # Discord Rich Presence
        self.discord_rpc = DiscordRichPresence()
        self.rpc_connected = False
        
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
        
        # Ana pencere stili
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
        # Arka planda token güncelleme işlemini başlat
        self.token_worker.start()
        # Discord Rich Presence'ı 2 saniye sonra başlat (GUI hazır olduktan sonra)
        QTimer.singleShot(2000, self.init_discord_rpc)
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Başlık Alanı
        title_frame = ModernFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)  # Başlık kenar boşluklarını azalttık
        
        title_label = QLabel("DM Cleaner")
        title_label.setStyleSheet("""
            QLabel {
                color: #7289DA;
                font-size: 28px;
                font-weight: bold;
                padding: 5px;
                background-color: #2C2F33;
                border-radius: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        layout.addWidget(title_frame, 0)  # 0 stretch factor
        
        # Ana Container
        main_container = QHBoxLayout()
        main_container.setSpacing(15)
        
        # Sol Panel - DM Listesi Frame
        dm_frame = ModernFrame()
        dm_layout = QVBoxLayout(dm_frame)
        dm_layout.setSpacing(8)  # Boşlukları azalttık
        dm_layout.setContentsMargins(10, 10, 10, 10)  # Kenar boşluklarını azalttık
        
        # Başlık ve Arama Kutusu
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)  # Başlık elemanları arası boşluğu azalttık
        
        dm_label = QLabel("DM List:")
        dm_label.setStyleSheet("""
            QLabel {
                color: #7289DA;
                font-size: 18px;
                margin-bottom: 5px;
            }
        """)
        header_layout.addWidget(dm_label)
        
        # Yükleme durumu etiketi
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
        
        # Arama kutusu
        self.search_box = ModernSearchBox()
        self.search_box.setFixedHeight(40)  # Yüksekliği artırdık
        self.search_box.textChanged.connect(self.filter_dm_list)
        header_layout.addWidget(self.search_box)
        
        # Arama kutusu için container oluştur
        search_container = QHBoxLayout()
        search_container.setContentsMargins(0, 5, 0, 5)  # Üst ve alt boşluk ekle
        search_container.addWidget(self.search_box)
        header_layout.addLayout(search_container)
        
        dm_layout.addLayout(header_layout, 0)  # 0 stretch factor
        
        # DM Listesi
        self.dm_list = ModernListWidget()
        self.dm_list.setMinimumWidth(300)
        dm_layout.addWidget(self.dm_list, 1)  # 1 stretch factor
        
        main_container.addWidget(dm_frame, 40)
        
        # Sağ Panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)  # Boşlukları azalttık
        
        # Butonlar Frame
        button_frame = ModernFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        self.delete_selected_btn = ModernButton("Delete", QStyle.StandardPixmap.SP_DialogOkButton)
        self.delete_all_btn = ModernButton("Delete All DMs", QStyle.StandardPixmap.SP_DialogYesButton)
        self.refresh_btn = ModernButton("Refresh", QStyle.StandardPixmap.SP_BrowserReload)
        self.stop_btn = ModernButton("Stop", QStyle.StandardPixmap.SP_DialogCancelButton)
        
        # Butonların boyutlarını ayarla
        for btn in [self.delete_selected_btn, self.delete_all_btn, self.refresh_btn, self.stop_btn]:
            btn.setFixedHeight(40)  # Yüksekliği sabitledik
            btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.delete_selected_btn)
        button_layout.addWidget(self.delete_all_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.stop_btn)
        right_panel.addWidget(button_frame, 0)  # 0 stretch factor
        
        # İlerleme çubuğu Frame
        progress_frame = ModernFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setFixedHeight(25)  # Yüksekliği sabitledik
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        right_panel.addWidget(progress_frame, 0)  # 0 stretch factor
        
        # Log alanı Frame
        log_frame = ModernFrame()
        log_layout = QVBoxLayout(log_frame)
        log_layout.setSpacing(8)  # Boşlukları azalttık
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        log_label = QLabel("Log")
        log_label.setStyleSheet("""
            QLabel {
                color: #7289DA;
                font-size: 18px;
                margin-bottom: 5px;
            }
        """)
        log_layout.addWidget(log_label, 0)  # 0 stretch factor
        
        self.log_list = ModernListWidget(is_log=True)
        log_layout.addWidget(self.log_list, 1)  # 1 stretch factor
        right_panel.addWidget(log_frame, 1)  # 1 stretch factor
        
        main_container.addLayout(right_panel, 60)
        layout.addLayout(main_container, 1)  # 1 stretch factor
        
        # Copyright Label
        copyright_container = QHBoxLayout()
        copyright_label = QLabel("Copyright © 2025 - Developed by copief and Efe Kırbaş")
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
        layout.addLayout(copyright_container, 0)  # 0 stretch factor
        
        # Buton bağlantıları
        self.delete_selected_btn.clicked.connect(self.delete_selected_messages)
        self.delete_all_btn.clicked.connect(self.delete_all_messages)
        self.refresh_btn.clicked.connect(self.load_dm_list)
        self.stop_btn.clicked.connect(self.stop_deletion)
        
    def load_dm_list(self):
        if not self.token:
            self.show_error("Token not found!")
            return

        # Update Discord activity
        self.update_discord_activity("DM Cleaner Open", "Loading DM list...")

        self.dm_list.clear()
        self.log_list.clear()
        self.progress_bar.setVisible(False)

        # Eski worker'ı durdur ve yeni worker oluştur
        try:
            self.worker.stop()
        except Exception:
            pass

        self.worker = DiscordWorker(self)
        self.worker.set_token(self.token)
        self.worker.dm_list_ready.connect(self.update_dm_list)
        self.worker.message_deleted.connect(self.log_message)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.dm_loading_progress.connect(self.update_loading_progress)
        self.worker.finished_deletion.connect(self.on_deletion_finished)

        self.worker.selected_channel = None
        self.worker.delete_all = False
        self.worker._is_running = True
        self.worker.start()
        
    def update_dm_list(self, dm_list):
        self.dm_channels = {}
        self.all_users = []
        self.dm_list.clear()
        
        for dm in dm_list:
            # Benzersiz key oluştur: username + user_id (eğer varsa)
            unique_key = dm['username']
            if 'user_id' in dm and dm['user_id']:
                unique_key = f"{dm['username']}#{dm['user_id']}"
            
            self.dm_channels[unique_key] = dm['id']
            self.all_users.append(dm['username'])
            
            item = QListWidgetItem()
            user_widget = UserListItem(dm['username'], dm['avatar'])
            item.setSizeHint(user_widget.sizeHint())
            
            # Benzersiz key'i item'a kaydet
            item.setData(Qt.ItemDataRole.UserRole, unique_key)
            
            self.dm_list.addItem(item)
            self.dm_list.setItemWidget(item, user_widget)
        
        # Update Discord activity - DM list loaded
        self.update_discord_activity("DM Cleaner Open", f"{len(dm_list)} DMs found - Ready")
            
    def filter_dm_list(self, search_text):
        search_text = search_text.lower()
        
        for i in range(self.dm_list.count()):
            item = self.dm_list.item(i)
            widget = self.dm_list.itemWidget(item)
            username = widget.username_label.text()
            
            item.setHidden(search_text not in username.lower())
            
        # Eğer tam eşleşen bir sonuç varsa, onu seç
        visible_items = [i for i in range(self.dm_list.count()) if not self.dm_list.item(i).isHidden()]
        if len(visible_items) == 1:
            self.dm_list.setCurrentRow(visible_items[0])
        
    def delete_selected_messages(self):
        current_item = self.dm_list.currentItem()
        if not current_item:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Warning")
            dialog.setText("Please select a DM!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("OK")
            dialog.exec()
            return
            
        # Get username from widget
        widget = self.dm_list.itemWidget(current_item)
        if not widget:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Warning")
            dialog.setText("Selected user not found!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("OK")
            dialog.exec()
            return
            
        # Get unique key from item
        unique_key = current_item.data(Qt.ItemDataRole.UserRole)
        if not unique_key or unique_key not in self.dm_channels:
            dialog = ModernMessageBox(self)
            dialog.setWindowTitle("Warning")
            dialog.setText("Selected user's DM channel not found!")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.button(QMessageBox.StandardButton.Ok).setText("OK")
            dialog.exec()
            return
            
        channel_id = self.dm_channels[unique_key]
        username = widget.username_label.text()
        
        reply = show_confirmation_dialog(
            self,
            "Confirmation",
            f"All your messages with {username} will be deleted. Are you sure?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message("Please wait, starting process...")
            self.start_deletion(channel_id)
            
    def delete_all_messages(self):
        if not self.token:
            self.show_error("Token not found! Please restart Discord.")
            return
            
        reply = show_confirmation_dialog(
            self,
            "Confirmation",
            "All your messages in all DMs will be deleted. Are you sure?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message("Please wait, starting process...")
            self.start_deletion(None, delete_all=True)
            
    def start_deletion(self, channel_id=None, delete_all=False):
        self.progress_bar.setVisible(True)
        self.log_list.clear()
        
        # Update Discord activity
        if delete_all:
            self.update_discord_activity("Cleaning All DMs", "Deleting all messages...")
        else:
            self.update_discord_activity("Cleaning DM", "Deleting messages in selected DM...")
        
        # Eski worker'ı durdur ve yeni worker oluştur
        try:
            self.worker.stop()
        except Exception:
            pass

        self.worker = DiscordWorker(self)
        self.worker.set_token(self.token)
        self.worker.dm_list_ready.connect(self.update_dm_list)
        self.worker.message_deleted.connect(self.log_message)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.dm_loading_progress.connect(self.update_loading_progress)
        self.worker.finished_deletion.connect(self.on_deletion_finished)

        self.worker.selected_channel = channel_id
        self.worker.delete_all = delete_all
        self.worker._is_running = True
        self.worker.start()
        # Butonları güncelle
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
        
        # Update Discord activity
        if "deleting" in message.lower() or "deleted" in message.lower():
            if "Total" in message and "deleted" in message:
                # Process completed
                self.update_discord_activity("DM Cleaning Completed", message)
            else:
                # Process ongoing
                self.update_discord_activity("Cleaning DM", message)
        
    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def show_error(self, error_message):
        dialog = ModernMessageBox(self)
        dialog.setWindowTitle("Error")
        dialog.setText(error_message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText("OK")
        dialog.exec()

    def update_loading_progress(self, current, total):
        self.loading_label.setText(f"Loading DMs... ({current}/{total})")
        if current == total:
            self.loading_label.setText("DMs loaded!")
            QTimer.singleShot(2000, lambda: self.loading_label.setText(""))

    def on_token_ready(self, token):
        #print(f"Token alındı: {token[:25]}...")  # Token'in ilk 25 karakterini göster
        self.token = token
        self.worker.set_token(token)  # Worker'a token'i enjekte et
        self.load_dm_list()

    def on_deletion_finished(self):
        # Butonları tekrar aktif et
        self.delete_selected_btn.setEnabled(True)
        self.delete_all_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        # Clear Discord activity
        self.clear_discord_activity()
    
    def init_discord_rpc(self):
        """Initialize Discord Rich Presence"""
        try:
            print("Establishing Discord RPC connection...")
            # Close old connection
            if self.discord_rpc.rpc:
                try:
                    self.discord_rpc.close()
                except:
                    pass
            
            # Establish new connection
            self.rpc_connected = self.discord_rpc.connect()
            if self.rpc_connected:
                print("Discord RPC connection successful!")
                # Add a short wait
                import time
                time.sleep(1)
                # Set activity
                success = self.discord_rpc.set_activity(
                    details="DM Cleaner Open",
                    state="Loading DM list...",
                    large_image="cover",
                    large_text="DM Cleaner - Message Cleaning Tool"
                )
                if success:
                    print("Discord Rich Presence started")
                else:
                    print("❌ Discord activity could not be set")
            else:
                print("❌ Discord Rich Presence could not be started - Is Discord open?")
        except Exception as e:
            print(f"❌ Discord RPC initialization error: {e}")
            self.rpc_connected = False
    
    def update_discord_activity(self, details, state):
        """Update Discord Rich Presence activity"""
        if not self.rpc_connected:
            print("No Discord RPC connection, activity cannot be updated")
            return
        
        # Prevent sending the same activity again
        if hasattr(self, 'last_activity_details') and hasattr(self, 'last_activity_state'):
            if self.last_activity_details == details and self.last_activity_state == state:
                return
        
        self.last_activity_details = details
        self.last_activity_state = state
        
        try:
            print(f"Updating Discord activity: {details} - {state}")
            success = self.discord_rpc.set_activity(
                details=details,
                state=state,
                large_image="cover",
                large_text="DM Cleaner - Message Cleaning Tool"
            )
            if success:
                print("✅ Discord activity updated")
            else:
                print("❌ Discord activity could not be updated")
        except Exception as e:
            print(f"Discord activity update error: {e}")
    
    def clear_discord_activity(self):
        """Clear Discord Rich Presence activity"""
        if not self.rpc_connected:
            return
        try:
            self.discord_rpc.clear_activity()
        except Exception as e:
            print(f"Discord activity clear error: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.rpc_connected:
            self.clear_discord_activity()
            self.discord_rpc.close()
        event.accept()

def show_confirmation_dialog(parent, title, message):
    dialog = ModernMessageBox(parent)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    dialog.button(QMessageBox.StandardButton.Yes).setText("Yes")
    dialog.button(QMessageBox.StandardButton.No).setText("No")
    return dialog.exec()

async def validate_token(token):
    try:
        headers = {"Authorization": token}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as response:
                return response.status == 200
    except:
        return False

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
                    #print("Local State dosyası bulunamadı!")
                    continue

                leveldb_path = os.path.join(DISCORD_PATH, "Local Storage", "leveldb")
                if os.path.exists(leveldb_path):
                    for file_name in os.listdir(leveldb_path):
                        if file_name.endswith(".log") or file_name.endswith(".ldb"):
                            try:
                                with open(os.path.join(leveldb_path, file_name), "r", errors="ignore") as file:
                                    for line in file.readlines():
                                        # Şifrelenmiş token'ları ara
                                        for token in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                                            try:
                                                token = base64.b64decode(token.split('dQw4w9WgXcQ:')[1].encode())
                                                cipher = AES.new(key, AES.MODE_GCM, token[3:15])
                                                decrypted_token = cipher.decrypt(token[15:])[:-16].decode()
                                                if decrypted_token not in [t["token"] for t in tokens] and await validate_token(decrypted_token):
                                                    tokens.append({"token": decrypted_token, "source": "browser"})
                                            except Exception as e:
                                                continue
                                        # Şifrelenmemiş token'ları ara
                                        for token in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}", line):
                                            if token not in [t["token"] for t in tokens] and await validate_token(token):
                                                tokens.append({"token": token, "source": "browser"})
                            except Exception as e:
                                continue
                else:
                    pass#print("LevelDB klasörü bulunamadı!")
            else:
                pass#print(f"Discord dizini bulunamadı: {DISCORD_PATH}")
    except Exception as e:
        pass#print(f"Token arama hatası: {str(e)}")

    return [t["token"] for t in tokens]


def main():
    app = QApplication(sys.argv)
    
    # Set global application icon
    if hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'images', 'app_icon.png')
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'app_icon.png')
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()