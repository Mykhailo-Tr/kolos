import os
import sys
import subprocess
import threading
import webbrowser
import signal
import socket
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime

# ============================================================
# ГЛОБАЛЬНА КОНФІГУРАЦІЯ
# ============================================================
APP_NAME = "Kolos System Management"
APP_VERSION = "1.3.0"
APP_ICON = "kolos.ico"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
AUTO_OPEN_BROWSER = True

VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"
MANAGE_FILE = "manage.py"
MIN_PYTHON_VERSION = (3, 8)

PYTHON_EXEC_WIN = r"venv\Scripts\python.exe"
PYTHON_EXEC_UNIX = "venv/bin/python"

THEME = {
    "bg": "#f0f2f5",
    "sidebar": "#1a1c23",
    "sidebar_border": "#2b2f3a",
    "primary": "#0061ff",
    "success": "#28a745",
    "danger": "#e81123",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "text_dark": "#323338",
    "text_light": "#ffffff",
    "console_bg": "#0c0c0c",
    "console_default": "#cccccc",
    "progress_bg": "#2b2f3a"
}

# ============================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# ============================================================
# ГОЛОВНИЙ КЛАС ДОДАТКУ
# ============================================================
class KolosLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=THEME["bg"])

        try:
            self.root.iconbitmap(APP_ICON)
        except: pass

        self.server_process = None
        self.start_time = None
        self.is_running = False
        self.first_web_open = True

        self.setup_ui()
        self.update_clock()
        self.check_dependencies()
        self.log("INFO: Система готова до роботи.")

    # ========================================================
    # UI СТРУКТУРА
    # ========================================================
    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=THEME["sidebar"], width=280, highlightthickness=1, highlightbackground=THEME["sidebar_border"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="KOLOS", font=("Segoe UI", 28, "bold"), fg=THEME["primary"], bg=THEME["sidebar"]).pack(pady=(40, 5))
        tk.Label(self.sidebar, text="SYSTEM CONTROL", font=("Segoe UI", 9, "bold"), fg="#5c6370", bg=THEME["sidebar"]).pack()

        # Indicators
        self.status_indicators = {}
        checks = [("python", "Python Core"), ("venv", "Virtual Env"), ("manage", "Django Files"), ("deps", "Dependencies")]
        for key, label in checks:
            f = tk.Frame(self.sidebar, bg=THEME["sidebar"], padx=25, pady=8)
            f.pack(fill="x")
            ind = tk.Label(f, text="○", fg="#5c6370", bg=THEME["sidebar"], font=("Segoe UI", 14, "bold"))
            ind.pack(side="left")
            tk.Label(f, text=label, fg="#a0a0a0", bg=THEME["sidebar"], font=("Segoe UI", 10)).pack(side="left", padx=12)
            self.status_indicators[key] = ind

        # System Tools Section
        tk.Label(self.sidebar, text="ДІАГНОСТИКА", font=("Segoe UI", 8, "bold"), fg="#5c6370", bg=THEME["sidebar"]).pack(pady=(30, 10))
        self.create_sidebar_button("ПЕРЕВІРИТИ СИСТЕМУ", self.check_dependencies).pack(fill="x", padx=20, pady=5)
        self.btn_restart = self.create_sidebar_button("ПЕРЕЗАПУСТИТИ", self.restart_server, state="disabled")
        self.btn_restart.pack(fill="x", padx=20, pady=5)

        # Uptime
        self.uptime_frame = tk.Frame(self.sidebar, bg="#252833", pady=15)
        self.uptime_frame.pack(side="bottom", fill="x", padx=20, pady=30)
        self.lbl_uptime = tk.Label(self.uptime_frame, text="UPTIME: 00:00:00", font=("Consolas", 11, "bold"), fg=THEME["warning"], bg="#252833")
        self.lbl_uptime.pack()

        # Main Area
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Header & Clock
        header = tk.Frame(main, bg=THEME["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Статус терміналу", font=("Segoe UI", 16, "bold"), fg=THEME["text_dark"], bg=THEME["bg"]).pack(side="left")
        self.lbl_clock = tk.Label(header, text="", font=("Segoe UI", 11), fg="#6c757d", bg=THEME["bg"])
        self.lbl_clock.pack(side="right")

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=(0, 15))

        # Console
        self.console = scrolledtext.ScrolledText(main, bg=THEME["console_bg"], fg=THEME["console_default"], font=("Consolas", 10), borderwidth=0, padx=15, pady=15)
        self.console.pack(fill="both", expand=True)
        self.setup_console_tags()

        # Action Buttons
        btns = tk.Frame(main, bg=THEME["bg"])
        btns.pack(fill="x", pady=(25, 0))

        self.btn_toggle = self.create_main_button(btns, "▶ ЗАПУСТИТИ СЕРВЕР", THEME["success"], self.toggle_server)
        self.btn_web = self.create_main_button(btns, "🌐 БРАУЗЕР", THEME["primary"], self.open_browser)
        self.btn_kill = self.create_main_button(btns, "✕ ВИЙТИ", THEME["danger"], self.shutdown_everything)

        for i, b in enumerate((self.btn_toggle, self.btn_web, self.btn_kill)):
            b.grid(row=0, column=i, padx=5, sticky="nsew")
            btns.columnconfigure(i, weight=1)

    # ========================================================
    # ВІЗУАЛЬНІ ЕЛЕМЕНТИ
    # ========================================================
    def create_sidebar_button(self, text, command, state="normal"):
        return tk.Button(self.sidebar, text=text, bg="#2b2f3a", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", command=command, state=state, pady=8)

    def create_main_button(self, parent, text, color, command):
        btn = tk.Button(parent, text=text, bg=color, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=command, pady=12)
        btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def lighten_color(self, hex_color, factor=1.15):
        hex_color = hex_color.lstrip("#")
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        return f"#{min(255, int(rgb[0]*factor)):02x}{min(255, int(rgb[1]*factor)):02x}{min(255, int(rgb[2]*factor)):02x}"

    def setup_console_tags(self):
        self.console.tag_config("timestamp", foreground="#5c6370")
        self.console.tag_config("error", foreground=THEME["danger"], font=("Consolas", 10, "bold"))
        self.console.tag_config("success", foreground=THEME["success"], font=("Consolas", 10, "bold"))
        self.console.tag_config("warning", foreground=THEME["warning"])
        self.console.tag_config("info", foreground=THEME["primary"])

    # ========================================================
    # ЛОГІКА ТА СИСТЕМНІ ФУНКЦІЇ
    # ========================================================
    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] ", "timestamp")
        tag = None
        msg = message.upper()
        if "ERROR" in msg: tag = "error"
        elif "SUCCESS" in msg: tag = "success"
        elif "WARNING" in msg: tag = "warning"
        elif "INFO" in msg or "START" in msg: tag = "info"
        self.console.insert("end", message + "\n", tag)
        self.console.see("end")

    def update_clock(self):
        self.lbl_clock.config(text=datetime.now().strftime("%A, %d %B %Y | %H:%M:%S"))
        if self.is_running and self.start_time:
            delta = datetime.now() - self.start_time
            self.lbl_uptime.config(text=f"UPTIME: {str(delta).split('.')[0]}")
        self.root.after(1000, self.update_clock)

    def check_dependencies(self):
        self.log("INFO: Запуск діагностики системи...")
        p_ok = sys.version_info >= MIN_PYTHON_VERSION
        m_ok = os.path.exists(MANAGE_FILE)
        python_exe = PYTHON_EXEC_WIN if os.name == "nt" else PYTHON_EXEC_UNIX
        v_ok = os.path.exists(python_exe)
        d_ok = os.path.exists(REQUIREMENTS_FILE)

        self.set_status("python", p_ok)
        self.set_status("manage", m_ok)
        self.set_status("venv", v_ok)
        self.set_status("deps", d_ok)
        
        if all([p_ok, m_ok, v_ok, d_ok]):
            self.log("SUCCESS: Всі залежності в нормі.")
        else:
            self.log("WARNING: Знайдено проблеми в конфігурації.")

    def set_status(self, key, ok):
        self.status_indicators[key].config(text="✔" if ok else "✖", fg=THEME["success"] if ok else THEME["danger"])

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            if is_port_in_use(SERVER_PORT):
                self.log(f"ERROR: Порт {SERVER_PORT} вже зайнятий! Закрийте інші сервери.")
                return
            self.start_server_thread()

    def restart_server(self):
        self.log("INFO: Перезапуск сервера...")
        self.stop_server()
        self.root.after(1000, self.start_server_thread)

    def start_server_thread(self):
        self.btn_toggle.config(text="■ ЗУПИНИТИ СЕРВЕР", bg=THEME["warning"])
        self.btn_restart.config(state="normal")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            self.progress_var.set(5)
            python_exe = PYTHON_EXEC_WIN if os.name == "nt" else PYTHON_EXEC_UNIX

            if not os.path.exists(VENV_DIR):
                self.log("INFO: Створення Virtual Env...")
                subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
                self.set_status("venv", True)
            self.progress_var.set(25)

            self.log("INFO: Оновлення пакетів (pip)...")
            subprocess.run([python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], capture_output=True)
            self.set_status("deps", True)
            self.progress_var.set(50)

            self.log("INFO: Міграції бази даних...")
            subprocess.run([python_exe, MANAGE_FILE, "migrate", "--noinput"], capture_output=True)
            self.progress_var.set(75)

            self.log("INFO: Збір статики...")
            subprocess.run([python_exe, MANAGE_FILE, "collectstatic", "--noinput"], capture_output=True)
            self.progress_var.set(90)

            self.server_process = subprocess.Popen(
                [python_exe, MANAGE_FILE, "runserver", f"{SERVER_HOST}:{SERVER_PORT}", "--noreload"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )

            self.is_running = True
            self.start_time = datetime.now()
            self.progress_var.set(100)
            self.log(f"SUCCESS: Kolos запущено на http://{SERVER_HOST}:{SERVER_PORT}")

            if AUTO_OPEN_BROWSER and self.first_web_open:
                self.first_web_open = False
                self.root.after(1000, self.open_browser)

            for line in self.server_process.stdout:
                if line.strip(): self.log(line.strip())

        except Exception as e:
            self.log(f"ERROR: Критичний збій: {e}")
            self.stop_server()

    def stop_server(self):
        if self.server_process:
            self.log("WARNING: Примусова зупинка процесів...")
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.server_process.pid)], capture_output=True)
            else:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process = None

        self.is_running = False
        self.start_time = None
        self.progress_var.set(0)
        self.btn_toggle.config(text="▶ ЗАПУСТИТИ СЕРВЕР", bg=THEME["success"])
        self.btn_restart.config(state="disabled")
        self.lbl_uptime.config(text="UPTIME: 00:00:00")
        self.log("SUCCESS: Сервер вимкнено.")

    def open_browser(self):
        webbrowser.open(f"http://{SERVER_HOST}:{SERVER_PORT}")
        self.log("INFO: Запит до браузера надіслано.")

    def shutdown_everything(self):
        if self.is_running: self.stop_server()
        self.log("INFO: Вихід...")
        self.root.after(300, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    # Налаштування стилю для Progress Bar (темна тема)
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=10, background=THEME["primary"], troughcolor=THEME["progress_bg"], borderwidth=0)
    
    app = KolosLauncher(root)
    root.mainloop()