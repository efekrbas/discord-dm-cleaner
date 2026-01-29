# Discord DM Cleaner

A modern, user-friendly Discord DM (Direct Message) cleaning tool with a beautiful GUI interface. Delete your Discord messages efficiently and safely.

![DM Cleaner](https://img.shields.io/badge/Version-1.0-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🎨 **Modern GUI Interface** - Beautiful, Discord-themed user interface built with PyQt6
- 🔍 **Search Functionality** - Quickly find specific users in your DM list
- 🗑️ **Selective Deletion** - Delete messages from specific users or all DMs at once
- 📊 **Progress Tracking** - Real-time progress bar and detailed logs
- 🔐 **Auto Token Detection** - Automatically detects and uses your Discord token
- 🎮 **Discord Rich Presence** - Shows your activity on Discord
- ⚡ **Fast & Efficient** - Optimized deletion process with rate limit handling
- 🛡️ **Safe Operation** - Only deletes your own messages, respects system messages

## 📋 Requirements

- Python 3.8 or higher
- Windows OS (uses Windows-specific token extraction)
- Discord desktop application installed
- Active Discord account

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/efekrbas/discord-dm-cleaner.git
   cd discord-dm-cleaner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.pyw
   ```

## 📖 Usage

### Getting Started

1. **Launch the application** - Run `main.pyw` to start DM Cleaner
2. **Login** - The application will automatically detect your Discord token, or you can manually enter it
3. **Select DMs** - Browse your DM list and select the conversation you want to clean
4. **Delete Messages** - Choose to delete messages from a specific user or all DMs

### Features Guide

#### Search Users
- Use the search box at the top of the DM list to quickly find specific users
- The list filters in real-time as you type

#### Delete Selected DM
- Select a user from the DM list
- Click the **"Delete"** button
- Confirm the action
- Watch the progress bar and logs for real-time updates

#### Delete All DMs
- Click the **"Delete All DMs"** button
- Confirm the action (this will delete messages from ALL your DMs)
- Monitor the progress across all conversations

#### Stop Operation
- Click the **"Stop"** button at any time to halt the deletion process
- The application will safely stop after completing the current message

#### Refresh DM List
- Click the **"Refresh"** button to reload your DM list
- Useful if you've received new messages or want to update the list

## ⚙️ Configuration

### Discord Rich Presence

The application includes Discord Rich Presence support. To customize it:

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Get your Application ID
3. Update the `client_id` in `main.pyw` (line 24):
   ```python
   def __init__(self, client_id="YOUR_APPLICATION_ID"):
   ```

### Token Detection

The application automatically detects Discord tokens from:
- Discord (stable)
- Discord Canary
- Discord PTB

If automatic detection fails, you can manually enter your token in the login window.

## 🔒 Security & Privacy

- **Local Only** - All operations run locally on your computer
- **No Data Collection** - The application doesn't collect or transmit any data
- **Token Security** - Your token is only used for API calls and never stored
- **Message Safety** - Only your own messages are deleted, never others' messages

## ⚠️ Important Notes

- **Irreversible Action** - Deleted messages cannot be recovered
- **Rate Limits** - The application respects Discord's rate limits automatically
- **System Messages** - System messages (calls, polls, etc.) are automatically skipped
- **Token Safety** - Never share your Discord token with anyone
- **Backup Recommended** - Consider backing up important messages before bulk deletion

## Images

<p align="left">
  <img src="https://github.com/efekrbas/discord-dm-cleaner/blob/main/images/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-11-30%20032339.png">
  </p>
  <p align="left">
  <img src="https://github.com/efekrbas/discord-dm-cleaner/blob/main/images/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-11-30%20033831.png">
</p>

<p align="left">
<img src="https://github.com/efekrbas/discord-dm-cleaner/blob/main/images/Ekran%20görüntüsü%202025-11-30%2004425.png">
</p>

## 🐛 Troubleshooting

### Token Not Found
- Make sure Discord desktop app is installed and you're logged in
- Try restarting Discord
- Manually enter your token in the login window

### Rate Limit Errors
- The application handles rate limits automatically
- If you see rate limit messages, wait for the automatic retry
- Consider deleting in smaller batches

### Application Won't Start
- Check Python version: `python --version` (should be 3.8+)
- Verify all dependencies are installed: `pip list`
- Check for error messages in the console

### GUI Not Displaying
- Ensure PyQt6 is installed: `pip install PyQt6`
- Try running with administrator privileges
- Check Windows display settings

## 🛠️ Building Executable

To create a standalone executable:

```bash
pyinstaller --onefile --windowed --icon=nike.ico main.pyw
```

Or use the provided build scripts:
- `build_simple.bat` - Simple build
- `build_advanced.py` - Advanced build with options

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Credits

**Developed by:** Efe Kırbaş

**Copyright © 2025**

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions

## 🙏 Acknowledgments

- Discord API for providing the platform
- PyQt6 for the GUI framework
- All contributors and users of this tool

---

**Disclaimer:** This tool is for personal use only. Use responsibly and in accordance with Discord's Terms of Service. The developers are not responsible for any misuse of this application.
