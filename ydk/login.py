import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QDialog, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPixmap, QImage
from app_core import DiscordMessageManager, get_discord_token
import aiohttp

class TokenLoaderThread(QThread):
    tokens_loaded = pyqtSignal(list)
    def run(self):
        import asyncio
        try:
            tokens = asyncio.run(get_discord_token())
        except Exception:
            tokens = []
        self.tokens_loaded.emit(tokens)

class TokenListDialog(QDialog):
    def __init__(self, parent=None, tokens=None):
        super().__init__(parent)
        self.setWindowTitle("Aktif Tokenler")
        self.setFixedSize(350, 400)
        self.setStyleSheet('''
            QDialog {
                background-color: #0a0a1a;
                border-radius: 16px;
            }
            QListWidget {
                background: #181828;
                border: none;
                color: #fff;
                font-size: 15px;
                border-radius: 10px;
            }
        ''')
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.tokens = tokens or []
        if not self.tokens:
            self.list_widget.addItem(QListWidgetItem("Bilgisayarda aktif token bulunamadı."))
        else:
            self.populate_tokens()

    def populate_tokens(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        items = loop.run_until_complete(self._fetch_all_user_info())
        for user_info in items:
            if user_info is None:
                continue
            item = QListWidgetItem()
            widget = self._create_user_widget(user_info)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    async def _fetch_all_user_info(self):
        results = []
        for token in self.tokens:
            user = await self._fetch_user_info(token)
            if user:
                user['token'] = token
                results.append(user)
        return results

    async def _fetch_user_info(self, token):
        headers = {"Authorization": token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        avatar_url = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.png?size=64" if data.get('avatar') else None
                        avatar_data = None
                        if avatar_url:
                            async with session.get(avatar_url) as avatar_resp:
                                if avatar_resp.status == 200:
                                    avatar_data = await avatar_resp.read()
                        return {"username": data.get("username", "?"), "avatar": avatar_data}
        except Exception:
            pass
        return None

    def _create_user_widget(self, user_info):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        avatar_label = QLabel()
        avatar_label.setFixedSize(44, 44)
        avatar_label.setStyleSheet("border-radius: 22px; background: #232336;")
        if user_info['avatar']:
            image = QImage()
            image.loadFromData(user_info['avatar'])
            pixmap = QPixmap.fromImage(image)
            avatar_label.setPixmap(pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            avatar_label.setText("?")
            avatar_label.setStyleSheet("color: #ff2e63; font-size: 22px; border-radius: 22px; background: #232336;")
        layout.addWidget(avatar_label)
        name_label = QLabel(user_info['username'])
        name_label.setStyleSheet("color: #ff2e63; font-size: 18px; font-weight: bold; margin-left: 10px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(name_label)
        layout.addStretch()
        widget.setStyleSheet('''
            QWidget {
                background: #232336;
                border-radius: 14px;
            }
            QWidget:hover {
                background: #26263a;
            }
        ''')
        widget.setMinimumHeight(56)
        return widget

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Token ile Giriş Yap")
        self.setFixedSize(400, 370)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.init_ui()
        self.tokens_loaded = False
        self.tokens = []
        self._drag_pos = None

    def init_ui(self):
        # Dış frame (tam border-radius ve opak arka plan)
        self.outer_frame = QFrame(self)
        self.outer_frame.setObjectName("outerFrame")
        self.outer_frame.setStyleSheet('''
            QFrame#outerFrame {
                background: #0a0a1a;
                border-radius: 18px;
            }
        ''')
        self.outer_layout = QVBoxLayout(self.outer_frame)
        self.outer_layout.setSpacing(0)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

        # Üst custom bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet('''
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #181828, stop:1 #232336);
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
        ''')
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(16, 0, 8, 0)
        title_bar_layout.setSpacing(0)
        self.title_label = QLabel("Copief DM Cleaner")
        self.title_label.setStyleSheet("color: #ff2e63; font-size: 20px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        self.min_btn = QPushButton("–")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setStyleSheet('''
            QPushButton {
                color: #ff2e63;
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
                color: #ff2e63;
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
        self.outer_layout.addWidget(self.title_bar)

        # İç ana widget (yuvarlatılmış ve paddingli)
        self.inner_widget = QWidget()
        self.inner_widget.setStyleSheet('''
            QWidget {
                background-color: transparent;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }
        ''')
        inner_layout = QVBoxLayout(self.inner_widget)
        inner_layout.setSpacing(18)
        inner_layout.setContentsMargins(20, 18, 20, 20)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token giriniz...")
        self.token_input.setStyleSheet('''
            QLineEdit {
                background: transparent;
                border: 2px solid #ff2e63;
                border-radius: 8px;
                padding: 10px 14px;
                color: #fff;
                font-size: 15px;
                font-family: "Segoe UI", Arial;
            }
            QLineEdit:focus {
                border: 2px solid #e94560;
                background: rgba(255,255,255,0.02);
            }
            QLineEdit::placeholder {
                color: #ff2e63;
                font-size: 15px;
            }
        ''')
        inner_layout.addWidget(self.token_input)

        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f3460, stop:1 #533483);
                color: #ff2e63;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
                font-family: "Segoe UI", Arial;
                padding: 10px 0;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #533483, stop:1 #0f3460);
                color: #fff;
            }
        ''')
        inner_layout.addWidget(self.login_btn)

        self.tokens_btn = QPushButton("Aktif Tokenler")
        self.tokens_btn.setCheckable(True)
        self.tokens_btn.clicked.connect(self.toggle_tokens_section)
        self.tokens_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #232336, stop:1 #181828);
                color: #ff2e63;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
                font-family: "Segoe UI", Arial;
                padding: 10px 0;
                margin-top: 5px;
            }
            QPushButton:hover {
                background: #181828;
                color: #fff;
            }
        ''')
        inner_layout.addWidget(self.tokens_btn)

        # Token list section (hidden by default)
        self.tokens_section = QWidget()
        self.tokens_section.setStyleSheet('''
            QWidget {
                background: #181828;
                border-radius: 10px;
                padding-bottom: 8px;
                padding-top: 8px;
            }
        ''')
        self.tokens_section_layout = QVBoxLayout(self.tokens_section)
        self.tokens_section_layout.setContentsMargins(0, 0, 0, 0)
        self.tokens_list = QListWidget()
        self.tokens_list.setStyleSheet('''
            QListWidget {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 15px;
                margin: 0;
                padding: 0 0 0 0;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                margin: 0 0 8px 0;
                padding: 0;
            }
            QListWidget::item:last-child {
                margin-bottom: 0;
            }
            QListWidget::item:hover {
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        ''')
        self.tokens_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tokens_list.itemDoubleClicked.connect(self.token_item_double_clicked)
        self.tokens_list.itemSelectionChanged.connect(self.update_token_selection_effects)
        self.tokens_section_layout.addWidget(self.tokens_list)
        self.tokens_section.setVisible(False)
        inner_layout.addWidget(self.tokens_section)

        self.outer_layout.addWidget(self.inner_widget)

        # Ana pencere layout'u
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.outer_frame)

        self.setStyleSheet('''
            QWidget#LoginWindow {
                background: transparent;
            }
        ''')

    # Pencereyi sürüklenebilir yap
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

    def toggle_tokens_section(self):
        if self.tokens_section.isVisible():
            self.tokens_section.setVisible(False)
            self.tokens_btn.setChecked(False)
        else:
            self.tokens_section.setVisible(True)
            self.tokens_btn.setChecked(True)
            if not self.tokens_loaded:
                self.load_tokens_async()

    def load_tokens_async(self):
        self.tokens_list.clear()
        self.tokens_list.addItem(QListWidgetItem("Tokenler yükleniyor..."))
        self.tokens_loaded = False
        self.tokens = []
        self.token_loader = TokenLoaderThread()
        self.token_loader.tokens_loaded.connect(self.on_tokens_loaded)
        self.token_loader.start()

    def on_tokens_loaded(self, tokens):
        self.tokens_list.clear()
        self.tokens_loaded = True
        self.tokens = tokens
        max_visible = 5
        self._user_widgets = []
        if tokens:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            items = loop.run_until_complete(self._fetch_all_user_info(tokens))
            for user_info in items:
                if user_info is None:
                    continue
                item = QListWidgetItem()
                widget = self._create_user_widget(user_info)
                item.setSizeHint(widget.sizeHint())
                self.tokens_list.addItem(item)
                self.tokens_list.setItemWidget(item, widget)
                self._user_widgets.append(widget)
            row_height = widget.sizeHint().height() if items else 48
            visible_count = min(len(items), max_visible)
            self.tokens_section.setFixedHeight(visible_count * row_height + 24)
        else:
            self.tokens_list.addItem(QListWidgetItem("Bilgisayarda aktif token bulunamadı."))
            self.tokens_section.setFixedHeight(48)

    def update_token_selection_effects(self):
        for i in range(self.tokens_list.count()):
            item = self.tokens_list.item(i)
            widget = self.tokens_list.itemWidget(item)
            if widget:
                selected = item.isSelected()
                self._set_user_widget_selected(widget, selected)

    def _set_user_widget_selected(self, widget, selected):
        # Seçili kutuda hiçbir ekstra stil uygulanmasın
        widget.setStyleSheet('''
            QWidget {
                background: #232336;
                border-radius: 14px;
            }
            QWidget:hover {
                background: #26263a;
            }
        ''')
        avatar = widget.findChild(QLabel)
        if avatar:
            avatar.setStyleSheet("border-radius: 22px; background: #232336;")
        name = widget.findChildren(QLabel)[1]
        if name:
            name.setStyleSheet("color: #ff2e63; font-size: 18px; font-weight: bold; margin-left: 10px;")

    def _create_user_widget(self, user_info):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        avatar_label = QLabel()
        avatar_label.setFixedSize(44, 44)
        avatar_label.setStyleSheet("border-radius: 22px; background: #232336;")
        if user_info['avatar']:
            image = QImage()
            image.loadFromData(user_info['avatar'])
            pixmap = QPixmap.fromImage(image)
            avatar_label.setPixmap(pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            avatar_label.setText("?")
            avatar_label.setStyleSheet("color: #ff2e63; font-size: 22px; border-radius: 22px; background: #232336;")
        layout.addWidget(avatar_label)
        name_label = QLabel(user_info['username'])
        name_label.setStyleSheet("color: #ff2e63; font-size: 18px; font-weight: bold; margin-left: 10px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(name_label)
        layout.addStretch()
        widget.setStyleSheet('''
            QWidget {
                background: #232336;
                border-radius: 14px;
            }
            QWidget:hover {
                background: #26263a;
            }
        ''')
        widget.setMinimumHeight(56)
        return widget

    async def _fetch_all_user_info(self, tokens):
        results = []
        for token in tokens:
            user = await self._fetch_user_info(token)
            if user:
                user['token'] = token
                results.append(user)
        return results

    async def _fetch_user_info(self, token):
        headers = {"Authorization": token}
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        avatar_url = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.png?size=64" if data.get('avatar') else None
                        avatar_data = None
                        if avatar_url:
                            async with session.get(avatar_url) as avatar_resp:
                                if avatar_resp.status == 200:
                                    avatar_data = await avatar_resp.read()
                        return {"username": data.get("username", "?"), "avatar": avatar_data, "token": token}
        except Exception:
            pass
        return None

    def token_item_double_clicked(self, item):
        row = self.tokens_list.row(item)
        # Find the token for this row
        if self.tokens and row < len(self.tokens):
            token = self.tokens[row]
            self.token_input.setText(token)
            self.login()

    def select_token(self, item):
        token = item.text()
        if "bulunamadı" not in token and "yükleniyor" not in token:
            self.token_input.setText(token)

    def login(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Hata", "Lütfen bir token girin veya listeden seçin.")
            return
        # Token ile ana pencereyi başlat
        self.hide()
        self.main_window = DiscordMessageManager()
        self.main_window.token = token
        self.main_window.worker.set_token(token)
        self.main_window.load_dm_list()
        self.main_window.show()
        self.close()

    def show_tokens(self):
        import asyncio
        tokens = []
        try:
            tokens = asyncio.run(get_discord_token())
        except Exception:
            tokens = []
        dlg = TokenListDialog(self, tokens)
        dlg.exec() 