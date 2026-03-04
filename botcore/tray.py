"""
core/tray.py
────────────
Maneja el icono en el system tray (área de notificaciones de Windows).

Comportamiento:
- Botón en el header → oculta la ventana y aparece en el tray
- Click izquierdo en tray → toggle mostrar/ocultar ventana
- Click derecho en tray → menú con Mostrar/Ocultar, Detener todos los bots, Salir
- X del sistema → cierra la app normalmente (comportamiento default de tkinter)

Requiere: pip install pystray pillow
"""

import threading

try:
    import pystray
    from pystray import MenuItem as Item, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


def create_tray(icon_path: str,
                on_toggle,
                on_stop_all,
                on_quit) -> object | None:
    """
    Crea y arranca el icono del tray en un hilo daemon.

    Parámetros:
    - icon_path  : ruta al archivo .ico
    - on_toggle  : callback para mostrar/ocultar la ventana
    - on_stop_all: callback para detener todos los bots
    - on_quit    : callback para cerrar la app completamente

    Devuelve el objeto tray (para poder llamar tray.stop() al salir),
    o None si pystray no está instalado.
    """
    if not PYSTRAY_AVAILABLE:
        return None

    try:
        from PIL import Image
        icon_image = Image.open(icon_path)
    except Exception:
        # Si no encuentra el .ico, usa un cuadrado azul como fallback
        from PIL import Image, ImageDraw
        icon_image = Image.new('RGBA', (64, 64), '#151820')
        draw = ImageDraw.Draw(icon_image)
        draw.ellipse([8, 8, 56, 56], fill='#00d4ff')

    menu = Menu(
        Item('Show / Hide',      lambda icon, item: on_toggle(),    default=True),
        Menu.SEPARATOR,
        Item('Stop all bots',    lambda icon, item: on_stop_all()),
        Menu.SEPARATOR,
        Item('Quit',             lambda icon, item: on_quit()),
    )

    tray = pystray.Icon(
        name='BotManager',
        icon=icon_image,
        title='Bot Manager',
        menu=menu,
    )

    # Click izquierdo → toggle (pystray llama al item default)
    threading.Thread(target=tray.run, daemon=True).start()
    return tray
