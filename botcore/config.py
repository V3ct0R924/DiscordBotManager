"""
core/config.py
──────────────
Carga, guarda y provee acceso a config.json y languages.json.
Si querés cambiar dónde se guardan los archivos, solo tocás CONFIG_FILE y LANG_FILE.
"""

import json
import os

CONFIG_FILE = 'config.json'
LANG_FILE   = 'languages.json'

APP_VERSION = 'v1.1'

DEFAULT_CONFIG = {
    "language": "en",
    "theme":    "dark",
    "bots":     []
}


def load_languages() -> dict:
    """Devuelve el dict de idiomas. Si no existe el archivo, crea uno mínimo."""
    try:
        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        minimal = {"en": {"app_title": "Discord Bot Manager"}}
        with open(LANG_FILE, 'w', encoding='utf-8') as f:
            json.dump(minimal, f, indent=2, ensure_ascii=False)
        return minimal


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
    """
    Serializa y guarda config.json.
    Recibe el dict de config y el dict de bots activos para actualizar la lista.
    """
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
    """Devuelve la traducción para `key` en `language`, con formato opcional."""
    text = languages.get(language, {}).get(key, key)
    return text.format(**kwargs) if kwargs else text
