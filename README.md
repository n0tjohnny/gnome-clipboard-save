# Clipboard Saver for GNOME

A simple Python 3 utility that saves clipboard text into files using customizable hotkeys in the GNOME desktop environment.  
It supports both quick saves (automatic filenames) and custom saves (filename dialog with Zenity).

---

## Features
- Save clipboard content with hotkeys  
- Two save modes: **Quick** and **Custom**  
- Zenity dialog for custom filenames  
- Template-based automatic filenames  
- Configurable JSON file  
- Compatible with Wayland (`wl-clipboard`), X11 (`xclip`), or Python (`pyperclip`)  

---

## Installation

### Prerequisites
- Python 3.6 or higher  
- GNOME desktop  
- One of the clipboard utilities:
  - `wl-clipboard` for Wayland  
  - `xclip` for X11  
  - or Python package `pyperclip`

### System dependencies (for dialogs and notification)
- For Debian/Ubuntu:
`sudo apt update && sudo apt install zenity libnotify-bin wl-clipboard`

- For Fedora/RHEL:
`sudo dnf install zenity libnotify wl-clipboard`

Also recommended:
- `zenity` (for dialogs)
- `libnotify` (for notifications)

### Setup

1. Copy the script `gnome-clipboard-save.py` to a directory of your choice.  
2. Make it executable:  
   `chmod +x gnome-clipboard-save.py`  
3. Optionally create a default configuration file:  
   `./gnome-clipboard-save.py --init-config`  

This creates a config file at:  
`~/.config/clipboard-saver/config.json`

---

## Hotkey Configuration

Create two GNOME custom shortcuts:

### Quick Save
- **Name:** Clipboard Quick Save  
- **Command:** `/full/path/to/gnome-clipboard-save.py`  
- **Shortcut:** Ctrl+Alt+S  

### Custom Save
- **Name:** Clipboard Custom Save  
- **Command:** `/full/path/to/gnome-clipboard-save.py --custom`  
- **Shortcut:** Ctrl+Alt+F  

To configure:  
`Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts`

---

## Configuration

Edit `~/.config/clipboard-saver/config.json`

```json
{
  "save_dir": "~/Documents/clipboard_saves",
  "file_template": "clip_{date}_{time}_{text}.txt",
  "max_filename_length": 50,
  "notifications": true,
  "log_level": "INFO"
}
