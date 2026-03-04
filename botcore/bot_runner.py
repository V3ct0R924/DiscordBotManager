"""
core/bot_runner.py
──────────────────
Todo lo que tiene que ver con arrancar, detener y monitorear procesos de bots.
No importa nada de tkinter — solo subprocess y threading.
Si en el futuro querés agregar soporte para otro runtime (Deno, Bun, etc.),
solo agregás una entrada en RUNTIMES.
"""

import subprocess
import threading
import os

# ── Runtimes soportados ───────────────────────────────────────────────────────
# Cada entrada define el comando y si necesita output sin buffer.
RUNTIMES = {
    'python': {
        'cmd':  lambda path: ['python', '-u', path],
        'env':  lambda base: {**base, 'PYTHONUNBUFFERED': '1'},
    },
    'node': {
        'cmd':  lambda path: ['node', path],
        'env':  lambda base: base,
    },
}

def detect_type(file_path: str) -> str:
    """Detecta el tipo de bot por extensión del archivo."""
    return 'node' if file_path.endswith('.js') else 'python'


def start_bot(file_path: str, bot_type: str) -> subprocess.Popen:
    """
    Arranca el proceso del bot y devuelve el objeto Popen.
    Lanza FileNotFoundError si el runtime no está instalado.
    """
    runtime = RUNTIMES.get(bot_type, RUNTIMES['python'])
    env     = runtime['env'](os.environ.copy())
    cmd     = runtime['cmd'](file_path)

    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        creationflags=flags,
    )


def stop_bot(process: subprocess.Popen, timeout: int = 5) -> None:
    """Termina el proceso limpiamente. No lanza excepciones si ya terminó."""
    try:
        process.terminate()
        process.wait(timeout=timeout)
    except Exception:
        pass


def monitor_output(bot_name: str, process: subprocess.Popen,
                   on_line,        # callback(bot_name, line)
                   on_cmd,         # callback(bot_name, user, channel, command)
                   on_exit):       # callback(bot_name)
    """
    Corre en un hilo daemon. Lee stdout línea a línea y dispara callbacks.
    El formato de log de comandos esperado es:  [CMD]|user|#channel|command
    """
    def _run():
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                on_line(bot_name, line)

                if line.startswith('[CMD]'):
                    parts = line.split('|')
                    if len(parts) >= 4:
                        on_cmd(bot_name, parts[1], parts[2], parts[3])

            if process.poll() is not None:
                on_exit(bot_name)

        except Exception as exc:
            on_line(bot_name, f"[monitor error] {exc}")

    threading.Thread(target=_run, daemon=True).start()
