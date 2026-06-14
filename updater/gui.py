from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any, Callable

from .config import UpdaterConfig, load_config, save_config
from .models import UpdateInfo, UpdaterError
from .update_service import UpdateService


THEME = {
    "bg": "#f4f6f8",
    "panel": "#ffffff",
    "border": "#d8dee9",
    "primary": "#1f6feb",
    "primary_hover": "#1557c0",
    "secondary": "#344054",
    "secondary_hover": "#1d2939",
    "success": "#1a7f37",
    "success_hover": "#116329",
    "disabled_bg": "#e5e7eb",
    "disabled_fg": "#98a2b3",
    "warning": "#9a6700",
    "danger": "#cf222e",
    "text": "#24292f",
    "muted": "#57606a",
    "log_bg": "#0f172a",
    "log_fg": "#dbeafe",
}


class UpdaterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.service = UpdateService(self.config)
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.update_info: UpdateInfo | None = None
        self.worker: threading.Thread | None = None

        self.title("Kolos Updater")
        self.geometry("900x640")
        self.minsize(820, 560)
        self.configure(bg=THEME["bg"])
        self._set_icon()
        self._configure_styles()
        self._build_ui()
        self.after(100, self._process_events)

        self._load_current_version()
        if self.config.auto_check_on_start:
            self.after(500, self.check_updates)

    def _set_icon(self) -> None:
        icon_path = Path(self.config.repo_dir) / "kolos.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=THEME["bg"])
        style.configure("Card.TFrame", background=THEME["panel"], relief="solid", borderwidth=1)
        style.configure("TLabel", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=THEME["muted"])
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=THEME["text"])
        style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 8))
        style.configure("Tool.TButton", font=("Segoe UI", 9), padding=(10, 7))
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#e5e7eb",
            background=THEME["primary"],
            bordercolor="#e5e7eb",
            lightcolor=THEME["primary"],
            darkcolor=THEME["primary"],
        )
        style.configure(
            "Treeview",
            rowheight=30,
            font=("Segoe UI", 9),
            background=THEME["panel"],
            fieldbackground=THEME["panel"],
            bordercolor=THEME["border"],
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Kolos Desktop Updater", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Оновлення коду, міграцій і резервне копіювання SQLite",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.status_label = tk.Label(
            header,
            text="○ Готово",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["panel"],
            fg=THEME["muted"],
            padx=14,
            pady=8,
            bd=1,
            relief="solid",
        )
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e")

        versions = self._card(root, row=1)
        versions.columnconfigure((1, 3), weight=1)
        self.current_var = tk.StringVar(value="...")
        self.latest_var = tk.StringVar(value="...")
        self.count_var = tk.StringVar(value="0")
        self.backup_dir_var = tk.StringVar(value=str(self.config.backups_dir))

        self._field(versions, "Поточна версія", self.current_var, 0, 0)
        self._field(versions, "Остання версія", self.latest_var, 0, 2)
        self._field(versions, "Нових комітів", self.count_var, 1, 0)
        self._backup_dir_field(versions, 1, 2)

        actions = ttk.Frame(root)
        actions.grid(row=2, column=0, sticky="ew", pady=16)
        actions.columnconfigure(0, weight=1)

        left_actions = ttk.Frame(actions)
        left_actions.grid(row=0, column=0, sticky="w")
        self.check_button = self._action_button(
            left_actions,
            text="↻ Перевірити оновлення",
            command=self.check_updates,
            variant="primary",
        )
        self.check_button.pack(side="left", padx=(0, 8))
        self.update_button = self._action_button(
            left_actions,
            text="⬇ Оновлення недоступне",
            command=self.install_update,
            variant="success",
            enabled=False,
        )
        self.update_button.pack(side="left", padx=(0, 8))
        ttk.Button(
            left_actions,
            text="📁 Відкрити backups",
            command=self.open_backups_folder,
            style="Tool.TButton",
        ).pack(side="left")

        right_actions = ttk.Frame(actions)
        right_actions.grid(row=0, column=1, sticky="e")
        ttk.Button(right_actions, text="Закрити", command=self.destroy, style="Tool.TButton").pack(side="right")

        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress.grid(row=3, column=0, sticky="ew", pady=(0, 16))

        body = ttk.Frame(root)
        body.grid(row=4, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        commits_card = self._card(body, row=0, column=0, padding=10)
        commits_card.rowconfigure(1, weight=1)
        commits_card.columnconfigure(0, weight=1)
        ttk.Label(commits_card, text="Changelog", font=("Segoe UI", 12, "bold"), background=THEME["panel"]).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        columns = ("date", "author", "message")
        self.commits = ttk.Treeview(commits_card, columns=columns, show="headings", height=10)
        self.commits.heading("date", text="Дата")
        self.commits.heading("author", text="Автор")
        self.commits.heading("message", text="Повідомлення")
        self.commits.column("date", width=135, anchor="w")
        self.commits.column("author", width=120, anchor="w")
        self.commits.column("message", width=280, anchor="w")
        self.commits.grid(row=1, column=0, sticky="nsew")
        self.commits.bind("<Double-1>", lambda _event: self.show_update_dialog())

        log_card = self._card(body, row=0, column=1, padding=10)
        log_card.rowconfigure(1, weight=1)
        log_card.columnconfigure(0, weight=1)
        ttk.Label(log_card, text="Лог", font=("Segoe UI", 12, "bold"), background=THEME["panel"]).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.log_text = scrolledtext.ScrolledText(
            log_card,
            height=14,
            bg=THEME["log_bg"],
            fg=THEME["log_fg"],
            insertbackground=THEME["log_fg"],
            font=("Consolas", 9),
            relief="flat",
            wrap="word",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

    def _card(self, parent: tk.Widget, row: int, column: int = 0, padding: int = 16) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=padding)
        frame.grid(row=row, column=column, sticky="nsew", padx=(0, 10 if column == 0 else 0))
        return frame

    def _action_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        variant: str,
        enabled: bool = True,
    ) -> tk.Button:
        colors = self._button_colors(variant)
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            bd=0,
            relief="flat",
            cursor="hand2",
            bg=colors["bg"],
            fg="#ffffff",
            activebackground=colors["hover"],
            activeforeground="#ffffff",
            disabledforeground=THEME["disabled_fg"],
            highlightthickness=0,
        )
        button.configure(takefocus=True)
        button.bind("<Enter>", lambda _event: self._button_hover(button, variant, True))
        button.bind("<Leave>", lambda _event: self._button_hover(button, variant, False))
        self._set_button_enabled(button, enabled, variant)
        return button

    def _button_colors(self, variant: str) -> dict[str, str]:
        if variant == "success":
            return {"bg": THEME["success"], "hover": THEME["success_hover"]}
        if variant == "primary":
            return {"bg": THEME["primary"], "hover": THEME["primary_hover"]}
        return {"bg": THEME["secondary"], "hover": THEME["secondary_hover"]}

    def _button_hover(self, button: tk.Button, variant: str, is_hovered: bool) -> None:
        if str(button.cget("state")) == "disabled":
            return
        colors = self._button_colors(variant)
        button.configure(bg=colors["hover"] if is_hovered else colors["bg"])

    def _set_button_enabled(self, button: tk.Button, enabled: bool, variant: str) -> None:
        colors = self._button_colors(variant)
        if enabled:
            button.configure(
                state="normal",
                bg=colors["bg"],
                fg="#ffffff",
                activebackground=colors["hover"],
                cursor="hand2",
            )
        else:
            button.configure(
                state="disabled",
                bg=THEME["disabled_bg"],
                fg=THEME["disabled_fg"],
                activebackground=THEME["disabled_bg"],
                cursor="arrow",
            )

    def _field(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int, column: int) -> None:
        ttk.Label(parent, text=label, background=THEME["panel"], style="Muted.TLabel").grid(
            row=row * 2, column=column, sticky="w", padx=(0, 18), pady=(0, 2)
        )
        ttk.Label(parent, textvariable=variable, background=THEME["panel"], font=("Segoe UI", 10, "bold")).grid(
            row=row * 2 + 1, column=column, sticky="w", padx=(0, 18), pady=(0, 10)
        )

    def _backup_dir_field(self, parent: ttk.Frame, row: int, column: int) -> None:
        ttk.Label(parent, text="Папка backup", background=THEME["panel"], style="Muted.TLabel").grid(
            row=row * 2, column=column, sticky="w", pady=(0, 2)
        )
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row * 2 + 1, column=column, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        ttk.Label(
            frame,
            textvariable=self.backup_dir_var,
            background=THEME["panel"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(frame, text="Змінити", command=self.change_backup_dir).grid(row=0, column=1, padx=(8, 0))

    def _load_current_version(self) -> None:
        try:
            short_commit = self.service.git.get_short_commit()
            self.current_var.set(short_commit)
            self._set_status("✓ Поточну версію визначено", "success")
        except UpdaterError as exc:
            self.current_var.set("невідомо")
            self._set_status("⚠ Помилка Git", "warning")
            self._log(str(exc))

    def check_updates(self) -> None:
        if self._is_busy():
            return
        self._clear_commits()
        self._set_buttons_busy(True)
        self.progress_var.set(15)
        self._set_status("↻ Перевірка оновлень", "primary")
        self._log("Перевірка віддаленого репозиторію...")
        self._run_worker(self._check_updates_worker)

    def _check_updates_worker(self) -> None:
        try:
            info = self.service.check_for_updates(log=self._thread_log)
            self.events.put(("checked", info))
        except Exception as exc:
            self.events.put(("error", exc))

    def install_update(self) -> None:
        if self._is_busy() or not self.update_info or not self.update_info.has_updates:
            return
        if not self._confirm_update(self.update_info):
            return

        self._set_buttons_busy(True)
        self.progress_var.set(0)
        self._set_status("⬇ Встановлення оновлення", "primary")
        self._log("Початок оновлення...")
        self._run_worker(self._install_update_worker)

    def _install_update_worker(self) -> None:
        try:
            backup = self.service.install_update(log=self._thread_log, progress=self._thread_progress)
            self.events.put(("installed", backup))
        except Exception as exc:
            self.events.put(("error", exc))

    def show_update_dialog(self) -> None:
        if not self.update_info or not self.update_info.has_updates:
            messagebox.showinfo("Оновлення", "Нових оновлень не знайдено.")
            return
        self._confirm_update(self.update_info, readonly=True)

    def _confirm_update(self, info: UpdateInfo, readonly: bool = False) -> bool:
        dialog = tk.Toplevel(self)
        dialog.title("Доступне оновлення")
        dialog.geometry("680x460")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=THEME["bg"])
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(2, weight=1)

        summary = (
            f"Знайдено {info.commit_count} нових змін.\n"
            f"Поточна версія: {info.local_commit[:10]}\n"
            f"Нова версія: {info.remote_commit[:10]}"
        )
        ttk.Label(dialog, text="Доступне оновлення", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 4)
        )
        ttk.Label(dialog, text=summary, style="Muted.TLabel").grid(row=1, column=0, sticky="new", padx=18)

        text = scrolledtext.ScrolledText(dialog, height=14, font=("Segoe UI", 10), wrap="word", relief="flat")
        text.grid(row=2, column=0, sticky="nsew", padx=18, pady=12)
        for commit in info.commits:
            date_text = commit.committed_at.strftime("%Y-%m-%d %H:%M")
            text.insert("end", f"• {commit.message}\n  {date_text} | {commit.author} | {commit.short_hash}\n\n")
        text.configure(state="disabled")

        buttons = ttk.Frame(dialog)
        buttons.grid(row=3, column=0, sticky="e", padx=18, pady=(0, 18))

        result = tk.BooleanVar(value=False)

        def approve() -> None:
            result.set(True)
            dialog.destroy()

        ttk.Button(buttons, text="Закрити" if readonly else "Скасувати", command=dialog.destroy).pack(
            side="right", padx=(8, 0)
        )
        if not readonly:
            ttk.Button(buttons, text="Оновити", command=approve).pack(side="right")

        self.wait_window(dialog)
        return result.get()

    def change_backup_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self.config.backups_dir), title="Оберіть папку backups")
        if not selected:
            return
        self.config = UpdaterConfig(
            repo_dir=self.config.repo_dir,
            remote_name=self.config.remote_name,
            branch_name=self.config.branch_name,
            manage_py=self.config.manage_py,
            database_path=self.config.database_path,
            backups_dir=Path(selected),
            use_daily_backup_folders=self.config.use_daily_backup_folders,
            requirements_file=self.config.requirements_file,
            auto_check_on_start=self.config.auto_check_on_start,
            restart_command=self.config.restart_command,
        )
        self.service = UpdateService(self.config)
        save_config(self.config)
        self.backup_dir_var.set(str(self.config.backups_dir))
        self._log(f"Папку backup змінено: {self.config.backups_dir}")

    def open_backups_folder(self) -> None:
        backups_dir = Path(self.config.backups_dir)
        backups_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(backups_dir)
        except OSError as exc:
            messagebox.showerror("Backups", f"Не вдалося відкрити папку:\n{exc}")

    def _process_events(self) -> None:
        while True:
            try:
                event, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "log":
                self._log(str(payload))
            elif event == "progress":
                value, message = payload
                self.progress_var.set(value)
                self._set_status(message, "primary")
            elif event == "checked":
                self._on_checked(payload)
            elif event == "installed":
                self._on_installed(payload)
            elif event == "error":
                self._on_error(payload)
        self.after(100, self._process_events)

    def _on_checked(self, info: UpdateInfo) -> None:
        self.update_info = info
        self.current_var.set(info.local_commit[:10])
        self.latest_var.set(info.remote_commit[:10])
        self.count_var.set(str(info.commit_count))
        self.progress_var.set(100)
        self._populate_commits(info)
        self._set_buttons_busy(False)
        if info.has_updates:
            self._set_update_button_available(True)
            self._set_status("✓ Оновлення доступне", "success")
            self._log(f"Доступне оновлення: {info.commit_count} нових комітів.")
            self.show_update_dialog()
        else:
            self._set_update_button_available(False)
            self._set_status("✓ Ви використовуєте останню версію", "success")
            self._log("Нових оновлень не знайдено.")

    def _on_installed(self, backup: Any) -> None:
        self._set_buttons_busy(False)
        self._set_update_button_available(False)
        self._set_status("✓ Оновлення завершено", "success")
        self._log(f"Оновлення завершено. Backup збережено: {backup.backup_path}")
        messagebox.showinfo(
            "Оновлення завершено",
            f"Програму оновлено успішно.\n\nBackup збережено:\n{backup.backup_path}",
        )
        self._load_current_version()

    def _on_error(self, exc: Exception) -> None:
        self._set_buttons_busy(False)
        self.progress_var.set(0)
        self._set_status("✕ Помилка", "danger")
        message = str(exc) or exc.__class__.__name__
        self._log(f"Помилка: {message}")
        messagebox.showerror("Помилка оновлення", message)

    def _populate_commits(self, info: UpdateInfo) -> None:
        self._clear_commits()
        for commit in info.commits:
            self.commits.insert(
                "",
                "end",
                values=(
                    commit.committed_at.strftime("%Y-%m-%d %H:%M"),
                    commit.author,
                    commit.message,
                ),
            )

    def _clear_commits(self) -> None:
        for item in self.commits.get_children():
            self.commits.delete(item)

    def _run_worker(self, target: Callable[[], None]) -> None:
        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def _is_busy(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def _set_buttons_busy(self, busy: bool) -> None:
        self._set_button_enabled(self.check_button, not busy, "primary")
        if busy:
            self.update_button.configure(text="⏳ Зачекайте...")
            self._set_button_enabled(self.update_button, False, "success")
        elif self.update_info and self.update_info.has_updates:
            self._set_update_button_available(True)
        else:
            self._set_update_button_available(False)

    def _set_update_button_available(self, available: bool) -> None:
        if available:
            self.update_button.configure(text="⬇ Оновити зараз")
            self._set_button_enabled(self.update_button, True, "success")
        else:
            self.update_button.configure(text="⬇ Оновлення недоступне")
            self._set_button_enabled(self.update_button, False, "success")

    def _set_status(self, text: str, color_key: str) -> None:
        status_colors = {
            "primary": ("#eff6ff", THEME["primary"]),
            "success": ("#f0fdf4", THEME["success"]),
            "warning": ("#fffbeb", THEME["warning"]),
            "danger": ("#fef2f2", THEME["danger"]),
        }
        bg_color, fg_color = status_colors.get(color_key, (THEME["panel"], THEME["text"]))
        self.status_label.configure(text=text, bg=bg_color, fg=fg_color)

    def _thread_log(self, message: str) -> None:
        self.events.put(("log", message))

    def _thread_progress(self, value: int, message: str) -> None:
        self.events.put(("progress", (value, message)))

    def _log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def run_app() -> None:
    app = UpdaterApp()
    app.mainloop()
