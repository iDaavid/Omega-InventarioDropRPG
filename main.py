"""
main.py — Punto de entrada del simulador Omega RPG.

Toda la lógica de interfaz se encuentra en modulos/interfaz.py.
Este archivo solo arranca la aplicación Flet.
"""

import flet as ft
from modulos.interfaz import main

if __name__ == "__main__":
    ft.run(main)