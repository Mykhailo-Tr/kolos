import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
import re
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

# --- КОНФІГУРАЦІЯ СТИЛЮ ---
THEME = {
    "bg": "#f0f2f5",
    "sidebar": "#1a1c23",
    "card": "#ffffff",
    "primary": "#0061ff",
    "success": "#28a745",
    "danger": "#e81123",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "text_dark": "#323338",
    "text_light": "#ffffff",
    "console_bg": "#0c0c0c",
    "console_default": "#cccccc"
}

class KolosLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Kolos System Management")
        self.root.geometry("1000x700")
        self.root.configure(bg=THEME["bg"])
        
        self.server_process = None
        self.start_time = None
        self.is_running = False
        
        self.setup_ui()
        self.update_clock()
        self.check_dependencies()
        self.log("INFO: Система готова до роботи.")

    def setup_ui(self):
        # --- Sidebar (Ліва панель) ---
        self.sidebar = tk.Frame(self.root, bg=THEME["sidebar"], width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="KOLOS", font=("Segoe UI", 28, "bold"), 
                 foreground=THEME["primary"], bg=THEME["sidebar"]).pack(pady=(40, 5))
        tk.Label(self.sidebar, text="CONTROL DASHBOARD", font=("Segoe UI", 9, "bold"), 
                 foreground="#5c6370", bg=THEME["sidebar"]).pack(pady=(0, 40))

        # Статуси перевірок
        self.status_indicators = {}
        checks = [
            ("python", "Python 3.12 [cite: 1]"),
            ("venv", "Virtual Env [cite: 9]"),
            ("manage", "Django Core [cite: 2]"),
            ("deps", "Requirements [cite: 4]")
        ]

        for key, label in checks:
            f = tk.Frame(self.sidebar, bg=THEME["sidebar"], padx=25, pady=8)
            f.pack(fill="x")
            ind = tk.Label(f, text="○", foreground="#5c6370", bg=THEME["sidebar"], font=("Segoe UI", 12, "bold"))
            ind.pack(side="left")
            tk.Label(f, text=label, foreground="#a0a0a0", bg=THEME["sidebar"], font=("Segoe UI", 10)).pack(side="left", padx=12)
            self.status_indicators[key] = ind

        # Таймер (Uptime)
        self.uptime_frame = tk.Frame(self.sidebar, bg="#252833", pady=15)
        self.uptime_frame.pack(side="bottom", fill="x", padx=20, pady=30)
        self.lbl_uptime = tk.Label(self.uptime_frame, text="UPTIME: 00:00:00", font=("Consolas", 12, "bold"), 
                                  foreground=THEME["warning"], bg="#252833")
        self.lbl_uptime.pack()

        # --- Main Area ---
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Header
        header = tk.Frame(main, bg=THEME["bg"])
        header.pack(fill="x", pady=(0, 20))
        tk.Label(header, text="Моніторинг активності", font=("Segoe UI", 16, "bold"), 
                 foreground=THEME["text_dark"], bg=THEME["bg"]).pack(side="left")
        self.lbl_clock = tk.Label(header, text="", font=("Segoe UI", 11), foreground="#6c757d", bg=THEME["bg"])
        self.lbl_clock.pack(side="right")

        # Консоль з кольорами
        self.console = scrolledtext.ScrolledText(main, bg=THEME["console_bg"], foreground=THEME["console_default"],
                                                font=("Consolas", 10), borderwidth=0, padx=15, pady=15)
        self.console.pack(fill="both", expand=True)
        self.setup_console_tags()

        # Панель кнопок
        btn_grid = tk.Frame(main, bg=THEME["bg"])
        btn_grid.pack(fill="x", pady=(25, 0))

        # Стильні кнопки
        self.btn_start = self.create_button(btn_grid, "▶ ЗАПУСТИТИ", THEME["success"], self.start_server_thread)
        self.btn_stop = self.create_button(btn_grid, "■ ЗУПИНИТИ", THEME["warning"], self.stop_server, state="disabled")
        self.btn_web = self.create_button(btn_grid, "🌐 БРАУЗЕР", THEME["primary"], self.open_browser)
        self.btn_kill = self.create_button(btn_grid, "✕ ВИМКНУТИ ВСЕ", THEME["danger"], self.shutdown_everything)

        # Розміщення кнопок
        self.btn_start.grid(row=0, column=0, padx=5, sticky="nsew")
        self.btn_stop.grid(row=0, column=1, padx=5, sticky="nsew")
        self.btn_web.grid(row=0, column=2, padx=5, sticky="nsew")
        self.btn_kill.grid(row=0, column=3, padx=5, sticky="nsew")
        btn_grid.columnconfigure((0,1,2,3), weight=1)

    def create_button(self, parent, text, color, command, state="normal"):
        btn = tk.Button(parent, text=text, bg=color, foreground="white", font=("Segoe UI", 10, "bold"),
                       relief="flat", activebackground=color, cursor="hand2", 
                       command=command, state=state, pady=12)
        btn.bind("<Enter>", lambda e: btn.config(background=self.lighten_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(background=color))
        return btn

    def lighten_color(self, hex_color):
        """Робить колір світлішим для ефекту наведення."""
        return hex_color # Можна додати складнішу логіку для RGB

    def setup_console_tags(self):
        self.console.tag_config("timestamp", foreground="#5c6370")
        self.console.tag_config("error", foreground=THEME["danger"], font=("Consolas", 10, "bold"))
        self.console.tag_config("success", foreground=THEME["success"], font=("Consolas", 10, "bold"))
        self.console.tag_config("warning", foreground=THEME["warning"])
        self.console.tag_config("info", foreground=THEME["primary"])

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Парсинг повідомлення для кольорів
        msg_lower = message.upper()
        tag = None
        if "ERROR" in msg_lower or "FAIL" in msg_lower: tag = "error"
        elif "SUCCESS" in msg_lower or "OK" in msg_lower or "DONE" in msg_lower: tag = "success"
        elif "WARNING" in msg_lower: tag = "warning"
        elif "INFO" in msg_lower or "STARTING" in msg_lower: tag = "info"

        self.console.insert(tk.END, message + "\n", tag)
        self.console.see(tk.END)

    def update_clock(self):
        self.lbl_clock.config(text=datetime.now().strftime("%A, %d %B %Y | %H:%M:%S"))
        if self.is_running and self.start_time:
            delta = datetime.now() - self.start_time
            self.lbl_uptime.config(text=f"UPTIME: {str(delta).split('.')[0]}")
        self.root.after(1000, self.update_clock)

    def check_dependencies(self):
        # Python check [cite: 1]
        self.set_status("python", sys.version_info >= (3, 8))
        # manage.py check [cite: 2]
        self.set_status("manage", os.path.exists("manage.py"))
        # venv check [cite: 9]
        venv_exec = "venv\\Scripts\\python.exe" if os.name == 'nt' else "venv/bin/python"
        self.set_status("venv", os.path.exists(venv_exec))
        # Requirements check [cite: 4]
        self.set_status("deps", os.path.exists("requirements.txt"))

    def set_status(self, key, ok):
        color = THEME["success"] if ok else THEME["danger"]
        self.status_indicators[key].config(text="●" if ok else "✘", foreground=color)

    def start_server_thread(self):
        self.btn_start.config(state="disabled", bg="#d1d1d1")
        self.btn_stop.config(state="normal")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            python_exe = "venv\\Scripts\\python.exe" if os.name == 'nt' else "venv/bin/python"
            
            if not os.path.exists("venv"):
                self.log("INFO: Створення віртуального оточення... [cite: 9]")
                subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                self.set_status("venv", True)

            self.log("INFO: Перевірка бібліотек (pip install)... [cite: 10]")
            subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True)
            self.set_status("deps", True)

            self.log("INFO: Міграція бази даних... [cite: 8]")
            subprocess.run([python_exe, "manage.py", "migrate", "--noinput"], capture_output=True)

            self.log("SUCCESS: Запуск сервера на http://127.0.0.1:8000")
            # Використовуємо CREATE_NEW_PROCESS_GROUP для повного контролю над деревом процесів
            self.server_process = subprocess.Popen(
                [python_exe, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            self.is_running = True
            self.start_time = datetime.now()
            self.root.after(1500, self.open_browser)

            for line in self.server_process.stdout:
                if line.strip(): self.log(line.strip())

        except Exception as e:
            self.log(f"ERROR: Помилка запуску: {e}")
            self.stop_server()

    def stop_server(self):
        if self.server_process:
            self.log("WARNING: Зупинка всіх процесів сервера...")
            if os.name == 'nt':
                # Примусове завершення всього дерева процесів (Django + Python)
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)], capture_output=True)
            else:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            
            self.server_process = None
        
        self.is_running = False
        self.btn_start.config(state="normal", bg=THEME["success"])
        self.btn_stop.config(state="disabled")
        self.lbl_uptime.config(text="UPTIME: 00:00:00")
        self.log("SUCCESS: Сервер успішно зупинено.")

    def open_browser(self):
        webbrowser.open("http://127.0.0.1:8000")
        self.log("INFO: Відкрито браузер.")

    def shutdown_everything(self):
        """Закриває сервер та сам лаунчер однією командою."""
        if self.is_running:
            self.stop_server()
        self.log("INFO: Завершення роботи лаунчера...")
        self.root.after(400, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    # Якщо у вас є файл kolos.ico, розкоментуйте наступний рядок:
    # root.iconbitmap("kolos.ico")
    app = KolosLauncher(root)
    root.mainloop()