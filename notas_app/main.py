#!/usr/bin/env python3
"""Punto de entrada de NotasPro: editor de notas para escritorio.

Ejecutar con:  python main.py   (requiere Python 3.10+ con tkinter)
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import ejecutar  # noqa: E402


def main():
    raiz = tk.Tk()
    try:
        from ctypes import windll  # solo Windows: icono nítido en alta resolución
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    ejecutar(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
