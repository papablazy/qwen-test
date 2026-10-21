"""Paletas de colores claro y oscuro para la aplicación."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Paleta:
    nombre: str
    fondo: str          # color general de la ventana
    panel: str          # listas / barras laterales
    tarjeta: str        # elementos de lista seleccionados
    cabecera: str       # barra superior
    texto: str          # texto principal
    texto_suave: str    # texto secundario
    entrada_fondo: str  # campos de escritura
    borde: str          # separadores
    acento: str         # botones principales
    acento_texto: str   # texto sobre el acento
    peligro: str        # acciones destructivas


CLARO = Paleta(
    nombre="Claro",
    fondo="#f6f7f9",
    panel="#eceef1",
    tarjeta="#dfe7f5",
    cabecera="#ffffff",
    texto="#1f2430",
    texto_suave="#6b7280",
    entrada_fondo="#ffffff",
    borde="#d5d9e0",
    acento="#2f6fed",
    acento_texto="#ffffff",
    peligro="#d64545",
)

OSCURO = Paleta(
    nombre="Oscuro",
    fondo="#15171c",
    panel="#1d2026",
    tarjeta="#2b3650",
    cabecera="#101216",
    texto="#e8eaf0",
    texto_suave="#9aa1ad",
    entrada_fondo="#1d2026",
    borde="#2c3038",
    acento="#4f83f7",
    acento_texto="#ffffff",
    peligro="#e05252",
)

PALETAS = {"claro": CLARO, "oscuro": OSCURO}
