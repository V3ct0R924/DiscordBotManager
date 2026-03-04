"""
main.py
───────
Entry point de la aplicación. Solo arranca la ventana y cede el control.
Para convertir a .exe con PyInstaller:
    pyinstaller --onefile --windowed --icon=icon.ico main.py
"""

import tkinter as tk
from app import BotManager


if __name__ == "__main__":
    root = tk.Tk()
    app  = BotManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.iconbitmap('icon.ico')
    root.mainloop()
