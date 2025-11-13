#!/usr/bin/env python3
"""
Clipboard Saver for GNOME
A simple utility to save clipboard content to files with customizable hotkeys
License: MIT
"""

import os
import sys
import json
import argparse
import pyperclip
from datetime import datetime
from pathlib import Path
import logging
import subprocess
from typing import Optional, Dict, Any

class ClipboardSaver:
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.setup_directories()
        
    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "save_dir": "~/Documents/clipboard_saves",
            "file_template": "clip_{date}_{time}_{text:.15}.txt",
            "max_filename_length": 50,
            "notifications": True,
            "log_level": "INFO",
            "hotkeys": {
                "quick_save": "Ctrl+Alt+S",
                "custom_save": "Ctrl+Alt+F"
            }
        }
        
        if config_path is None:
            config_path = Path.home() / ".config" / "clipboard-saver" / "config.json"
        
        config_path = config_path.expanduser()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.", file=sys.stderr)
        
        return default_config
    
    def setup_logging(self) -> None:
        """Setup logging configuration"""
        log_dir = Path.home() / ".local" / "share" / "clipboard-saver"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_level = getattr(logging, self.config["log_level"].upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "clipboard_saver.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("clipboard-saver")
    
    def setup_directories(self) -> None:
        """Create necessary directories"""
        self.save_dir = Path(self.config["save_dir"]).expanduser()
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Save directory: {self.save_dir}")
    
    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filenames"""
        # Remove or replace characters that are problematic in filenames
        sanitized = "".join(
            c if c.isalnum() or c in (' ', '-', '_', '.') else '_' 
            for c in text
        )
        # Limit length
        max_len = self.config["max_filename_length"]
        return sanitized[:max_len].strip()
    
    def create_filename(self, text: str) -> str:
        """Create filename based on template and clipboard content"""
        sanitized_text = self.sanitize_filename(text)
        
        template_vars = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H-%M-%S"),
            "datetime": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": str(int(datetime.now().timestamp())),
            "text": sanitized_text or "empty",
            "text_full": sanitized_text or "empty",
        }
        
        try:
            filename = self.config["file_template"].format(**template_vars)
        except KeyError as e:
            self.logger.warning(f"Invalid template variable: {e}. Using default.")
            filename = f"clip_{template_vars['datetime']}.txt"
        
        return filename
    
    def show_filename_dialog(self, suggested_name: str = "") -> Optional[str]:
        """Show a popup dialog for custom filename input"""
        try:
            # Use zenity to show a dialog for filename input
            cmd = [
                'zenity', '--entry',
                '--title=Save Clipboard As',
                '--text=Enter filename:',
                '--entry-text', suggested_name,
                '--width=400'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                filename = result.stdout.strip()
                if filename:
                    # Ensure .txt extension
                    if not filename.lower().endswith('.txt'):
                        filename += '.txt'
                    return filename
            return None
            
        except Exception as e:
            self.logger.error(f"Error showing filename dialog: {e}")
            return None
    
    def save_clipboard(self, custom_filename: Optional[str] = None, use_dialog: bool = False) -> bool:
        """Save current clipboard content to file"""
        try:
            text = pyperclip.paste()
            self.logger.info(f"Clipboard content length: {len(text)} characters")
            
            if not text or not text.strip():
                self.logger.info("Clipboard is empty or contains only whitespace")
                if self.config["notifications"]:
                    os.system('notify-send "Clipboard Saver" "Clipboard is empty" -t 3000')
                return False
            
            # Show dialog if requested
            if use_dialog:
                suggested_name = self.create_filename(text)
                custom_filename = self.show_filename_dialog(suggested_name)
                if custom_filename is None:
                    self.logger.info("User cancelled filename dialog")
                    return False  # User cancelled the dialog
            
            if custom_filename:
                filename = custom_filename
                # Ensure .txt extension for custom filenames
                if not filename.lower().endswith('.txt'):
                    filename += '.txt'
            else:
                filename = self.create_filename(text)
            
            file_path = self.save_dir / filename
            
            # Avoid overwriting existing files
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = original_path.parent / f"{stem}_{counter:02d}{suffix}"
                counter += 1
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.info(f"Clipboard saved to: {file_path}")
            
            if self.config["notifications"]:
                # Truncate filename for notification if too long
                display_name = file_path.name
                if len(display_name) > 40:
                    display_name = display_name[:37] + "..."
                
                save_type = "Custom" if custom_filename or use_dialog else "Quick"
                os.system(f'notify-send "Clipboard Saved ({save_type})" "{display_name}" -t 3000')
            
            return True
            
        except pyperclip.PyperclipException as e:
            self.logger.error(f"Clipboard access error: {e}")
            if self.config["notifications"]:
                os.system('notify-send "Clipboard Error" "Cannot access clipboard" -t 5000')
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.config["notifications"]:
                os.system(f'notify-send "Error" "Failed to save clipboard: {str(e)[:50]}..." -t 5000')
            return False
    
    def list_saves(self, count: int = 10) -> None:
        """List recent saved files"""
        files = sorted(self.save_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)
        
        if not files:
            print("No saved clipboard files found.")
            return
        
        print(f"\nRecent clipboard saves (newest first):")
        print("-" * 80)
        for i, file_path in enumerate(files[:count]):
            size = file_path.stat().st_size
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"{i+1:2d}. {mtime.strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"{size:6d} bytes | {file_path.name}")
    
    def show_info(self) -> None:
        """Show configuration information"""
        print("\nClipboard Saver - Configuration Info")
        print("=" * 50)
        print(f"Save directory: {self.save_dir}")
        print(f"File template: {self.config['file_template']}")
        print(f"Log level: {self.config['log_level']}")
        print(f"Notifications: {self.config['notifications']}")
        
        # Count saved files
        txt_files = list(self.save_dir.glob("*.txt"))
        print(f"Total saved files: {len(txt_files)}")
        
        # Show hotkey configuration
        hotkeys = self.config.get("hotkeys", {})
        print(f"Quick save hotkey: {hotkeys.get('quick_save', 'Ctrl+Alt+s')}")
        print(f"Custom save hotkey: {hotkeys.get('custom_save', 'Ctrl+Alt+f')}")
        
        # Show example filename
        example_vars = {
            "date": "2024-01-15",
            "time": "14-30-05", 
            "datetime": "20240115_143005",
            "timestamp": "1705332605",
            "text": "example_text",
            "text_full": "example_text",
        }
        example_name = self.config["file_template"].format(**example_vars)
        print(f"Example filename: {example_name}")

def create_default_config() -> None:
    """Create default configuration file"""
    config_dir = Path.home() / ".config" / "clipboard-saver"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = config_dir / "config.json"
    
    default_config = {
        "save_dir": "~/Documents/clipboard_saves",
        "file_template": "clip_{date}_{time}_{text:.20}.txt",
        "max_filename_length": 50,
        "notifications": True,
        "log_level": "INFO",
        "hotkeys": {
            "quick_save": "Ctrl+Alt+s",
            "custom_save": "Ctrl+Alt+f"
        },
        "_comment": "Available template variables: {date}, {time}, {datetime}, {timestamp}, {text}, {text_full}"
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"Default configuration created: {config_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clipboard Saver - Save clipboard content to files with GNOME hotkeys",
        epilog="Configure hotkey in GNOME Settings → Keyboard → Custom Shortcuts"
    )
    
    parser.add_argument(
        "--config", 
        type=Path,
        help="Path to custom config file"
    )
    
    parser.add_argument(
        "--list", "-l",
        type=int,
        nargs='?',
        const=10,
        metavar="COUNT",
        help="List recent saves (optional: number of files to show)"
    )
    
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show configuration information"
    )
    
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create default configuration file"
    )
    
    parser.add_argument(
        "--custom", "-c",
        action="store_true",
        help="Open dialog to enter custom filename"
    )
    
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick save using template (default behavior)"
    )
    
    parser.add_argument(
        "--filename", "-f",
        type=str,
        help="Save with specific filename"
    )
    
    args = parser.parse_args()
    
    if args.init_config:
        create_default_config()
        return
    
    try:
        saver = ClipboardSaver(args.config)
        
        if args.list is not None:
            saver.list_saves(args.list)
        elif args.info:
            saver.show_info()
        else:
            if args.filename:
                # Save with specific filename
                success = saver.save_clipboard(custom_filename=args.filename)
            elif args.custom:
                # Save with custom filename dialog
                success = saver.save_clipboard(use_dialog=True)
            else:
                # Quick save (default)
                success = saver.save_clipboard()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()