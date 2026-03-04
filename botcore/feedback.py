"""
core/feedback.py
────────────────
Envía feedback anónimo a un canal de Discord via webhook.

El webhook URL se lee desde la variable de entorno FEEDBACK_WEBHOOK
al momento de compilar con PyInstaller — nunca aparece en el código fuente.

Para compilar:
  Windows:  $env:FEEDBACK_WEBHOOK="https://discord.com/api/webhooks/xxx/yyy"
  Linux/mac: export FEEDBACK_WEBHOOK="https://discord.com/api/webhooks/xxx/yyy"
  Luego:    pyinstaller --onefile --windowed --icon=icon.ico --name BotManager main.py
"""

import os
import json
import urllib.request
import urllib.error
import threading
from datetime import datetime

# Se embebe en el .exe al compilar — nunca visible en el repo
WEBHOOK_URL = os.environ.get('FEEDBACK_WEBHOOK', '')

# Tipos de feedback y sus colores en Discord
FEEDBACK_COLORS = {
    'bug':         0xff4d6a,   # rojo
    'improvement': 0x00d4ff,   # cyan
    'rating':      0x00e5a0,   # verde
}

FEEDBACK_LABELS = {
    'bug':         '🐛 Bug Report',
    'improvement': '💡 Suggestion',
    'rating':      '⭐ Rating',
}

STAR_DISPLAY = {1: '★☆☆☆☆', 2: '★★☆☆☆', 3: '★★★☆☆', 4: '★★★★☆', 5: '★★★★★'}


def _build_embed(feedback_type: str, text: str,
                 rating: int | None, app_version: str) -> dict:
    """Construye el embed de Discord."""
    fields = []

    if text.strip():
        fields.append({
            'name':   'Message',
            'value':  text.strip()[:1000],  # límite de Discord
            'inline': False,
        })

    if rating is not None:
        fields.append({
            'name':   'Rating',
            'value':  f"{STAR_DISPLAY.get(rating, '?')}  ({rating}/5)",
            'inline': True,
        })

    fields.append({
        'name':   'App Version',
        'value':  app_version,
        'inline': True,
    })

    fields.append({
        'name':   'Sent at',
        'value':  datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'inline': True,
    })

    return {
        'embeds': [{
            'title':  FEEDBACK_LABELS.get(feedback_type, 'Feedback'),
            'color':  FEEDBACK_COLORS.get(feedback_type, 0x64748b),
            'fields': fields,
            'footer': {'text': 'Discord Bot Manager — Anonymous Feedback'},
        }]
    }


def send_feedback(feedback_type: str, text: str,
                  rating: int | None, app_version: str,
                  on_success=None, on_error=None):
    """
    Envía el feedback en un hilo daemon para no bloquear la UI.

    - on_success()     : callback si se envió correctamente
    - on_error(msg)    : callback si falló
    """
    if not WEBHOOK_URL:
        if on_error:
            on_error("Feedback is not configured in this build.")
        return

    def _send():
        try:
            payload = json.dumps(
                _build_embed(feedback_type, text, rating, app_version)
            ).encode('utf-8')

            req = urllib.request.Request(
                WEBHOOK_URL,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent':   'DiscordBotManager-Feedback',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 204):
                    if on_success:
                        on_success()
                else:
                    if on_error:
                        on_error(f"HTTP {resp.status}")

        except urllib.error.URLError:
            if on_error:
                on_error("Could not reach Discord. Check your internet connection.")
        except Exception as exc:
            if on_error:
                on_error(str(exc))

    threading.Thread(target=_send, daemon=True).start()