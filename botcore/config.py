"""
core/config.py
──────────────
Carga, guarda y provee acceso a config.json y languages.json.

Los archivos se guardan en la carpeta de datos del usuario:
  Windows : %APPDATA%\DiscordBotManager
  macOS   : ~/Library/Application Support/DiscordBotManager
  Linux   : ~/.config/DiscordBotManager

Esto evita errores de permisos cuando la app está instalada en Program Files.
"""

import json
import os
import sys
import shutil

APP_VERSION = 'v1.1'

DEFAULT_CONFIG = {
    "language": "en",
    "theme":    "dark",
    "bots":     []
}


def _get_data_dir() -> str:
    """Carpeta de datos del usuario, creada si no existe."""
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))

    data_dir = os.path.join(base, 'DiscordBotManager')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _get_bundled_languages() -> str:
    """Ruta al languages.json original (junto al .exe o en el repo)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'languages.json')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'languages.json')


DATA_DIR    = _get_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
LANG_FILE   = os.path.join(DATA_DIR, 'languages.json')


def load_languages() -> dict:
    """
    Devuelve el dict de idiomas.
    Si no existe en APPDATA, copia el languages.json del bundle.
    """
    if not os.path.exists(LANG_FILE):
        bundled = _get_bundled_languages()
        if os.path.exists(bundled):
            shutil.copy2(bundled, LANG_FILE)
        else:
            minimal = {"en": {"app_title": "Discord Bot Manager"}}
            with open(LANG_FILE, 'w', encoding='utf-8') as f:
                json.dump(minimal, f, indent=2, ensure_ascii=False)

    with open(LANG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_config() -> dict:
    """Devuelve la config completa, rellenando claves que falten con defaults."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for key, val in DEFAULT_CONFIG.items():
            cfg.setdefault(key, val)
        return cfg
    except FileNotFoundError:
        save_config(DEFAULT_CONFIG.copy(), {})
        return DEFAULT_CONFIG.copy()


def save_config(config: dict, bots: dict) -> None:
    """Serializa y guarda config.json en la carpeta de datos del usuario."""
    config['bots'] = [
        {
            'name':      name,
            'file_path': data['file_path'],
            'bot_type':  data.get('bot_type', 'python'),
        }
        for name, data in bots.items()
    ]
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def translate(languages: dict, language: str, key: str, **kwargs) -> str:
    """Devuelve la traducción para key en language, con formato opcional."""
    text = languages.get(language, {}).get(key, key)
    return text.format(**kwargs) if kwargs else text