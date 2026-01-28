import os
import sys
import subprocess
import threading
import webbrowser
import signal
import socket
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from datetime import datetime
import json
import atexit

# ============================================================
# ГЛОБАЛЬНА КОНФІГУРАЦІЯ
# ============================================================
APP_NAME = "Kolos System Management"
APP_VERSION = "1.4.0"
APP_ICON = "kolos.ico"
CONFIG_FILE = "kolos_config.json"

# Налаштування за замовчуванням
DEFAULT_CONFIG = {
    "SERVER_HOST": "127.0.0.1",
    "SERVER_PORT": 8000,
    "AUTO_OPEN_BROWSER": True,
    "VENV_DIR": "venv",
    "REQUIREMENTS_FILE": "requirements.txt",
    "MANAGE_FILE": "manage.py",
    "PYTHON_EXEC_WIN": r"venv\Scripts\python.exe",
    "PYTHON_EXEC_UNIX": "venv/bin/python"
}

MIN_PYTHON_VERSION = (3, 8)

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
    "progress_bg": "#2b2f3a",
    "input_bg": "#ffffff",
    "input_fg": "#323338",
    "input_border": "#d1d9e6"
}

# ============================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def load_config():
    """Завантажити конфігурацію з файлу або використати значення за замовчуванням"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Оновлюємо тільки існуючі ключі
                for key in DEFAULT_CONFIG:
                    if key in config:
                        DEFAULT_CONFIG[key] = config[key]
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Помилка завантаження конфігурації: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Зберегти конфігурацію у файл"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Помилка збереження конфігурації: {e}")
        return False

# ============================================================
# КЛАС НАЛАШТУВАНЬ
# ============================================================
class SettingsDialog:
    def __init__(self, parent, config, on_save_callback):
        self.parent = parent
        self.config = config.copy()
        self.on_save_callback = on_save_callback
        self.changes_made = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Налаштування системи")
        self.dialog.geometry("600x550")
        self.dialog.configure(bg=THEME["bg"])
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Обробка закриття вікна
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Центрування вікна
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.setup_validation()
        
    def setup_ui(self):
        # Заголовок
        header_frame = tk.Frame(self.dialog, bg=THEME["primary"], height=60)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="⚙ НАЛАШТУВАННЯ СИСТЕМИ", 
                font=("Segoe UI", 14, "bold"), 
                fg=THEME["text_light"], 
                bg=THEME["primary"]).pack(expand=True)
        
        # Основний контент
        content_frame = tk.Frame(self.dialog, bg=THEME["bg"], padx=30, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Секція сервера
        server_frame = self.create_section(content_frame, "Налаштування сервера", 0)
        
        self.create_setting(server_frame, "Хост сервера:", 
                           "SERVER_HOST", self.config["SERVER_HOST"], 0)
        self.create_setting(server_frame, "Порт сервера:", 
                           "SERVER_PORT", str(self.config["SERVER_PORT"]), 1, "number")
        
        # Секція файлів
        files_frame = self.create_section(content_frame, "Шляхи до файлів", 1)
        
        self.create_setting(files_frame, "Віртуальне середовище:", 
                           "VENV_DIR", self.config["VENV_DIR"], 0)
        self.create_setting(files_frame, "Файл залежностей:", 
                           "REQUIREMENTS_FILE", self.config["REQUIREMENTS_FILE"], 1)
        self.create_setting(files_frame, "Файл manage.py:", 
                           "MANAGE_FILE", self.config["MANAGE_FILE"], 2)
        
        # Секція поведінки
        behavior_frame = self.create_section(content_frame, "Поведінка програми", 2)
        
        self.create_checkbox(behavior_frame, "Автоматично відкривати браузер при запуску", 
                            "AUTO_OPEN_BROWSER", self.config["AUTO_OPEN_BROWSER"], 0)
        
        # Індикатор змін
        self.changes_label = tk.Label(content_frame, text="", font=("Segoe UI", 9),
                                     bg=THEME["bg"], fg=THEME["warning"])
        self.changes_label.grid(row=3, column=0, sticky="w", pady=(10, 0))
        
        # Кнопки
        button_frame = tk.Frame(self.dialog, bg=THEME["bg"], pady=20)
        button_frame.pack(fill="x", padx=30)
        
        btn_style = {"font": ("Segoe UI", 10, "bold"), "cursor": "hand2", "pady": 10, "width": 12}
        
        tk.Button(button_frame, text="Скасувати", 
                 bg="#6c757d", fg="white", 
                 command=self.on_close, **btn_style).pack(side="right", padx=5)
        
        self.save_btn = tk.Button(button_frame, text="💾 Зберегти", 
                 bg=THEME["success"], fg="white", 
                 command=self.save_settings, **btn_style)
        self.save_btn.pack(side="right", padx=5)
        self.save_btn.config(state="disabled")  # Спочатку неактивна
        
        tk.Button(button_frame, text="За замовчуванням", 
                 bg=THEME["info"], fg="white", 
                 command=self.reset_to_default, **btn_style).pack(side="left", padx=5)
    
    def create_section(self, parent, title, row):
        frame = tk.LabelFrame(parent, text=f"  {title}  ", 
                             font=("Segoe UI", 10, "bold"),
                             bg=THEME["bg"], fg=THEME["text_dark"],
                             padx=15, pady=15)
        frame.grid(row=row, column=0, sticky="nsew", pady=(0, 15), padx=5)
        parent.grid_columnconfigure(0, weight=1)
        return frame
    
    def create_setting(self, parent, label, config_key, value, row, input_type="text"):
        tk.Label(parent, text=label, font=("Segoe UI", 9), 
                bg=THEME["bg"], fg=THEME["text_dark"]).grid(row=row, column=0, sticky="w", pady=8)
        
        if input_type == "number":
            var = tk.StringVar(value=value)
            entry = tk.Spinbox(parent, from_=1024, to=65535, textvariable=var,
                              font=("Segoe UI", 9), bg=THEME["input_bg"], fg=THEME["input_fg"],
                              relief="flat", highlightthickness=1, 
                              highlightbackground=THEME["input_border"],
                              highlightcolor=THEME["primary"])
        else:
            var = tk.StringVar(value=value)
            entry = tk.Entry(parent, textvariable=var, font=("Segoe UI", 9),
                            bg=THEME["input_bg"], fg=THEME["input_fg"],
                            relief="flat", highlightthickness=1,
                            highlightbackground=THEME["input_border"],
                            highlightcolor=THEME["primary"])
        
        entry.grid(row=row, column=1, sticky="ew", pady=8, padx=(15, 0))
        entry.bind("<FocusIn>", lambda e: e.widget.configure(highlightbackground=THEME["primary"]))
        entry.bind("<FocusOut>", lambda e: e.widget.configure(highlightbackground=THEME["input_border"]))
        
        parent.grid_columnconfigure(1, weight=1)
        
        # Зберігаємо посилання на змінну та прив'язуємо зміни
        setattr(self, f"var_{config_key}", var)
        var.trace_add("write", self.on_value_changed)
    
    def create_checkbox(self, parent, label, config_key, value, row):
        var = tk.BooleanVar(value=value)
        cb = tk.Checkbutton(parent, text=label, variable=var,
                           font=("Segoe UI", 9), bg=THEME["bg"], fg=THEME["text_dark"],
                           selectcolor=THEME["bg"], activebackground=THEME["bg"],
                           activeforeground=THEME["text_dark"])
        cb.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
        
        # Зберігаємо посилання на змінну та прив'язуємо зміни
        setattr(self, f"var_{config_key}", var)
        var.trace_add("write", self.on_value_changed)
    
    def setup_validation(self):
        """Налаштування валідації для полів"""
        # Валідація для порту
        port_var = getattr(self, "var_SERVER_PORT", None)
        if port_var:
            vcmd = (self.dialog.register(self.validate_port), '%P')
            port_widget = port_var._tk.globalgetvar(port_var._name)
            if hasattr(port_widget, 'configure'):
                port_widget.configure(validate='key', validatecommand=vcmd)
    
    def validate_port(self, value):
        """Валідація номера порту"""
        if value == "" or value.isdigit():
            return True
        return False
    
    def on_value_changed(self, *args):
        """Обробка зміни значень полів"""
        self.changes_made = True
        self.save_btn.config(state="normal", bg="#1e7e34")  # Темніший зелений
        self.changes_label.config(text="⚠ Зроблено зміни. Натисніть 'Зберегти'.")
    
    def on_close(self):
        """Обробка закриття вікна налаштувань"""
        if self.changes_made:
            response = messagebox.askyesnocancel(
                "Зберегти зміни?",
                "Ви зробили зміни в налаштуваннях.\n\nЗберегти зміни перед закриттям?",
                icon=messagebox.QUESTION
            )
            
            if response is None:  # Скасувати
                return
            elif response:  # Так, зберегти
                if not self.save_settings():
                    return  # Не закривати, якщо не вдалося зберегти
            # Ні - просто закрити без збереження
        
        self.dialog.destroy()
    
    def save_settings(self):
        """Зберегти змінені налаштування"""
        try:
            # Оновлюємо конфігурацію зі значень полів
            for key in self.config:
                var = getattr(self, f"var_{key}", None)
                if var:
                    if isinstance(var, tk.BooleanVar):
                        self.config[key] = var.get()
                    else:
                        value = var.get().strip()
                        if key == "SERVER_PORT":
                            if not value.isdigit():
                                messagebox.showerror("Помилка", "Порт повинен бути числом")
                                return False
                            port = int(value)
                            if not (1024 <= port <= 65535):
                                messagebox.showerror("Помилка", "Порт повинен бути в діапазоні 1024-65535")
                                return False
                            self.config[key] = port
                        else:
                            self.config[key] = value
            
            # Збереження у файл
            if save_config(self.config):
                # Скидаємо індикатор змін
                self.changes_made = False
                self.save_btn.config(state="disabled", bg=THEME["success"])
                self.changes_label.config(text="✓ Налаштування збережено!", fg=THEME["success"])
                
                # Викликаємо callback для оновлення головного вікна
                self.on_save_callback(self.config)
                
                # Автоматично закриваємо через 2 секунди
                self.dialog.after(2000, self.dialog.destroy)
                return True
            else:
                messagebox.showerror("Помилка", "Не вдалося зберегти налаштування")
                return False
                
        except ValueError as e:
            messagebox.showerror("Помилка", f"Невірне значення: {str(e)}")
            return False
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка збереження: {str(e)}")
            return False
    
    def reset_to_default(self):
        """Скинути налаштування до значень за замовчуванням"""
        if messagebox.askyesno("Скинути налаштування", 
                              "Ви впевнені, що хочете скинути всі налаштування до значень за замовчуванням?"):
            # Оновлюємо змінні значеннями за замовчуванням
            for key in DEFAULT_CONFIG:
                var = getattr(self, f"var_{key}", None)
                if var:
                    if isinstance(var, tk.BooleanVar):
                        var.set(DEFAULT_CONFIG[key])
                    else:
                        var.set(str(DEFAULT_CONFIG[key]))
            
            self.config = DEFAULT_CONFIG.copy()
            self.on_value_changed()  # Відмічаємо зміни

# ============================================================
# ГОЛОВНИЙ КЛАС ДОДАТКУ
# ============================================================
class KolosLauncher:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=THEME["bg"])

        try:
            self.root.iconbitmap(APP_ICON)
        except: 
            pass

        self.server_process = None
        self.start_time = None
        self.is_running = False
        self.first_web_open = True

        # Реєстрація обробника закриття
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.update_clock()
        self.check_dependencies()
        self.log("INFO: Система готова до роботи.")

    # ========================================================
    # UI СТРУКТУРА
    # ========================================================
    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=THEME["sidebar"], width=280, 
                               highlightthickness=1, highlightbackground=THEME["sidebar_border"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="KOLOS", font=("Segoe UI", 28, "bold"), 
                fg=THEME["primary"], bg=THEME["sidebar"]).pack(pady=(40, 5))
        tk.Label(self.sidebar, text="SYSTEM CONTROL", font=("Segoe UI", 9, "bold"), 
                fg="#5c6370", bg=THEME["sidebar"]).pack()

        # Indicators
        self.status_indicators = {}
        checks = [("python", "Python Core"), ("venv", "Virtual Env"), 
                 ("manage", "Django Files"), ("deps", "Dependencies")]
        for key, label in checks:
            f = tk.Frame(self.sidebar, bg=THEME["sidebar"], padx=25, pady=8)
            f.pack(fill="x")
            ind = tk.Label(f, text="○", fg="#5c6370", bg=THEME["sidebar"], 
                          font=("Segoe UI", 14, "bold"))
            ind.pack(side="left")
            tk.Label(f, text=label, fg="#a0a0a0", bg=THEME["sidebar"], 
                    font=("Segoe UI", 10)).pack(side="left", padx=12)
            self.status_indicators[key] = ind

        # System Tools Section
        tk.Label(self.sidebar, text="ДІАГНОСТИКА", font=("Segoe UI", 8, "bold"), 
                fg="#5c6370", bg=THEME["sidebar"]).pack(pady=(30, 10))
        
        self.create_sidebar_button("ПЕРЕВІРИТИ СИСТЕМУ", self.check_dependencies).pack(fill="x", padx=20, pady=5)
        self.btn_restart = self.create_sidebar_button("ПЕРЕЗАПУСТИТИ", self.restart_server, state="disabled")
        self.btn_restart.pack(fill="x", padx=20, pady=5)
        
        # Налаштування
        tk.Label(self.sidebar, text="КОНФІГУРАЦІЯ", font=("Segoe UI", 8, "bold"), 
                fg="#5c6370", bg=THEME["sidebar"]).pack(pady=(30, 10))
        self.create_sidebar_button("⚙ НАЛАШТУВАННЯ", self.open_settings).pack(fill="x", padx=20, pady=5)
        
        # Інформація про конфігурацію
        self.config_info_frame = tk.Frame(self.sidebar, bg="#252833", padx=15, pady=10)
        self.config_info_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        tk.Label(self.config_info_frame, text="АКТИВНІ НАЛАШТУВАННЯ:", 
                font=("Segoe UI", 7, "bold"), fg="#5c6370", bg="#252833").pack(anchor="w")
        self.lbl_config = tk.Label(self.config_info_frame, text="", font=("Consolas", 7), 
                                  fg="#cccccc", bg="#252833", justify="left")
        self.lbl_config.pack(anchor="w", pady=(5, 0))
        
        self.update_config_display()

        # Uptime
        self.uptime_frame = tk.Frame(self.sidebar, bg="#252833", pady=15)
        self.uptime_frame.pack(side="bottom", fill="x", padx=20, pady=30)
        self.lbl_uptime = tk.Label(self.uptime_frame, text="UPTIME: 00:00:00", 
                                  font=("Consolas", 11, "bold"), fg=THEME["warning"], bg="#252833")
        self.lbl_uptime.pack()

        # Main Area
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Header & Clock
        header = tk.Frame(main, bg=THEME["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Статус терміналу", font=("Segoe UI", 16, "bold"), 
                fg=THEME["text_dark"], bg=THEME["bg"]).pack(side="left")
        self.lbl_clock = tk.Label(header, text="", font=("Segoe UI", 11), 
                                 fg="#6c757d", bg=THEME["bg"])
        self.lbl_clock.pack(side="right")

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=(0, 15))

        # Console
        self.console = scrolledtext.ScrolledText(main, bg=THEME["console_bg"], 
                                                fg=THEME["console_default"], 
                                                font=("Consolas", 10), borderwidth=0, 
                                                padx=15, pady=15)
        self.console.pack(fill="both", expand=True)
        self.setup_console_tags()

        # Action Buttons
        btns = tk.Frame(main, bg=THEME["bg"])
        btns.pack(fill="x", pady=(25, 0))

        self.btn_toggle = self.create_main_button(btns, "▶ ЗАПУСТИТИ СЕРВЕР", 
                                                 THEME["success"], self.toggle_server)
        self.btn_web = self.create_main_button(btns, "🌐 БРАУЗЕР", 
                                              THEME["primary"], self.open_browser)
        self.btn_kill = self.create_main_button(btns, "✕ ВИЙТИ", 
                                               THEME["danger"], self.shutdown_everything)

        for i, b in enumerate((self.btn_toggle, self.btn_web, self.btn_kill)):
            b.grid(row=0, column=i, padx=5, sticky="nsew")
            btns.columnconfigure(i, weight=1)

    # ========================================================
    # ВІЗУАЛЬНІ ЕЛЕМЕНТИ
    # ========================================================
    def create_sidebar_button(self, text, command, state="normal"):
        return tk.Button(self.sidebar, text=text, bg="#2b2f3a", fg="white", 
                        font=("Segoe UI", 8, "bold"), relief="flat", 
                        cursor="hand2", command=command, state=state, pady=8)

    def create_main_button(self, parent, text, color, command):
        btn = tk.Button(parent, text=text, bg=color, fg="white", 
                       font=("Segoe UI", 10, "bold"), relief="flat", 
                       cursor="hand2", command=command, pady=12)
        btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def lighten_color(self, hex_color, factor=1.15):
        hex_color = hex_color.lstrip("#")
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        return f"#{min(255, int(rgb[0]*factor)):02x}{min(255, int(rgb[1]*factor)):02x}{min(255, int(rgb[2]*factor)):02x}"

    def setup_console_tags(self):
        self.console.tag_config("timestamp", foreground="#5c6370")
        self.console.tag_config("error", foreground=THEME["danger"], 
                               font=("Consolas", 10, "bold"))
        self.console.tag_config("success", foreground=THEME["success"], 
                               font=("Consolas", 10, "bold"))
        self.console.tag_config("warning", foreground=THEME["warning"])
        self.console.tag_config("info", foreground=THEME["primary"])

    # ========================================================
    # ФУНКЦІОНАЛ НАЛАШТУВАНЬ
    # ========================================================
    def open_settings(self):
        """Відкрити вікно налаштувань"""
        SettingsDialog(self.root, self.config, self.on_settings_saved)
    
    def on_settings_saved(self, new_config):
        """Обробка збережених налаштувань"""
        self.config = new_config
        self.update_config_display()
        self.log("INFO: Налаштування оновлено.")
        
        # Якщо сервер запущено, повідомити про необхідність перезапуску
        if self.is_running:
            self.log("WARNING: Для застосування змін перезапустіть сервер.")
    
    def update_config_display(self):
        """Оновити відображення поточних налаштувань"""
        config_text = f"Host: {self.config['SERVER_HOST']}:{self.config['SERVER_PORT']}\n"
        config_text += f"Auto browser: {'Так' if self.config['AUTO_OPEN_BROWSER'] else 'Ні'}\n"
        config_text += f"Venv: {self.config['VENV_DIR']}"
        self.lbl_config.config(text=config_text)
    
    def on_closing(self):
        """Обробка закриття головного вікна"""
        # Автоматично зберігаємо конфігурацію при закритті
        save_config(self.config)
        
        # Зупиняємо сервер, якщо він працює
        if self.is_running:
            self.stop_server()
        
        self.root.destroy()

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
        m_ok = os.path.exists(self.config["MANAGE_FILE"])
        python_exe = self.config["PYTHON_EXEC_WIN"] if os.name == "nt" else self.config["PYTHON_EXEC_UNIX"]
        v_ok = os.path.exists(python_exe)
        d_ok = os.path.exists(self.config["REQUIREMENTS_FILE"])

        self.set_status("python", p_ok)
        self.set_status("manage", m_ok)
        self.set_status("venv", v_ok)
        self.set_status("deps", d_ok)
        
        if all([p_ok, m_ok, v_ok, d_ok]):
            self.log("SUCCESS: Всі залежності в нормі.")
        else:
            self.log("WARNING: Знайдено проблеми в конфігурації.")

    def set_status(self, key, ok):
        self.status_indicators[key].config(text="✔" if ok else "✖", 
                                          fg=THEME["success"] if ok else THEME["danger"])

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            if is_port_in_use(self.config["SERVER_PORT"]):
                self.log(f"ERROR: Порт {self.config['SERVER_PORT']} вже зайнятий! Закрийте інші сервери.")
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
            python_exe = self.config["PYTHON_EXEC_WIN"] if os.name == "nt" else self.config["PYTHON_EXEC_UNIX"]

            if not os.path.exists(self.config["VENV_DIR"]):
                self.log("INFO: Створення Virtual Env...")
                subprocess.run([sys.executable, "-m", "venv", self.config["VENV_DIR"]], check=True)
                self.set_status("venv", True)
            self.progress_var.set(25)

            self.log("INFO: Оновлення пакетів (pip)...")
            subprocess.run([python_exe, "-m", "pip", "install", "-r", self.config["REQUIREMENTS_FILE"]], 
                          capture_output=True)
            self.set_status("deps", True)
            self.progress_var.set(50)

            self.log("INFO: Міграції бази даних...")
            subprocess.run([python_exe, self.config["MANAGE_FILE"], "migrate", "--noinput"], 
                          capture_output=True)
            self.progress_var.set(75)

            self.log("INFO: Збір статики...")
            subprocess.run([python_exe, self.config["MANAGE_FILE"], "collectstatic", "--noinput"], 
                          capture_output=True)
            self.progress_var.set(90)

            self.server_process = subprocess.Popen(
                [python_exe, self.config["MANAGE_FILE"], "runserver", 
                 f"{self.config['SERVER_HOST']}:{self.config['SERVER_PORT']}", "--noreload"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )

            self.is_running = True
            self.start_time = datetime.now()
            self.progress_var.set(100)
            self.log(f"SUCCESS: Kolos запущено на http://{self.config['SERVER_HOST']}:{self.config['SERVER_PORT']}")

            if self.config["AUTO_OPEN_BROWSER"] and self.first_web_open:
                self.first_web_open = False
                self.root.after(1000, self.open_browser)

            for line in self.server_process.stdout:
                if line.strip(): 
                    self.log(line.strip())

        except Exception as e:
            self.log(f"ERROR: Критичний збій: {e}")
            self.stop_server()

    def stop_server(self):
        if self.server_process:
            self.log("WARNING: Примусова зупинка процесів...")
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.server_process.pid)], 
                              capture_output=True)
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
        webbrowser.open(f"http://{self.config['SERVER_HOST']}:{self.config['SERVER_PORT']}")
        self.log("INFO: Запит до браузера надіслано.")

    def shutdown_everything(self):
        if self.is_running: 
            self.stop_server()
        # Автоматично зберігаємо конфігурацію
        save_config(self.config)
        self.log("INFO: Вихід...")
        self.root.after(300, self.root.destroy)

# ============================================================
# ТОЧКА ВХОДУ
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    # Налаштування стилю для Progress Bar
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=10, background=THEME["primary"], 
                   troughcolor=THEME["progress_bg"], borderwidth=0)
    
    app = KolosLauncher(root)
    root.mainloop()