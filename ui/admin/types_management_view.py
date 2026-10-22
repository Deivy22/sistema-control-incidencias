"""
types_management_view.py - Apartado Exclusivo del Administrador para Tipos de Incidente
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Peachy Delight)

Este módulo implementa el panel exclusivo para administradores que permite:
1. Agregar nuevos tipos de incidente dinámicos cuando se presenten situaciones no contempladas.
2. Consultar el catálogo activo de tipos y su departamento gubernamental clasificado.
3. Restricción estricta de acceso: Solo usuarios con rol 'Admin' pueden acceder y modificar el catálogo.
"""

import tkinter as tk
from typing import Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, VERTICAL, W, X, Y
from ttkbootstrap.dialogs import Messagebox

from core.engine import clasificar_incidente
from ui.state_manager import StateManager


class IncidentTypesView(tb.Frame):
    """
    Vista administrativa exclusiva para la gestión y alta de nuevos tipos de incidente.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager

        self.var_nombre_tipo = tk.StringVar()
        self.var_mensaje = tk.StringVar()
        self.var_conteo_tipos = tk.StringVar(value="Tipos Registrados: 0")
        self.var_preview_depto = tk.StringVar(value="Dirección General de Atención Ciudadana")

        self._construir_interfaz()
        self.refrescar_tabla()

    def _construir_interfaz(self) -> None:
        """Construye la interfaz gráfica de dos columnas (Formulario de alta + Catálogo activo)."""
        # 1. Banner superior explicativo
        banner = tb.Labelframe(
            self,
            text="🏷️ Catálogo Dinámico de Tipos de Incidente (Exclusivo Administrador)",
            padding=12,
            style="Pastel.TLabelframe"
        )
        banner.pack(fill=X, padx=15, pady=(10, 10))

        tb.Label(
            banner,
            text="Sección exclusiva para la cuenta de Administrador. Permite incorporar nuevas categorías de incidencias "
                 "urbanas que no fueron contempladas originalmente, actualizando en caliente los formularios del sistema.",
            style="PastelMuted.TLabel"
        ).pack(anchor=W)

        # 2. Contenedor de paneles (Izquierda: Formulario | Derecha: Tabla de catálogo)
        paneles = tb.Frame(self, style="Pastel.TFrame")
        paneles.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))

        # Panel Izquierdo: Formulario de Registro
        panel_form = tb.Labelframe(
            paneles,
            text="📝 Agregar Nuevo Tipo de Incidente",
            padding=20,
            style="Pastel.TLabelframe",
            width=420
        )
        panel_form.pack(side=LEFT, fill=BOTH, padx=(0, 10))
        panel_form.pack_propagate(False)

        tb.Label(
            panel_form,
            text="Nombre del Tipo de Incidente:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        self.entry_tipo = tb.Entry(
            panel_form,
            textvariable=self.var_nombre_tipo,
            font=("Segoe UI", 9)
        )
        self.entry_tipo.pack(fill=X, pady=(0, 10))
        self.entry_tipo.bind("<KeyRelease>", self._on_texto_cambiado)
        self.entry_tipo.bind("<Return>", lambda event: self._on_agregar_tipo())

        # Vista previa del departamento derivado por el motor funcional
        tb.Label(
            panel_form,
            text="Departamento Responsable Asignado:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        lbl_depto = tb.Label(
            panel_form,
            textvariable=self.var_preview_depto,
            font=("Segoe UI", 9, "italic"),
            wraplength=360,
            style="PastelBadge.TLabel"
        )
        lbl_depto.pack(fill=X, pady=(0, 15))

        tb.Label(
            panel_form,
            text="ℹ️ Los nuevos tipos no contemplados en el clasificador base son asignados "
                 "a la Dirección General de Atención Ciudadana para su canalización formal.",
            style="PastelMuted.TLabel",
            wraplength=360
        ).pack(fill=X, pady=(0, 15))

        # Label de feedback
        self.lbl_feedback = tb.Label(
            panel_form,
            textvariable=self.var_mensaje,
            wraplength=360,
            font=("Segoe UI", 8, "bold"),
            style="Pastel.TLabel"
        )
        self.lbl_feedback.pack(fill=X, pady=(0, 10))

        # Botones de Acción
        btn_crear = tb.Button(
            panel_form,
            text="➕ Agregar al Catálogo",
            style="PastelPeach.TButton",
            command=self._on_agregar_tipo
        )
        btn_crear.pack(fill=X, ipady=3, pady=(0, 6))

        btn_limpiar = tb.Button(
            panel_form,
            text="🧹 Limpiar",
            style="PastelNeutral.TButton",
            command=self._limpiar_formulario
        )
        btn_limpiar.pack(fill=X, ipady=2)

        # Panel Derecho: Catálogo de Tipos Habilitados
        panel_tabla = tb.Labelframe(
            paneles,
            text="📋 Tipos de Incidente Habilitados en el Sistema",
            padding=15,
            style="Pastel.TLabelframe"
        )
        panel_tabla.pack(side=RIGHT, fill=BOTH, expand=True)

        # Barra superior con métricas
        barra_info = tb.Frame(panel_tabla, style="Pastel.TFrame")
        barra_info.pack(fill=X, pady=(0, 8))

        tb.Label(
            barra_info,
            textvariable=self.var_conteo_tipos,
            style="PastelBadge.TLabel"
        ).pack(side=LEFT)

        tb.Button(
            barra_info,
            text="🔄 Actualizar",
            style="PastelNeutral.TButton",
            command=self.refrescar_tabla
        ).pack(side=RIGHT)

        # Treeview de Tipos
        frame_tree = tb.Frame(panel_tabla, style="Pastel.TFrame")
        frame_tree.pack(fill=BOTH, expand=True)

        columnas = ("num", "tipo", "departamento")
        self.tree_tipos = tb.Treeview(
            frame_tree,
            columns=columnas,
            show="headings",
            style="Pastel.Treeview",
            selectmode="browse"
        )

        self.tree_tipos.heading("num", text="#", anchor=W)
        self.tree_tipos.heading("tipo", text="Tipo de Incidente", anchor=W)
        self.tree_tipos.heading("departamento", text="Departamento Gubernamental Asignado", anchor=W)

        self.tree_tipos.column("num", width=45, minwidth=35, stretch=False)
        self.tree_tipos.column("tipo", width=190, minwidth=140)
        self.tree_tipos.column("departamento", width=300, minwidth=200)

        scroll_y = tb.Scrollbar(frame_tree, orient=VERTICAL, command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scroll_y.set)

        self.tree_tipos.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)

    def _on_texto_cambiado(self, event=None) -> None:
        """Actualiza la vista previa del departamento en base a pattern matching."""
        texto = self.var_nombre_tipo.get().strip()
        if texto:
            _, depto = clasificar_incidente(texto)
            self.var_preview_depto.set(depto)
        else:
            self.var_preview_depto.set("Dirección General de Atención Ciudadana")

    def _on_agregar_tipo(self) -> None:
        """Procesa el alta del nuevo tipo delegando en el StateManager."""
        if not self.state_manager.puede_administrar_usuarios:
            Messagebox.show_warning(
                "Solo los administradores tienen privilegios para agregar tipos de incidente.",
                title="Acceso Denegado"
            )
            return

        tipo = self.var_nombre_tipo.get().strip()
        exito, mensaje = self.state_manager.agregar_tipo_incidente(tipo)

        if exito:
            self.lbl_feedback.configure(foreground="#2E7D32")
            self.var_mensaje.set(f"✅ {mensaje}")
            Messagebox.show_info(mensaje, title="Tipo de Incidente Agregado")
            self._limpiar_formulario()
            self.refrescar_tabla()
        else:
            self.lbl_feedback.configure(foreground="#D9534F")
            self.var_mensaje.set(f"❌ {mensaje}")

    def _limpiar_formulario(self) -> None:
        self.var_nombre_tipo.set("")
        self.var_preview_depto.set("Dirección General de Atención Ciudadana")

    def refrescar_tabla(self) -> None:
        """Recarga la lista de tipos desde el StateManager."""
        for item in self.tree_tipos.get_children():
            self.tree_tipos.delete(item)

        tipos = self.state_manager.obtener_tipos_incidente()
        for idx, t in enumerate(tipos, start=1):
            _, depto = clasificar_incidente(t)
            self.tree_tipos.insert(
                "",
                tk.END,
                values=(idx, t, depto)
            )

        self.var_conteo_tipos.set(f"Tipos Registrados: {len(tipos)}")

