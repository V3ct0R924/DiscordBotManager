"""
botcore/updater.py
──────────────────
Consulta la GitHub API para ver si hay una nueva release disponible.
Soporta tanto releases estables como pre-releases, con comportamiento distinto:

- Release estable  → banner simple "nueva versión disponible"
- Pre-release      → banner con advertencia de errores + opción "no mostrar de nuevo"

La preferencia "no mostrar" se guarda en config.json por tag específico,
así que ignorar la v1.1-beta no afecta futuros avisos de v1.2-beta o v2.0.
"""

import threading
import urllib.request
import urllib.error
import json

GITHUB_REPO = "V3ct0R924/DiscordBotManager"
API_URL     = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases"


def _parse_version(tag: str) -> tuple:
    clean = tag.lstrip('v').split('-')[0]
    try:
        return tuple(int(x) for x in clean.split('.'))
    except ValueError:
        return (0,)


def check_for_updates(current_version: str, skipped_tags: list,
                      on_stable, on_prerelease, on_error=None):
    def _check():
        try:
            req = urllib.request.Request(
                API_URL,
                headers={'User-Agent': 'DiscordBotManager-Updater'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                releases = json.loads(resp.read().decode())

            if not releases:
                return

            current_tuple = _parse_version(current_version)

            # Buscar release estable mas nueva
            best_stable = None
            for r in releases:
                if r.get('prerelease') or r.get('draft'):
                    continue
                tag = r.get('tag_name', '')
                if _parse_version(tag) > current_tuple:
                    if best_stable is None or _parse_version(tag) > _parse_version(best_stable['tag_name']):
                        best_stable = r

            if best_stable:
                on_stable(best_stable['tag_name'], best_stable.get('html_url', RELEASE_URL))
                return

            # Buscar pre-release mas nueva (no ignorada)
            best_pre = None
            for r in releases:
                if not r.get('prerelease') or r.get('draft'):
                    continue
                tag = r.get('tag_name', '')
                if _parse_version(tag) <= current_tuple:
                    continue
                if tag in skipped_tags:
                    continue
                if best_pre is None or _parse_version(tag) > _parse_version(best_pre['tag_name']):
                    best_pre = r

            if best_pre:
                on_prerelease(best_pre['tag_name'], best_pre.get('html_url', RELEASE_URL))

        except urllib.error.URLError:
            if on_error:
                on_error("Could not reach GitHub to check for updates.")
        except Exception as exc:
            if on_error:
                on_error(f"Update check failed: {exc}")

    threading.Thread(target=_check, daemon=True).start()