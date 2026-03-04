"""
ui/styles.py
────────────
Paleta de colores y configuración de ttk.Style.
Para cambiar cualquier color de la app, solo tocás este archivo.
"""

from tkinter import ttk

# ── Paletas ───────────────────────────────────────────────────────────────────

DARK = {
    'bg':            '#0d0f12',
    'card_bg':       '#151820',
    'fg':            '#e2e8f0',
    'fg_dim':        '#64748b',
    'button_bg':     '#1e2330',
    'button_active': '#252d3d',
    'accent':        '#00d4ff',
    'accent_dim':    '#0099bb',
    'accent_green':  '#00e5a0',
    'accent_green_hover': '#00c488',
    'accent_red':    '#ff4d6a',
    'accent_red_hover':   '#e0334f',
    'entry_bg':      '#1a1f2e',
    'entry_fg':      '#e2e8f0',
    'border':        '#1e2d40',
}

LIGHT = {
    'bg':            '#f1f5f9',
    'card_bg':       '#ffffff',
    'fg':            '#0f172a',
    'fg_dim':        '#94a3b8',
    'button_bg':     '#e2e8f0',
    'button_active': '#cbd5e1',
    'accent':        '#0284c7',
    'accent_dim':    '#0369a1',
    'accent_green':  '#059669',
    'accent_green_hover': '#047857',
    'accent_red':    '#dc2626',
    'accent_red_hover':   '#b91c1c',
    'entry_bg':      '#f8fafc',
    'entry_fg':      '#0f172a',
    'border':        '#cbd5e1',
}

# ── Fuentes ───────────────────────────────────────────────────────────────────

FONTS = {
    'body':    ('Segoe UI', 10),
    'bold':    ('Segoe UI', 10, 'bold'),
    'small':   ('Segoe UI', 9),
    'small_bold': ('Segoe UI', 9, 'bold'),
    'caps':    ('Segoe UI', 8, 'bold'),
    'title':   ('Segoe UI', 15, 'bold'),
    'header':  ('Segoe UI', 14, 'bold'),
    'mono':    ('Consolas', 9),
    'mono_sm': ('Consolas', 8),
    'tab':     ('Segoe UI', 10),
    'tab_sel': ('Segoe UI', 10, 'bold'),
}


def get_palette(dark_mode: bool) -> dict:
    """Devuelve la paleta correcta según el tema."""
    return DARK.copy() if dark_mode else LIGHT.copy()


def apply_styles(dark_mode: bool) -> dict:
    """
    Aplica todos los estilos ttk y devuelve la paleta de colores activa.
    Llamar cada vez que cambia el tema.
    """
    C = get_palette(dark_mode)
    s = ttk.Style()
    s.theme_use('clam')

    # Frames y labels base
    s.configure('TFrame',  background=C['bg'])
    s.configure('TLabel',  background=C['bg'], foreground=C['fg'],     font=FONTS['body'])
    s.configure('Dim.TLabel',    background=C['bg'], foreground=C['fg_dim'], font=FONTS['small'])
    s.configure('Title.TLabel',  background=C['bg'], foreground=C['fg'],     font=FONTS['title'])
    s.configure('Accent.TLabel', background=C['bg'], foreground=C['accent'], font=FONTS['small_bold'])

    # Botón genérico
    s.configure('TButton',
                background=C['button_bg'], foreground=C['fg'],
                borderwidth=0, focuscolor='none',
                font=FONTS['body'], padding=(12, 6))
    s.map('TButton',
          background=[('active', C['button_active']), ('pressed', C['button_active'])])

    # Botón "+ Add Bot"
    s.configure('Add.TButton',
                background=C['accent'], foreground='#000000',
                font=('Segoe UI', 13, 'bold'), borderwidth=0, padding=(10, 4))
    s.map('Add.TButton', background=[('active', C['accent_dim'])])

    # Botones Run / Stop
    s.configure('Start.TButton',
                background=C['accent_green'], foreground='#000000',
                font=FONTS['small_bold'], borderwidth=0, padding=(10, 5))
    s.map('Start.TButton', background=[('active', C['accent_green_hover'])])

    s.configure('Stop.TButton',
                background=C['accent_red'], foreground='#ffffff',
                font=FONTS['small_bold'], borderwidth=0, padding=(10, 5))
    s.map('Stop.TButton', background=[('active', C['accent_red_hover'])])

    # Notebook
    s.configure('TNotebook', background=C['bg'], borderwidth=0, tabmargins=0)
    s.configure('TNotebook.Tab',
                background=C['bg'], foreground=C['fg_dim'],
                padding=[18, 9], font=FONTS['tab'], borderwidth=0)
    s.map('TNotebook.Tab',
          background=[('selected', C['card_bg'])],
          foreground=[('selected', C['accent'])],
          font=[('selected', FONTS['tab_sel'])])

    # Treeview
    s.configure('Treeview',
                background=C['entry_bg'], foreground=C['fg'],
                fieldbackground=C['entry_bg'], borderwidth=0,
                rowheight=26, font=FONTS['mono'])
    s.configure('Treeview.Heading',
                background=C['button_bg'], foreground=C['fg_dim'],
                font=FONTS['caps'], borderwidth=0, relief='flat')
    s.map('Treeview',
          background=[('selected', C['button_active'])],
          foreground=[('selected', C['accent'])])

    # Combobox y separador
    s.configure('TCombobox',
                fieldbackground=C['entry_bg'], background=C['button_bg'],
                foreground=C['fg'], borderwidth=0)
    s.configure('TSeparator', background=C['border'])

    return C
