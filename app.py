"""
app.py
──────
Clase BotManager: orquesta core (config, bot_runner) y ui (styles, widgets).
Aquí solo vive la lógica de coordinación — nada de colores hardcodeados,
nada de subprocess directo, nada de construcción de widgets a mano.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import threading
import os
import webbrowser
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from botcore import (load_languages, load_config, save_config, translate,
                  APP_VERSION, detect_type, start_bot, stop_bot, monitor_output,
                  check_for_updates, create_tray, PYSTRAY_AVAILABLE, send_feedback)
from ui  import (apply_styles, build_header, build_bots_tab, build_bot_card,
                 build_developer_tab, build_settings_tab)


class BotManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("900x650")

        # ── Estado ────────────────────────────────────────────────────
        self.bots:           dict = {}   # bot_name → dict con proceso y widgets
        self.developer_logs: list = []

        # ── Cargar datos persistentes ─────────────────────────────────
        self.languages       = load_languages()
        self.config          = load_config()
        self.current_language = self.config.get('language', 'en')
        self.dark_mode        = self.config.get('theme', 'dark') == 'dark'

        # ── Configurar ventana ────────────────────────────────────────
        self.root.title(self.t('app_title'))
        self.colors = apply_styles(self.dark_mode)
        self.root.configure(bg=self.colors['bg'])

        # ── Construir UI ──────────────────────────────────────────────
        self._build_ui()
        self._load_saved_bots()

        if PSUTIL_AVAILABLE:
            self._start_resource_monitor()

        # Chequear updates en background (no bloquea el arranque)
        check_for_updates(
            APP_VERSION,
            skipped_tags=self.config.get('skipped_prereleases', []),
            on_stable=lambda tag, url: self.root.after(
                0, lambda: self._show_update_banner(tag, url, is_prerelease=False)
            ),
            on_prerelease=lambda tag, url: self.root.after(
                0, lambda: self._show_update_banner(tag, url, is_prerelease=True)
            ),
            on_error=lambda msg: self.root.after(
                0, lambda: self.log(f"[updater] {msg}", '#ffaa00')
            ),
        )

        # System tray
        self._tray = create_tray(
            icon_path='icon.ico',
            on_toggle=lambda: self.root.after(0, self._toggle_window),
            on_stop_all=lambda: self.root.after(0, self.stop_all_bots),
            on_quit=lambda: self.root.after(0, self._quit_app),
        )
        if not PYSTRAY_AVAILABLE:
            self.log("[tray] Install pystray for system tray support: pip install pystray", '#ffaa00')

    # ══════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════

    def t(self, key: str, **kwargs) -> str:
        return translate(self.languages, self.current_language, key, **kwargs)

    def _save(self):
        save_config(self.config, self.bots)

    # ══════════════════════════════════════════════════════════════════
    # Construcción de UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        C = self.colors

        main = tk.Frame(self.root, bg=C['bg'])
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        self.theme_button = build_header(
            main, C, APP_VERSION, self.dark_mode,
            on_toggle_theme=self.toggle_theme,
            on_minimize_tray=self._minimize_to_tray if PYSTRAY_AVAILABLE else None,
            on_feedback=self.show_feedback_window,
        )

        # Notebook
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab: Bots
        self.bots_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.bots_tab, text=f"  {self.t('bots_tab')}  ")
        (self.canvas, self.scrollable_frame,
         self.empty_label, self.log_text) = build_bots_tab(
            self.bots_tab, C, self.t, on_add_bot=self.add_bot,
        )

        # Tab: Developer
        self.developer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.developer_tab, text=f"  {self.t('developer_tab')}  ")
        (self.bot_filter_var, self.bot_filter,
         self.log_table, self.resource_table,
         self.warning_frame) = build_developer_tab(
            self.developer_tab, C, self.t,
            on_clear_logs=self.clear_developer_logs,
            on_show_help=self.show_logging_help,
            on_filter_change=self.filter_logs,
            psutil_available=PSUTIL_AVAILABLE,
            on_show_resource_help=self.show_resource_help,
        )

        # Tab: Settings
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text=f"  {self.t('settings_tab')}  ")
        build_settings_tab(
            self.settings_tab, C, self.t,
            dark_mode=self.dark_mode,
            current_language=self.current_language,
            on_lang_change=self._on_lang_change,
            on_reset=self.reset_all_settings,
        )

    def _rebuild_ui(self):
        """Destruye y reconstruye toda la UI (usado al cambiar tema)."""
        for w in self.root.winfo_children():
            w.destroy()
        self.bots           = {}
        self.developer_logs = []
        self._build_ui()
        self._load_saved_bots()
        self._update_bot_filter()

    def _show_update_banner(self, latest_tag: str, release_url: str,
                            is_prerelease: bool = False):
        """
        Muestra un banner de update debajo del header.
        - Release estable  → banner verde simple
        - Pre-release      → banner amarillo con advertencia + checkbox "no mostrar de nuevo"
        """
        if getattr(self, '_update_banner_shown', False):
            return
        self._update_banner_shown = True

        C = self.colors

        if is_prerelease:
            banner_bg  = '#2a2200'
            accent_col = '#ffcc00'
            hover_col  = '#e6b800'
        else:
            banner_bg  = '#1a2a1a'
            accent_col = C['accent_green']
            hover_col  = C['accent_green_hover']

        banner = tk.Frame(self.root, bg=banner_bg)
        banner.pack(fill=tk.X, before=self.notebook)

        # línea de acento arriba
        tk.Frame(banner, bg=accent_col, height=1).pack(fill=tk.X)

        # fila principal
        row = tk.Frame(banner, bg=banner_bg)
        row.pack(fill=tk.X, padx=16, pady=(6, 4))

        # ícono + texto
        icon = "⚠" if is_prerelease else "⬆"
        label_text = (
            f"{icon}  Pre-release available: {latest_tag}  —  may contain bugs"
            if is_prerelease else
            f"{icon}  New version available: {latest_tag}"
        )
        tk.Label(row, text=label_text,
                 font=('Segoe UI', 9, 'bold'),
                 bg=banner_bg, fg=accent_col).pack(side=tk.LEFT)

        # botón cerrar
        tk.Button(row, text="✕",
                  bg=banner_bg, fg=C['fg_dim'],
                  font=('Segoe UI', 9), relief=tk.FLAT,
                  cursor='hand2', borderwidth=0,
                  activebackground=banner_bg,
                  command=banner.destroy).pack(side=tk.RIGHT, padx=(8, 0))

        # botón descargar
        tk.Button(row,
                  text="Download →",
                  bg=accent_col, fg='#000000',
                  font=('Segoe UI', 9, 'bold'), relief=tk.FLAT,
                  cursor='hand2', borderwidth=0, padx=10, pady=3,
                  activebackground=hover_col,
                  command=lambda: webbrowser.open(release_url)).pack(side=tk.RIGHT)

        # checkbox "no mostrar de nuevo" — solo en pre-releases
        if is_prerelease:
            skip_row = tk.Frame(banner, bg=banner_bg)
            skip_row.pack(fill=tk.X, padx=16, pady=(0, 6))

            skip_var = tk.BooleanVar(value=False)

            def on_skip_toggle():
                if skip_var.get():
                    skipped = self.config.setdefault('skipped_prereleases', [])
                    if latest_tag not in skipped:
                        skipped.append(latest_tag)
                    self._save()
                else:
                    skipped = self.config.get('skipped_prereleases', [])
                    if latest_tag in skipped:
                        skipped.remove(latest_tag)
                    self._save()

            cb = tk.Checkbutton(
                skip_row,
                text=f"Don't show this pre-release again  ({latest_tag})",
                variable=skip_var,
                command=on_skip_toggle,
                bg=banner_bg, fg=C['fg_dim'],
                selectcolor=banner_bg,
                activebackground=banner_bg,
                font=('Segoe UI', 8),
                relief=tk.FLAT, borderwidth=0, cursor='hand2',
            )
            cb.pack(side=tk.LEFT)

    # ══════════════════════════════════════════════════════════════════
    # Tema
    # ══════════════════════════════════════════════════════════════════

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.config['theme'] = 'dark' if self.dark_mode else 'light'
        self._save()
        self.colors = apply_styles(self.dark_mode)
        self.root.configure(bg=self.colors['bg'])
        self._rebuild_ui()
        mode = "Dark" if self.dark_mode else "Light"
        self.log(self.t('theme_switched', mode=mode), '#00aaff')

    # ══════════════════════════════════════════════════════════════════
    # Gestión de bots
    # ══════════════════════════════════════════════════════════════════

    def _load_saved_bots(self):
        for data in self.config.get('bots', []):
            if os.path.exists(data['file_path']):
                btype = data.get('bot_type') or detect_type(data['file_path'])
                self._add_bot_row(data['name'], data['file_path'], btype)
        if self.bots and self.empty_label.winfo_exists():
            self.empty_label.pack_forget()

    def add_bot(self):
        file_path = filedialog.askopenfilename(
            title=self.t('select_bot_file'),
            filetypes=[
                ("Bot files",   "*.py *.js"),
                ("Python",      "*.py"),
                ("Node.js",     "*.js"),
                ("All files",   "*.*"),
            ],
        )
        if not file_path:
            return

        name = Path(file_path).stem
        if name in self.bots:
            messagebox.showwarning(self.t('warning'),
                                   self.t('bot_already_exists', name=name))
            return

        btype = detect_type(file_path)
        self._add_bot_row(name, file_path, btype)
        self._save()
        self._update_bot_filter()
        if self.empty_label.winfo_exists():
            self.empty_label.pack_forget()

    def _add_bot_row(self, name: str, file_path: str, bot_type: str):
        bot_frame, inner_frame, status_label = build_bot_card(
            self.scrollable_frame, self.colors,
            bot_name=name, file_path=file_path, bot_type=bot_type,
            on_start=lambda: self.start_bot(name),
            on_stop=lambda:  self.stop_bot(name),
            on_delete=lambda: self.delete_bot(name),
        )
        self.bots[name] = {
            'process':      None,
            'file_path':    file_path,
            'bot_type':     bot_type,
            'frame':        bot_frame,
            'inner_frame':  inner_frame,
            'status_label': status_label,
            'has_logging':  False,
        }

    def delete_bot(self, name: str):
        bot = self.bots.get(name)
        if not bot:
            return
        if bot['process'] is not None:
            messagebox.showwarning(
                self.t('warning'),
                f"Stop '{name}' before deleting it."
            )
            return
        if messagebox.askyesno(self.t('confirm'),
                               f"Delete '{name}' from the list?"):
            bot['frame'].destroy()
            del self.bots[name]
            self._save()
            self._update_bot_filter()
            if not self.bots:
                self.empty_label.pack(pady=50)
            self.log(f"'{name}' removed from list", '#ffaa00')

    # ══════════════════════════════════════════════════════════════════
    # Start / Stop
    # ══════════════════════════════════════════════════════════════════

    def start_bot(self, name: str):
        bot = self.bots.get(name)
        if not bot:
            return
        if bot['process'] is not None:
            self.log(self.t('bot_is_running', name=name), '#ffaa00')
            return

        try:
            self.log(self.t('starting_bot', name=name), '#00aaff')
            process = start_bot(bot['file_path'], bot['bot_type'])
            bot['process'] = process
            bot['status_label'].config(text="●", fg=self.colors['accent_green'])
            self.log(self.t('bot_started', name=name, pid=process.pid), '#00ff00')

            monitor_output(
                name, process,
                on_line=self._on_bot_line,
                on_cmd=self._on_bot_cmd,
                on_exit=lambda n: self.root.after(0, lambda: self._on_bot_stopped(n)),
            )

        except FileNotFoundError:
            runtime = bot['bot_type']
            if runtime == 'node':
                self.log("Error: 'node' not found. Is Node.js installed?", '#ff0000')
            else:
                self.log(self.t('error_python_not_found'), '#ff0000')
        except Exception as e:
            self.log(self.t('error_starting_bot', name=name, error=str(e)), '#ff0000')

    def stop_bot(self, name: str):
        bot = self.bots.get(name)
        if not bot:
            return
        if bot['process'] is None:
            self.log(self.t('bot_not_running', name=name), '#ffaa00')
            return
        try:
            self.log(self.t('stopping_bot', name=name), '#00aaff')
            stop_bot(bot['process'])
            bot['process'] = None
            bot['status_label'].config(text="●", fg=self.colors['accent_red'])
            self.log(self.t('bot_stopped', name=name), '#00ff00')
        except Exception as e:
            self.log(self.t('error_stopping_bot', name=name, error=str(e)), '#ff0000')

    def stop_all_bots(self):
        for name, bot in list(self.bots.items()):
            if bot['process'] is not None:
                stop_bot(bot['process'])

    def has_running_bots(self) -> bool:
        return any(b['process'] is not None for b in self.bots.values())

    # ══════════════════════════════════════════════════════════════════
    # Callbacks del monitor de output
    # ══════════════════════════════════════════════════════════════════

    def _on_bot_line(self, name: str, line: str):
        self.root.after(0, lambda: self.log(f"[{name}] {line}", '#00ff00'))

    def _on_bot_cmd(self, name: str, user: str, channel: str, command: str):
        bot = self.bots.get(name)
        if bot:
            bot['has_logging'] = True
        self.root.after(0, lambda: self.add_developer_log(name, command, user, channel))

    def _on_bot_stopped(self, name: str):
        bot = self.bots.get(name)
        if bot:
            bot['process'] = None
            bot['status_label'].config(text="●", fg=self.colors['accent_red'])
            self.log(self.t('bot_stopped_unexpected', name=name), '#ffaa00')

    # ══════════════════════════════════════════════════════════════════
    # Logs
    # ══════════════════════════════════════════════════════════════════

    def log(self, message: str, color: str = '#00ff00'):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{ts}] {message}\n", ('colored',))
        self.log_text.tag_config('colored', foreground=color)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def add_developer_log(self, bot_name: str, command: str,
                          user: str, channel: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = {'time': ts, 'bot': bot_name, 'command': command,
                 'user': user, 'channel': channel}
        self.developer_logs.append(entry)
        current = self.bot_filter_var.get()
        if current == self.t('all_bots') or current == bot_name:
            self.log_table.insert('', 0, values=(ts, bot_name, command, user, channel))

    def filter_logs(self, event=None):
        selected = self.bot_filter_var.get()
        for item in self.log_table.get_children():
            self.log_table.delete(item)
        for entry in reversed(self.developer_logs):
            if selected == self.t('all_bots') or entry['bot'] == selected:
                self.log_table.insert('', 0, values=(
                    entry['time'], entry['bot'], entry['command'],
                    entry['user'], entry['channel'],
                ))

    def clear_developer_logs(self):
        self.developer_logs.clear()
        for item in self.log_table.get_children():
            self.log_table.delete(item)
        self.log(self.t('logs_cleared'), '#00aaff')

    def _update_bot_filter(self):
        self.bot_filter['values'] = [self.t('all_bots')] + list(self.bots.keys())

    # ══════════════════════════════════════════════════════════════════
    # Monitor de recursos
    # ══════════════════════════════════════════════════════════════════

    def _start_resource_monitor(self):
        def _loop():
            while True:
                try:
                    time.sleep(2)
                    self.root.after(0, self._update_resource_table)
                except Exception:
                    break
        threading.Thread(target=_loop, daemon=True).start()

    def _update_resource_table(self):
        if not PSUTIL_AVAILABLE or self.resource_table is None:
            return
        for item in self.resource_table.get_children():
            self.resource_table.delete(item)
        for name, bot in self.bots.items():
            if bot['process'] is None:
                continue
            try:
                proc    = psutil.Process(bot['process'].pid)
                ram_mb  = proc.memory_info().rss / 1024 / 1024
                cpu_pct = proc.cpu_percent(interval=None)
                display = name if bot.get('has_logging') else f"⚠️ {name}"
                self.resource_table.insert('', tk.END, values=(
                    display, f"{ram_mb:.1f} MB", f"{cpu_pct:.1f}%"
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    # ══════════════════════════════════════════════════════════════════
    # Settings
    # ══════════════════════════════════════════════════════════════════

    def _on_lang_change(self, selected_name: str, lang_options: dict):
        lang_code = next(k for k, v in lang_options.items() if v == selected_name)
        if lang_code != self.current_language:
            self.current_language = lang_code
            self.config['language'] = lang_code
            self._save()
            messagebox.showinfo(
                "Language Changed",
                "Please restart the application to apply the new language.\n\n"
                "Por favor reinicia la aplicación para aplicar el nuevo idioma.\n\n"
                "アプリケーションを再起動して新しい言語を適用してください。\n\n"
                "Bitte starten Sie die Anwendung neu, um die neue Sprache anzuwenden."
            )

    def reset_all_settings(self):
        if not messagebox.askyesno(self.t('confirm'), self.t('confirm_reset')):
            return
        self.stop_all_bots()
        self.config = {"language": "en", "theme": "dark", "bots": []}
        self._save()
        messagebox.showinfo("Info", self.t('settings_reset'))
        self.root.destroy()

    # ══════════════════════════════════════════════════════════════════
    # Ventanas de ayuda
    # ══════════════════════════════════════════════════════════════════

    def show_feedback_window(self):
        """Ventana de feedback anónimo con rating, bug report y sugerencias."""
        C   = self.colors
        win = tk.Toplevel(self.root)
        win.title("Send Feedback")
        win.geometry("480x520")
        win.configure(bg=C['bg'])
        win.resizable(False, False)

        # ── Header de la ventana ──────────────────────────────────────
        top = tk.Frame(win, bg=C['card_bg'])
        top.pack(fill=tk.X)
        tk.Frame(win, bg=C['accent'], height=2).pack(fill=tk.X)

        tk.Label(top, text="💬  Send Feedback",
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['card_bg'], fg=C['fg']).pack(side=tk.LEFT, padx=18, pady=14)
        tk.Label(top, text="Anonymous · v" + APP_VERSION,
                 font=('Consolas', 8),
                 bg=C['button_bg'], fg=C['fg_dim'],
                 padx=6, pady=2).pack(side=tk.LEFT, pady=18)

        outer = tk.Frame(win, bg=C['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # ── Tipo de feedback ─────────────────────────────────────────
        tk.Label(outer, text="TYPE", font=('Segoe UI', 8, 'bold'),
                 bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(0, 6))

        type_var = tk.StringVar(value='bug')
        type_row = tk.Frame(outer, bg=C['bg'])
        type_row.pack(fill=tk.X, pady=(0, 16))

        for val, label, emoji in [
            ('bug',         'Bug Report',  '🐛'),
            ('improvement', 'Suggestion',  '💡'),
            ('rating',      'Rating',      '⭐'),
        ]:
            btn = tk.Radiobutton(
                type_row, text=f"{emoji}  {label}",
                variable=type_var, value=val,
                bg=C['button_bg'], fg=C['fg'],
                selectcolor=C['button_active'],
                activebackground=C['button_bg'],
                font=('Segoe UI', 9), relief=tk.FLAT,
                borderwidth=0, cursor='hand2',
                padx=10, pady=6,
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))

        # ── Rating (1-5 estrellas) ────────────────────────────────────
        rating_frame = tk.Frame(outer, bg=C['bg'])
        rating_frame.pack(fill=tk.X, pady=(0, 16))

        tk.Label(rating_frame, text="RATING", font=('Segoe UI', 8, 'bold'),
                 bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(0, 6))

        rating_var = tk.IntVar(value=0)
        stars_row  = tk.Frame(rating_frame, bg=C['bg'])
        stars_row.pack(anchor='w')

        star_buttons = []

        def update_stars(value):
            rating_var.set(value)
            for i, sb in enumerate(star_buttons):
                sb.config(fg=C['accent_green'] if i < value else C['fg_dim'])

        for i in range(1, 6):
            sb = tk.Button(
                stars_row, text='★',
                font=('Segoe UI', 18), bg=C['bg'], fg=C['fg_dim'],
                relief=tk.FLAT, borderwidth=0, cursor='hand2',
                activebackground=C['bg'],
                command=lambda v=i: update_stars(v),
            )
            sb.pack(side=tk.LEFT)
            star_buttons.append(sb)

        # ── Mensaje de texto ──────────────────────────────────────────
        tk.Label(outer, text="MESSAGE", font=('Segoe UI', 8, 'bold'),
                 bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(0, 6))

        text_outer = tk.Frame(outer, bg=C['border'], padx=1, pady=1)
        text_outer.pack(fill=tk.X, pady=(0, 16))

        text_box = tk.Text(
            text_outer, height=6,
            bg=C['entry_bg'], fg=C['fg'],
            font=('Segoe UI', 10), wrap=tk.WORD,
            borderwidth=0, padx=10, pady=8,
            insertbackground=C['accent'],
            selectbackground=C['button_active'],
        )
        text_box.pack(fill=tk.X)

        placeholder = "Describe the bug, suggestion, or leave a comment..."
        text_box.insert('1.0', placeholder)
        text_box.config(fg=C['fg_dim'])

        def on_focus_in(e):
            if text_box.get('1.0', 'end-1c') == placeholder:
                text_box.delete('1.0', tk.END)
                text_box.config(fg=C['fg'])

        def on_focus_out(e):
            if not text_box.get('1.0', 'end-1c').strip():
                text_box.insert('1.0', placeholder)
                text_box.config(fg=C['fg_dim'])

        text_box.bind('<FocusIn>',  on_focus_in)
        text_box.bind('<FocusOut>', on_focus_out)

        # ── Botones ───────────────────────────────────────────────────
        btn_row = tk.Frame(outer, bg=C['bg'])
        btn_row.pack(fill=tk.X)

        status_label = tk.Label(btn_row, text="",
                                font=('Segoe UI', 9),
                                bg=C['bg'], fg=C['fg_dim'])
        status_label.pack(side=tk.LEFT)

        def do_send():
            text = text_box.get('1.0', 'end-1c').strip()
            if text == placeholder:
                text = ''

            ftype  = type_var.get()
            rating = rating_var.get() if rating_var.get() > 0 else None

            if ftype == 'rating' and rating is None:
                status_label.config(text="Please select a star rating.", fg='#ffaa00')
                return
            if not text and ftype != 'rating':
                status_label.config(text="Please write a message.", fg='#ffaa00')
                return

            send_btn.config(state='disabled')
            status_label.config(text="Sending...", fg=C['fg_dim'])

            send_feedback(
                feedback_type=ftype,
                text=text,
                rating=rating,
                app_version=APP_VERSION,
                on_success=lambda: self.root.after(0, lambda: (
                    status_label.config(text="✓ Sent! Thank you.", fg=C['accent_green']),
                    win.after(1500, win.destroy),
                )),
                on_error=lambda msg: self.root.after(0, lambda: (
                    status_label.config(text=f"✗ {msg}", fg=C['accent_red']),
                    send_btn.config(state='normal'),
                )),
            )

        ttk.Button(btn_row, text="Cancel",
                   command=win.destroy).pack(side=tk.RIGHT, padx=(6, 0))

        send_btn = ttk.Button(btn_row, text="Send →",
                              style='Add.TButton', command=do_send)
        send_btn.pack(side=tk.RIGHT)

    def show_logging_help(self):
        C   = self.colors
        win = tk.Toplevel(self.root)
        win.title(self.t('logging_help_title'))
        win.geometry("700x550")
        win.configure(bg=C['bg'])

        frame = ttk.Frame(win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=self.t('logging_help_title'),
                  font=('Segoe UI', 14, 'bold')).pack(pady=(0, 15))
        ttk.Label(frame, text=self.t('logging_help_description'),
                  wraplength=650).pack(pady=(0, 20))

        for title_key, code in [
            ('logging_help_text_commands',
             '@bot.event\nasync def on_command(ctx):\n'
             '    print(f"[CMD]|{ctx.author.name}#{ctx.author.discriminator}'
             '|#{ctx.channel.name}|{ctx.command.name}")\n\n'
             '@bot.command()\nasync def ping(ctx):\n    await ctx.send(\'Pong!\')'),
            ('logging_help_slash_commands',
             '@bot.tree.command(name="ping", description="Pong!")\n'
             'async def ping(interaction: discord.Interaction):\n'
             '    print(f"[CMD]|{interaction.user.name}#{interaction.user.discriminator}'
             '|#{interaction.channel.name}|/ping")\n'
             '    await interaction.response.send_message("Pong!")'),
        ]:
            ttk.Label(frame, text=self.t(title_key),
                      font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 5))
            box_frame = tk.Frame(frame, bg=C['entry_bg'],
                                 highlightbackground='#4d4d4d', highlightthickness=1)
            box_frame.pack(fill=tk.X, pady=(0, 6))
            widget = tk.Text(box_frame, height=5, bg=C['entry_bg'], fg=C['fg'],
                             font=('Consolas', 9), wrap=tk.WORD)
            widget.pack(fill=tk.X, padx=5, pady=5)
            widget.insert('1.0', code)
            widget.config(state='disabled')
            ttk.Button(frame, text=self.t('copy_code'),
                       command=lambda c=code: self.copy_to_clipboard(c)).pack(anchor='w', pady=(0, 12))

        ttk.Label(frame, text=self.t('logging_help_note'),
                  foreground='orange', wraplength=650, justify=tk.LEFT).pack(pady=(10, 0))

    def show_resource_help(self):
        C   = self.colors
        win = tk.Toplevel(self.root)
        win.title(self.t('resource_help_title'))
        win.geometry("500x400")
        win.configure(bg=C['bg'])

        frame = ttk.Frame(win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=self.t('resource_help_title'),
                  font=('Segoe UI', 14, 'bold')).pack(pady=(0, 15))
        info = "\n\n".join([
            f"{self.t('resource_help_ram')}\n{self.t('resource_help_ram_desc')}",
            f"{self.t('resource_help_cpu')}\n{self.t('resource_help_cpu_desc')}",
            f"{self.t('resource_help_zero')}\n{self.t('resource_help_zero_desc')}",
            f"{self.t('resource_help_warning')}\n{self.t('resource_help_warning_desc')}",
        ])
        ttk.Label(frame, text=info, justify=tk.LEFT, wraplength=450).pack(pady=(0, 15))
        ttk.Button(frame, text=self.t('close'), command=win.destroy).pack()

    def copy_to_clipboard(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log(self.t('code_copied'), '#00aaff')

    # ══════════════════════════════════════════════════════════════════
    # Cierre
    # ══════════════════════════════════════════════════════════════════

    def on_closing(self):
        if self.has_running_bots():
            if messagebox.askyesno(self.t('confirm'), self.t('bots_running_exit')):
                self.stop_all_bots()
                self._quit_app()
        else:
            self._quit_app()

    def _minimize_to_tray(self):
        """Oculta la ventana y la manda al tray."""
        self.root.withdraw()

    def _toggle_window(self):
        """Muestra u oculta la ventana (llamado desde click izquierdo en tray)."""
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        else:
            self.root.withdraw()

    def _quit_app(self):
        """Cierra completamente la app, deteniendo el tray si existe."""
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.root.destroy()