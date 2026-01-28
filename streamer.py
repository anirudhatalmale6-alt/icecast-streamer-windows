import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
import json

# Get the directory where the exe/script is located
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")

# Default configuration
DEFAULT_CONFIG = {
    "icecast_host": "172.236.22.5",
    "icecast_port": "8000",
    "icecast_mount": "stream",
    "icecast_user": "source",
    "icecast_pass": "sourcepass123",
    "audio_device": "",
    "bitrate": "128k"
}

process = None
is_streaming = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_audio_devices():
    """Get list of audio input devices using ffmpeg"""
    devices = []
    try:
        # Run ffmpeg to list devices
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.run(
            [FFMPEG_PATH, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            startupinfo=startupinfo if sys.platform == 'win32' else None,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stderr

        # Debug: save output to file for troubleshooting
        try:
            with open(os.path.join(BASE_DIR, "devices_debug.txt"), 'w', encoding='utf-8') as f:
                f.write(output)
        except:
            pass

        in_audio_section = False
        for line in output.split('\n'):
            # Check for audio devices section (various ffmpeg versions)
            if 'audio devices' in line.lower() or 'DirectShow audio' in line:
                in_audio_section = True
                continue

            # Stop at video devices section
            if in_audio_section and ('video devices' in line.lower() or 'DirectShow video' in line):
                break

            if in_audio_section:
                # Look for device names in quotes - handle various formats
                # Format 1: [dshow @ ...] "Device Name"
                # Format 2: [dshow @ ...]  "Device Name" (audio)
                if '"' in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    if start > 0 and end > start:
                        device_name = line[start:end]
                        # Skip alternative names (start with @) and empty names
                        if device_name and not device_name.startswith('@') and len(device_name) > 1:
                            devices.append(device_name)

    except Exception as e:
        # Save error for debugging
        try:
            with open(os.path.join(BASE_DIR, "error_debug.txt"), 'w', encoding='utf-8') as f:
                f.write(f"Error: {str(e)}\nFFmpeg path: {FFMPEG_PATH}\nExists: {os.path.exists(FFMPEG_PATH)}")
        except:
            pass

    return devices

class IcecastStreamer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("משדר אודיו ל-Icecast")
        self.root.geometry("450x500")
        self.root.resizable(False, False)

        # RTL support
        self.root.tk.call('tk', 'scaling', 1.2)

        self.config = load_config()
        self.process = None
        self.is_streaming = False

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="🎙️ משדר Icecast", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))

        # Audio device section
        device_frame = ttk.LabelFrame(main_frame, text="התקן אודיו", padding="10")
        device_frame.pack(fill=tk.X, pady=(0, 10))

        self.device_var = tk.StringVar(value=self.config.get('audio_device', ''))
        # Changed to normal state so user can type device name manually
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, width=40)
        self.device_combo.pack(side=tk.LEFT, padx=(0, 5))

        refresh_btn = ttk.Button(device_frame, text="🔄", width=3, command=self.refresh_devices)
        refresh_btn.pack(side=tk.LEFT)

        # Manual entry hint
        device_hint = ttk.Label(main_frame, text="(אם הרשימה ריקה - הקלד ידנית את שם ההתקן)", foreground='gray', font=('Arial', 8))
        device_hint.pack(anchor='e')

        # Server settings
        server_frame = ttk.LabelFrame(main_frame, text="הגדרות שרת", padding="10")
        server_frame.pack(fill=tk.X, pady=(0, 10))

        # Host
        host_row = ttk.Frame(server_frame)
        host_row.pack(fill=tk.X, pady=2)
        ttk.Label(host_row, text="כתובת שרת:", width=12, anchor='e').pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value=self.config.get('icecast_host', ''))
        ttk.Entry(host_row, textvariable=self.host_var, width=30).pack(side=tk.LEFT, padx=5)

        # Port
        port_row = ttk.Frame(server_frame)
        port_row.pack(fill=tk.X, pady=2)
        ttk.Label(port_row, text="פורט:", width=12, anchor='e').pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=self.config.get('icecast_port', ''))
        ttk.Entry(port_row, textvariable=self.port_var, width=10).pack(side=tk.LEFT, padx=5)

        # Mount
        mount_row = ttk.Frame(server_frame)
        mount_row.pack(fill=tk.X, pady=2)
        ttk.Label(mount_row, text="Mount:", width=12, anchor='e').pack(side=tk.LEFT)
        self.mount_var = tk.StringVar(value=self.config.get('icecast_mount', ''))
        ttk.Entry(mount_row, textvariable=self.mount_var, width=20).pack(side=tk.LEFT, padx=5)

        # Username
        user_row = ttk.Frame(server_frame)
        user_row.pack(fill=tk.X, pady=2)
        ttk.Label(user_row, text="שם משתמש:", width=12, anchor='e').pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value=self.config.get('icecast_user', ''))
        ttk.Entry(user_row, textvariable=self.user_var, width=20).pack(side=tk.LEFT, padx=5)

        # Password
        pass_row = ttk.Frame(server_frame)
        pass_row.pack(fill=tk.X, pady=2)
        ttk.Label(pass_row, text="סיסמה:", width=12, anchor='e').pack(side=tk.LEFT)
        self.pass_var = tk.StringVar(value=self.config.get('icecast_pass', ''))
        ttk.Entry(pass_row, textvariable=self.pass_var, width=20, show='*').pack(side=tk.LEFT, padx=5)

        # Bitrate
        bitrate_row = ttk.Frame(server_frame)
        bitrate_row.pack(fill=tk.X, pady=2)
        ttk.Label(bitrate_row, text="איכות:", width=12, anchor='e').pack(side=tk.LEFT)
        self.bitrate_var = tk.StringVar(value=self.config.get('bitrate', '128k'))
        bitrate_combo = ttk.Combobox(bitrate_row, textvariable=self.bitrate_var, width=10,
                                      values=['64k', '96k', '128k', '192k', '256k', '320k'], state='readonly')
        bitrate_combo.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar(value="לא פעיל")
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        ttk.Label(status_frame, text="סטטוס:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground='gray')
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)

        self.start_btn = ttk.Button(btn_frame, text="▶️ התחל שידור", command=self.start_stream, width=18)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True)

        self.stop_btn = ttk.Button(btn_frame, text="⏹️ עצור שידור", command=self.stop_stream, width=18, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True)

        # Save button
        save_btn = ttk.Button(main_frame, text="💾 שמור הגדרות", command=self.save_settings)
        save_btn.pack(pady=5)

        # Instructions
        info_text = "הוראות:\n1. בחר התקן אודיו (מיקרופון)\n2. הזן פרטי שרת Icecast\n3. לחץ 'התחל שידור'"
        info_label = ttk.Label(main_frame, text=info_text, foreground='gray', justify='right')
        info_label.pack(pady=10)

    def refresh_devices(self):
        if not os.path.exists(FFMPEG_PATH):
            messagebox.showerror("שגיאה", f"לא נמצא ffmpeg.exe\nיש להוריד ולהעתיק ל:\n{BASE_DIR}")
            return

        devices = get_audio_devices()
        self.device_combo['values'] = devices

        if devices:
            # Try to select previously saved device
            saved_device = self.config.get('audio_device', '')
            if saved_device in devices:
                self.device_var.set(saved_device)
            else:
                self.device_var.set(devices[0])
        else:
            messagebox.showwarning("אזהרה", "לא נמצאו התקני אודיו")

    def save_settings(self):
        self.config = {
            "icecast_host": self.host_var.get(),
            "icecast_port": self.port_var.get(),
            "icecast_mount": self.mount_var.get(),
            "icecast_user": self.user_var.get(),
            "icecast_pass": self.pass_var.get(),
            "audio_device": self.device_var.get(),
            "bitrate": self.bitrate_var.get()
        }
        save_config(self.config)
        messagebox.showinfo("נשמר", "ההגדרות נשמרו בהצלחה")

    def start_stream(self):
        if self.is_streaming:
            messagebox.showinfo("מידע", "השידור כבר פעיל")
            return

        device = self.device_var.get()
        if not device:
            messagebox.showerror("שגיאה", "יש לבחור התקן אודיו")
            return

        host = self.host_var.get()
        port = self.port_var.get()
        mount = self.mount_var.get()
        user = self.user_var.get()
        password = self.pass_var.get()
        bitrate = self.bitrate_var.get()

        if not all([host, port, mount, user, password]):
            messagebox.showerror("שגיאה", "יש למלא את כל פרטי השרת")
            return

        icecast_url = f"icecast://{user}:{password}@{host}:{port}/{mount}"

        ffmpeg_command = [
            FFMPEG_PATH,
            "-f", "dshow",
            "-i", f"audio={device}",
            "-ac", "1",
            "-ar", "44100",
            "-c:a", "libmp3lame",
            "-b:a", bitrate,
            "-f", "mp3",
            "-content_type", "audio/mpeg",
            icecast_url
        ]

        try:
            # Start ffmpeg in background
            self.process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            self.is_streaming = True
            self.status_var.set("🔴 משדר...")
            self.status_label.config(foreground='red')
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')

            # Monitor process in background
            threading.Thread(target=self.monitor_process, daemon=True).start()

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בהפעלת FFmpeg:\n{str(e)}")

    def monitor_process(self):
        """Monitor ffmpeg process and update status if it stops"""
        if self.process:
            self.process.wait()
            if self.is_streaming:
                self.root.after(0, self.on_stream_stopped)

    def on_stream_stopped(self):
        """Called when stream stops unexpectedly"""
        self.is_streaming = False
        self.status_var.set("⚠️ השידור נעצר")
        self.status_label.config(foreground='orange')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def stop_stream(self):
        if self.process:
            self.process.terminate()
            self.process = None

        self.is_streaming = False
        self.status_var.set("לא פעיל")
        self.status_label.config(foreground='gray')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        messagebox.showinfo("שידור", "השידור הופסק")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = IcecastStreamer()
    app.run()
