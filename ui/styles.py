"""
styles.py - Configuración de Paleta de Colores Pastel y Estilos Visuales
Sistema de Control de Incidencias Ciudadanas
Tema: Soft Sand & Soft Peachy Delight

Configuración declarativa de estilos ttkbootstrap para garantizar:
- Fondo general en tonos Soft Sand (#FAF0E6 / #F5F5DC).
- Acentos en Soft Peachy Delight (#FFDAB9 / #FADADD) y Warm Neutrals.
- Contraste visual accesible con texto en tonos oscuros suaves (#2D2A26).
"""

import tkinter as tk
import ttkbootstrap as tb


# Paleta de Colores Pastel
COLOR_FONDO_GENERAL = "#FAF0E6"        # Soft Sand / Linen
COLOR_FONDO_TARJETA = "#FFFDF9"        # Warm Ivory
COLOR_MELOCOTON_DELIGHT = "#FADADD"    # Soft Peachy Delight
COLOR_MELOCOTON_ACTIVO = "#F3BFC4"     # Hover Peachy
COLOR_MELOCOTON_CALIDO = "#FFDAB9"     # Warm Peach Puff
COLOR_MENTA_PASTEL = "#DDF0DE"         # Soft Mint (Acción Voto)
COLOR_TEXTO_OSCURO = "#2D2A26"         # Soft Charcoal (Alto contraste)
COLOR_TEXTO_SECUNDARIO = "#68615A"     # Warm Muted Gray
COLOR_BORDE_SUAVE = "#E2D8CC"          # Neutral Border
COLOR_TABLA_FILA = "#FFFFFF"           # Blanco nítido para datos


def aplicar_estilos_pastel(style: tb.Style, root: tk.Tk) -> None:
    """
    Aplica y registra la paleta pastel sobre el motor de estilos de ttkbootstrap.
    """
    # 1. Configuración de fondo del root y contendedores
    root.configure(bg=COLOR_FONDO_GENERAL)

    # 2. Configuración de Frames y Labelframes
    style.configure(
        "Pastel.TFrame",
        background=COLOR_FONDO_GENERAL
    )
    style.configure(
        "PastelCard.TFrame",
        background=COLOR_FONDO_TARJETA,
        relief="flat"
    )

    style.configure(
        "Pastel.TLabelframe",
        background=COLOR_FONDO_GENERAL,
        bordercolor=COLOR_BORDE_SUAVE,
        relief="groove"
    )
    style.configure(
        "Pastel.TLabelframe.Label",
        background=COLOR_FONDO_GENERAL,
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 10, "bold")
    )

    # 3. Etiquetas (Labels)
    style.configure(
        "Pastel.TLabel",
        background=COLOR_FONDO_GENERAL,
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 9)
    )
    style.configure(
        "PastelHeader.TLabel",
        background=COLOR_MELOCOTON_DELIGHT,
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 14, "bold"),
        padding=(15, 10)
    )
    style.configure(
        "PastelMuted.TLabel",
        background=COLOR_FONDO_GENERAL,
        foreground=COLOR_TEXTO_SECUNDARIO,
        font=("Segoe UI", 8, "italic")
    )
    style.configure(
        "PastelBadge.TLabel",
        background=COLOR_MELOCOTON_CALIDO,
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 4)
    )

    # 4. Botones Pastel Personalizados
    # Botón Principal Peachy
    style.configure(
        "PastelPeach.TButton",
        background=COLOR_MELOCOTON_DELIGHT,
        foreground=COLOR_TEXTO_OSCURO,
        bordercolor=COLOR_BORDE_SUAVE,
        font=("Segoe UI", 9, "bold"),
        padding=(12, 6)
    )
    style.map(
        "PastelPeach.TButton",
        background=[("active", COLOR_MELOCOTON_ACTIVO), ("pressed", COLOR_MELOCOTON_CALIDO)],
        foreground=[("active", COLOR_TEXTO_OSCURO)]
    )

    # Botón de Éxito / Voto Mint
    style.configure(
        "PastelMint.TButton",
        background=COLOR_MENTA_PASTEL,
        foreground=COLOR_TEXTO_OSCURO,
        bordercolor=COLOR_BORDE_SUAVE,
        font=("Segoe UI", 9, "bold"),
        padding=(12, 6)
    )
    style.map(
        "PastelMint.TButton",
        background=[("active", "#C8E5CA"), ("pressed", "#B5DDB7")],
        foreground=[("active", COLOR_TEXTO_OSCURO)]
    )

    # Botón Neutro Suave
    style.configure(
        "PastelNeutral.TButton",
        background="#EFECE5",
        foreground=COLOR_TEXTO_OSCURO,
        bordercolor=COLOR_BORDE_SUAVE,
        font=("Segoe UI", 9),
        padding=(10, 5)
    )

    # 5. Notebook (Pestañas) Pastel
    style.configure(
        "Pastel.TNotebook",
        background=COLOR_FONDO_GENERAL,
        tabmargins=[10, 5, 2, 0]
    )
    style.configure(
        "Pastel.TNotebook.Tab",
        background="#EFE6DC",
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 9, "bold"),
        padding=(15, 6)
    )
    style.map(
        "Pastel.TNotebook.Tab",
        background=[("selected", COLOR_MELOCOTON_DELIGHT), ("active", COLOR_MELOCOTON_CALIDO)],
        foreground=[("selected", COLOR_TEXTO_OSCURO)]
    )

    # 6. Tabla (Treeview)
    style.configure(
        "Pastel.Treeview",
        background=COLOR_TABLA_FILA,
        foreground=COLOR_TEXTO_OSCURO,
        fieldbackground=COLOR_TABLA_FILA,
        font=("Segoe UI", 9),
        rowheight=26
    )
    style.configure(
        "Pastel.Treeview.Heading",
        background="#F2E6DA",
        foreground=COLOR_TEXTO_OSCURO,
        font=("Segoe UI", 9, "bold")
    )
    style.map(
        "Pastel.Treeview",
        background=[("selected", COLOR_MELOCOTON_CALIDO)],
        foreground=[("selected", COLOR_TEXTO_OSCURO)]
    )
