"""
ui/widgets.py
─────────────
Funciones puras de construcción de UI.
Cada función recibe el frame padre, la paleta de colores, callbacks, y devuelve
los widgets que el caller necesita referenciar (ej: status_label, log_text).
No tienen estado propio — toda la lógica vive en app.py.
"""

import tkinter as tk
from tkinter import ttk


# ── Header ────────────────────────────────────────────────────────────────────

def build_header(parent, colors, version: str, dark_mode: bool,
                 on_toggle_theme, on_minimize_tray=None,
                 on_feedback=None) -> tk.Button:
    """Construye la barra de título. Devuelve el botón de tema."""
    C = colors

    header = tk.Frame(parent, bg=C['card_bg'], height=56)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    # línea de acento debajo del header
    tk.Frame(parent, bg=C['accent'], height=2).pack(fill=tk.X)

    tk.Label(header, text="⬡", font=('Segoe UI', 18),
             bg=C['card_bg'], fg=C['accent']).pack(side=tk.LEFT, padx=(18, 6), pady=10)

    tk.Label(header, text="Bot Manager", font=('Segoe UI', 14, 'bold'),
             bg=C['card_bg'], fg=C['fg']).pack(side=tk.LEFT, pady=10)

    tk.Label(header, text=version, font=('Consolas', 8),
             bg=C['button_bg'], fg=C['fg_dim'],
             padx=6, pady=2).pack(side=tk.LEFT, padx=(8, 0), pady=16)

    # botón tema
    theme_btn = tk.Button(
        header,
        text="🌙" if dark_mode else "☀️",
        font=('Segoe UI', 14),
        bg=C['card_bg'], fg=C['fg'],
        relief=tk.FLAT, cursor='hand2',
        command=on_toggle_theme, borderwidth=0,
        activebackground=C['card_bg'],
    )
    theme_btn.pack(side=tk.RIGHT, padx=(4, 18))

    # botón minimizar al tray
    if on_minimize_tray:
        tk.Button(
            header,
            text="⬛",
            font=('Segoe UI', 11),
            bg=C['card_bg'], fg=C['fg_dim'],
            relief=tk.FLAT, cursor='hand2',
            command=on_minimize_tray, borderwidth=0,
            activebackground=C['card_bg'],
            activeforeground=C['accent'],
        ).pack(side=tk.RIGHT, padx=(4, 0))

    # botón feedback
    if on_feedback:
        tk.Button(
            header,
            text="💬",
            font=('Segoe UI', 13),
            bg=C['card_bg'], fg=C['fg_dim'],
            relief=tk.FLAT, cursor='hand2',
            command=on_feedback, borderwidth=0,
            activebackground=C['card_bg'],
            activeforeground=C['accent'],
        ).pack(side=tk.RIGHT, padx=(4, 0))

    return theme_btn


# ── Tab: Bots ─────────────────────────────────────────────────────────────────

def build_bots_tab(parent, colors, t, on_add_bot) -> tuple:
    """
    Construye el contenido del tab Bots.
    Devuelve (scrollable_frame, empty_label, log_text, canvas).
    """
    C = colors

    # toolbar
    toolbar = tk.Frame(parent, bg=C['bg'])
    toolbar.pack(fill=tk.X, padx=16, pady=(14, 8))
    tk.Label(toolbar, text="BOTS", font=('Segoe UI', 8, 'bold'),
             bg=C['bg'], fg=C['fg_dim']).pack(side=tk.LEFT)
    ttk.Button(toolbar, text="+ Add Bot", style='Add.TButton',
               command=on_add_bot).pack(side=tk.RIGHT)

    ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=16)

    # lista scrollable
    canvas_frame = tk.Frame(parent, bg=C['bg'])
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(10, 0))

    canvas = tk.Canvas(canvas_frame, bg=C['bg'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

    scrollable_frame = tk.Frame(canvas, bg=C['bg'])
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    empty_label = tk.Label(
        scrollable_frame,
        text="No bots yet  ·  Click «+ Add Bot» to get started",
        font=('Segoe UI', 10), bg=C['bg'], fg=C['fg_dim'],
    )
    empty_label.pack(pady=40)

    # terminal de logs
    log_outer = tk.Frame(parent, bg=C['border'], pady=1)
    log_outer.pack(fill=tk.X, padx=16, pady=(10, 14))

    log_frame = tk.Frame(log_outer, bg=C['entry_bg'])
    log_frame.pack(fill=tk.BOTH, expand=True)

    log_header = tk.Frame(log_frame, bg=C['button_bg'])
    log_header.pack(fill=tk.X)

    for dot_color in ('#ff5f57', '#febc2e', '#28c840'):
        tk.Label(log_header, text='●', font=('Arial', 8),
                 bg=C['button_bg'], fg=dot_color).pack(side=tk.LEFT, padx=(6, 0), pady=4)
    tk.Label(log_header, text=t('system_logs'), font=('Segoe UI', 8, 'bold'),
             bg=C['button_bg'], fg=C['fg_dim']).pack(side=tk.LEFT, padx=8)

    log_text = tk.Text(
        log_frame, height=5,
        bg=C['entry_bg'], fg='#00e5a0',
        font=('Consolas', 9), wrap=tk.WORD,
        state='disabled', borderwidth=0,
        insertbackground=C['accent'],
        selectbackground=C['button_active'],
    )
    log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

    return canvas, scrollable_frame, empty_label, log_text


# ── Bot card ──────────────────────────────────────────────────────────────────

def build_bot_card(parent, colors, bot_name: str, file_path: str,
                   bot_type: str, on_start, on_stop, on_delete) -> tk.Label:
    """
    Construye la card de un bot dentro del scrollable_frame.
    Devuelve el status_label para que app.py pueda actualizarlo.
    """
    C       = colors
    is_node = bot_type == 'node'
    side_color = '#f7df1e' if is_node else C['accent']

    bot_frame = tk.Frame(parent, bg=C['bg'])
    bot_frame.pack(fill=tk.X, pady=4, padx=4)

    outer = tk.Frame(bot_frame, bg=C['border'], padx=1, pady=1)
    outer.pack(fill=tk.X)

    inner_frame = tk.Frame(outer, bg=C['card_bg'])
    inner_frame.pack(fill=tk.X)

    # barra lateral de color
    side_bar = tk.Frame(inner_frame, bg=side_color, width=3)
    side_bar.pack(side=tk.LEFT, fill=tk.Y)
    side_bar.pack_propagate(False)

    # nombre + path
    content = tk.Frame(inner_frame, bg=C['card_bg'])
    content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

    tk.Label(content, text=bot_name, bg=C['card_bg'], fg=C['fg'],
             font=('Segoe UI', 11, 'bold'), anchor='w').pack(side=tk.LEFT, pady=14)

    short_path = file_path if len(file_path) < 45 else '…' + file_path[-42:]
    tk.Label(content, text=short_path, bg=C['card_bg'], fg=C['fg_dim'],
             font=('Consolas', 8), anchor='w').pack(side=tk.LEFT, padx=(10, 0), pady=14)

    # controles
    controls = tk.Frame(inner_frame, bg=C['card_bg'])
    controls.pack(side=tk.RIGHT, padx=12, pady=10)

    # badge tipo
    badge_bg = '#3a3000' if is_node else '#002a35'
    badge_fg = '#f7df1e' if is_node else C['accent']
    tk.Label(controls, text='JS' if is_node else 'PY',
             bg=badge_bg, fg=badge_fg,
             font=('Consolas', 8, 'bold'), padx=7, pady=2).pack(side=tk.LEFT, padx=(0, 10))

    # status dot
    status_label = tk.Label(controls, text="●", bg=C['card_bg'],
                            fg=C['accent_red'], font=('Arial', 11))
    status_label.pack(side=tk.LEFT, padx=(0, 8))

    ttk.Button(controls, text="▶  Run",  style='Start.TButton',
               command=on_start).pack(side=tk.LEFT, padx=(0, 4))
    ttk.Button(controls, text="■  Stop", style='Stop.TButton',
               command=on_stop).pack(side=tk.LEFT, padx=(0, 4))

    tk.Button(controls, text="✕",
              bg=C['button_bg'], fg=C['fg_dim'],
              font=('Segoe UI', 9), relief=tk.FLAT, cursor='hand2', borderwidth=0,
              activebackground=C['button_active'], activeforeground=C['accent_red'],
              command=on_delete).pack(side=tk.LEFT, padx=(0, 4))

    # devolvemos frame raíz y status_label
    return bot_frame, inner_frame, status_label


# ── Tab: Developer ────────────────────────────────────────────────────────────

def build_developer_tab(parent, colors, t,
                        on_clear_logs, on_show_help,
                        on_filter_change,
                        psutil_available: bool,
                        on_show_resource_help) -> tuple:
    """
    Construye el tab Developer.
    Devuelve (bot_filter_var, bot_filter, log_table, resource_table | None, warning_frame).
    """
    C = colors

    # toolbar
    toolbar = tk.Frame(parent, bg=C['bg'])
    toolbar.pack(fill=tk.X, padx=16, pady=(14, 8))
    tk.Label(toolbar, text="COMMAND LOGS", font=('Segoe UI', 8, 'bold'),
             bg=C['bg'], fg=C['fg_dim']).pack(side=tk.LEFT)

    ttk.Button(toolbar, text="Clear", command=on_clear_logs).pack(side=tk.RIGHT, padx=(4, 0))
    ttk.Button(toolbar, text="?", width=3, command=on_show_help).pack(side=tk.RIGHT, padx=(0, 4))

    bot_filter_var = tk.StringVar(value=t('all_bots'))
    bot_filter = ttk.Combobox(toolbar, textvariable=bot_filter_var,
                              state='readonly', width=18)
    bot_filter['values'] = [t('all_bots')]
    bot_filter.pack(side=tk.RIGHT, padx=(0, 12))
    tk.Label(toolbar, text="Filter:", font=('Segoe UI', 9),
             bg=C['bg'], fg=C['fg_dim']).pack(side=tk.RIGHT)
    bot_filter.bind('<<ComboboxSelected>>', on_filter_change)

    ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=16)

    # warning frame (oculto por defecto)
    warning_frame = tk.Frame(parent, bg='#2a2000',
                             highlightbackground='#ffaa00', highlightthickness=1)

    # tabla de logs
    table_outer = tk.Frame(parent, bg=C['border'], padx=1, pady=1)
    table_outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
    table_frame = tk.Frame(table_outer, bg=C['entry_bg'])
    table_frame.pack(fill=tk.BOTH, expand=True)

    columns = ('time', 'bot', 'command', 'user', 'channel')
    log_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

    for col, label, width, anchor in [
        ('time',    t('time'),    75,  'center'),
        ('bot',     t('bot'),    120,  'w'),
        ('command', t('command'),160,  'w'),
        ('user',    t('user'),  150,  'w'),
        ('channel', t('channel'),150,  'w'),
    ]:
        log_table.heading(col, text=label)
        log_table.column(col, width=width, anchor=anchor)

    table_sb = ttk.Scrollbar(table_frame, orient="vertical", command=log_table.yview)
    log_table.configure(yscrollcommand=table_sb.set)
    log_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    table_sb.pack(side=tk.RIGHT, fill=tk.Y)

    # monitor de recursos
    resource_table = None
    if psutil_available:
        res_header = tk.Frame(parent, bg=C['bg'])
        res_header.pack(fill=tk.X, padx=16, pady=(0, 6))
        tk.Label(res_header, text="RESOURCE MONITOR", font=('Segoe UI', 8, 'bold'),
                 bg=C['bg'], fg=C['fg_dim']).pack(side=tk.LEFT)
        ttk.Button(res_header, text="?", width=3,
                   command=on_show_resource_help).pack(side=tk.LEFT, padx=8)

        res_outer = tk.Frame(parent, bg=C['border'], padx=1, pady=1)
        res_outer.pack(fill=tk.X, padx=16, pady=(0, 16))
        res_inner = tk.Frame(res_outer, bg=C['entry_bg'])
        res_inner.pack(fill=tk.X)

        resource_table = ttk.Treeview(res_inner, columns=('bot', 'ram', 'cpu'),
                                      show='headings', height=4)
        resource_table.heading('bot', text=t('bot'))
        resource_table.heading('ram', text=t('ram_usage'))
        resource_table.heading('cpu', text=t('cpu_usage'))
        resource_table.column('bot', width=250)
        resource_table.column('ram', width=150, anchor='center')
        resource_table.column('cpu', width=150, anchor='center')
        resource_table.pack(fill=tk.X)
    else:
        tk.Label(parent, text=t('install_psutil'), font=('Segoe UI', 9),
                 justify=tk.CENTER, bg=C['bg'], fg='#ffaa00').pack(pady=16)

    return bot_filter_var, bot_filter, log_table, resource_table, warning_frame


# ── Tab: Settings ─────────────────────────────────────────────────────────────

def build_settings_tab(parent, colors, t,
                       dark_mode: bool,
                       current_language: str,
                       on_lang_change,
                       on_reset) -> None:
    """Construye el tab Settings."""
    C = colors

    outer = tk.Frame(parent, bg=C['bg'])
    outer.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

    tk.Label(outer, text="SETTINGS", font=('Segoe UI', 8, 'bold'),
             bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(0, 16))
    ttk.Separator(outer, orient='horizontal').pack(fill=tk.X, pady=(0, 20))

    # Language
    lang_block = tk.Frame(outer, bg=C['bg'])
    lang_block.pack(fill=tk.X, pady=(0, 20))
    tk.Label(lang_block, text="Language", font=('Segoe UI', 11, 'bold'),
             bg=C['bg'], fg=C['fg']).pack(anchor='w')
    tk.Label(lang_block, text="Interface language (restart required)",
             font=('Segoe UI', 9), bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(2, 8))

    lang_options = {'en': 'English', 'es': 'Español', 'ja': '日本語', 'de': 'Deutsch'}
    lang_var = tk.StringVar(value=lang_options.get(current_language, 'English'))
    lang_combo = ttk.Combobox(lang_block, textvariable=lang_var,
                              state='readonly', width=22,
                              values=list(lang_options.values()))
    lang_combo.pack(anchor='w')
    lang_combo.bind('<<ComboboxSelected>>',
                    lambda e: on_lang_change(lang_var.get(), lang_options))

    ttk.Separator(outer, orient='horizontal').pack(fill=tk.X, pady=(16, 20))

    # Theme
    theme_block = tk.Frame(outer, bg=C['bg'])
    theme_block.pack(fill=tk.X, pady=(0, 20))
    tk.Label(theme_block, text="Theme", font=('Segoe UI', 11, 'bold'),
             bg=C['bg'], fg=C['fg']).pack(anchor='w')
    mode_text = "Dark mode active" if dark_mode else "Light mode active"
    tk.Label(theme_block, text=f"{mode_text}  ·  Use the 🌙/☀️ button in the header to toggle",
             font=('Segoe UI', 9), bg=C['bg'], fg=C['fg_dim']).pack(anchor='w', pady=(2, 0))

    ttk.Separator(outer, orient='horizontal').pack(fill=tk.X, pady=20)

    # Danger Zone
    reset_block = tk.Frame(outer, bg=C['bg'])
    reset_block.pack(fill=tk.X)
    tk.Label(reset_block, text="Danger Zone", font=('Segoe UI', 11, 'bold'),
             bg=C['bg'], fg=C['accent_red']).pack(anchor='w')
    tk.Label(reset_block, text=t('reset_warning'), font=('Segoe UI', 9),
             bg=C['bg'], fg=C['fg_dim'], wraplength=440, justify=tk.LEFT).pack(anchor='w', pady=(4, 10))
    ttk.Button(reset_block, text=t('reset_settings'),
               style='Stop.TButton', command=on_reset).pack(anchor='w')