"""
list_view.py - Tabla de Consulta de Incidencias Ciudadanas
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel y Treeview Reactivo

Características:
1. Evento de doble clic (`<Double-1>`) y botón "✏️ Editar Seleccionada" para cargar la fila en el formulario de modificación.
2. Botón "👍 Adherir Voto" con transformación inmutable.
3. Filtrado por sector (Closure + filter/map) y cálculo de prioridad total acumulada (reduce).
4. La información visualizada está estrictamente filtrada por permisos (`filtrar_por_permisos`).
"""

import tkinter as tk
from typing import Callable, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, HORIZONTAL, LEFT, RIGHT, VERTICAL, W, X, Y
from ttkbootstrap.dialogs import Messagebox

from core.models import Incidente
from ui.state_manager import StateManager


class IncidentesListView(tb.Frame):
    """
    Vista tabular de consulta de incidentes con soporte para selección y edición inmutable.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager,
        on_solicitar_edicion: Optional[Callable[[Incidente], None]] = None
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager
        self.on_solicitar_edicion = on_solicitar_edicion

        self.var_filtro_sector = tk.StringVar()
        self.var_filtro_activo_texto = tk.StringVar(value="Filtro: Todos")
        self.var_prioridad_total_texto = tk.StringVar(value="Prioridad Acumulada: 0")
        self.var_conteo_incidentes_texto = tk.StringVar(value="Total Visibles: 0")

        self._construir_interfaz()
        self.refrescar_tabla()

    def _construir_interfaz(self) -> None:
        """Construye la barra de herramientas, la tabla Treeview y la barra de acciones."""
        # 1. Barra de Herramientas y Filtros
        toolbar = tb.Labelframe(
            self,
            text="🔍 Filtros por Sector y Resúmenes",
            padding=10,
            style="Pastel.TLabelframe"
        )
        toolbar.pack(fill=X, pady=(0, 10))

        tb.Label(
            toolbar,
            text="Sector:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(side=LEFT, padx=(0, 5))

        entry_filtro = tb.Entry(
            toolbar,
            textvariable=self.var_filtro_sector,
            width=20,
            font=("Segoe UI", 9)
        )
        entry_filtro.pack(side=LEFT, padx=(0, 8))

        tb.Button(
            toolbar,
            text="Filtrar Sector",
            style="PastelPeach.TButton",
            command=self._on_aplicar_filtro
        ).pack(side=LEFT, padx=3)

        tb.Button(
            toolbar,
            text="Ver Todos",
            style="PastelNeutral.TButton",
            command=self._on_limpiar_filtro
        ).pack(side=LEFT, padx=3)

        tb.Button(
            toolbar,
            text="📑 Ver Resúmenes",
            style="PastelNeutral.TButton",
            command=self._on_mostrar_resumenes_map
        ).pack(side=LEFT, padx=8)

        # Badges métricos a la derecha
        tb.Label(
            toolbar,
            textvariable=self.var_prioridad_total_texto,
            style="PastelBadge.TLabel"
        ).pack(side=RIGHT, padx=4)

        tb.Label(
            toolbar,
            textvariable=self.var_filtro_activo_texto,
            style="PastelBadge.TLabel"
        ).pack(side=RIGHT, padx=4)

        # 2. Tabla Treeview
        frame_tabla = tb.Frame(self, style="Pastel.TFrame")
        frame_tabla.pack(fill=BOTH, expand=True)

        columnas = ("id", "sector", "tipo", "prioridad", "estado", "departamento", "descripcion")
        self.tree = tb.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            style="Pastel.Treeview",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID", anchor=W)
        self.tree.heading("sector", text="Sector", anchor=W)
        self.tree.heading("tipo", text="Tipo", anchor=W)
        self.tree.heading("prioridad", text="Prioridad", anchor=W)
        self.tree.heading("estado", text="Estado", anchor=W)
        self.tree.heading("departamento", text="Dpto. Responsable", anchor=W)
        self.tree.heading("descripcion", text="Descripción", anchor=W)

        self.tree.column("id", width=45, minwidth=40, stretch=False)
        self.tree.column("sector", width=120, minwidth=100)
        self.tree.column("tipo", width=110, minwidth=90)
        self.tree.column("prioridad", width=75, minwidth=60, stretch=False)
        self.tree.column("estado", width=95, minwidth=80, stretch=False)
        self.tree.column("departamento", width=220, minwidth=180)
        self.tree.column("descripcion", width=360, minwidth=200)

        scroll_y = tb.Scrollbar(frame_tabla, orient=VERTICAL, command=self.tree.yview)
        scroll_x = tb.Scrollbar(frame_tabla, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_x.pack(side=tk.BOTTOM, fill=X)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)

        # EVENTO DOBLE CLIC SOBRE LA FILA
        self.tree.bind("<Double-1>", self._on_doble_clic_fila)

        # 3. Barra de Acciones Inferiores
        barra_acciones = tb.Frame(self, padding=(0, 10), style="Pastel.TFrame")
        barra_acciones.pack(fill=X)

        self.btn_voto = tb.Button(
            barra_acciones,
            text="👍 Adherir Voto (+1 Prioridad)",
            style="PastelMint.TButton",
            command=self._on_adherir_voto
        )
        self.btn_voto.pack(side=LEFT, padx=(0, 8))

        self.btn_editar = tb.Button(
            barra_acciones,
            text="✏️ Editar Seleccionada",
            style="PastelPeach.TButton",
            command=self._on_click_editar_seleccionada
        )
        self.btn_editar.pack(side=LEFT, padx=(0, 8))

        # Botón Borrar: Rojo ('danger'), solo visible y habilitado para Admin
        self.btn_borrar = tb.Button(
            barra_acciones,
            text="🗑️ Borrar Seleccionada",
            bootstyle="danger",
            command=self._on_click_borrar_seleccionada
        )

        tb.Label(
            barra_acciones,
            text="💡 Tip: Seleccione una fila para editarla, gestionarla o consultar sus detalles.",
            style="PastelMuted.TLabel"
        ).pack(side=RIGHT)

    # ========================================================================
    # EVENTOS DE SELECCIÓN Y EDICIÓN
    # ========================================================================

    def _obtener_incidente_seleccionado(self) -> Optional[Incidente]:
        """Extrae el objeto Incidente correspondiente a la fila seleccionada."""
        seleccion = self.tree.selection()
        if not seleccion:
            return None
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        if not valores:
            return None
        incidente_id = int(valores[0])
        return self.state_manager.obtener_incidente_por_id(incidente_id)

    def _on_doble_clic_fila(self, event=None) -> None:
        """Callback del evento doble clic sobre la fila de la tabla."""
        incidente = self._obtener_incidente_seleccionado()
        if incidente and self.on_solicitar_edicion:
            self.on_solicitar_edicion(incidente)

    def _on_click_editar_seleccionada(self) -> None:
        """Callback del botón 'Editar Seleccionada'."""
        incidente = self._obtener_incidente_seleccionado()
        if not incidente:
            Messagebox.show_warning(
                "Seleccione un incidente de la tabla para editar.",
                title="Atención"
            )
            return

        if self.on_solicitar_edicion:
            self.on_solicitar_edicion(incidente)

    def _on_adherir_voto(self) -> None:
        """Adhiere un voto mediante transformación inmutable."""
        incidente = self._obtener_incidente_seleccionado()
        if not incidente:
            Messagebox.show_warning(
                "Seleccione un incidente de la tabla para adherir un voto.",
                title="Atención"
            )
            return

        exito, mensaje = self.state_manager.adherir_voto(incidente.id, incremento=1)
        if exito:
            self._seleccionar_por_id(incidente.id)
        else:
            Messagebox.show_error(mensaje, title="Error")

    def _on_click_borrar_seleccionada(self) -> None:
        """Callback del botón 'Borrar Seleccionada' (restringido a Admin)."""
        if not self.state_manager.puede_eliminar:
            Messagebox.show_warning(
                "Solo los administradores tienen permisos para eliminar incidencias del sistema.",
                title="Acceso Denegado"
            )
            return

        incidente = self._obtener_incidente_seleccionado()
        if not incidente:
            Messagebox.show_warning(
                "Seleccione un incidente de la tabla para eliminar.",
                title="Atención"
            )
            return

        confirmacion = Messagebox.yesno(
            f"¿Está seguro de que desea eliminar permanentemente el incidente #{incidente.id} ({incidente.tipo_incidente})?\n\n"
            f"Sector: {incidente.sector}\n"
            f"Descripción: {incidente.descripcion[:60]}...\n\n"
            f"Esta acción no se puede deshacer.",
            title="Confirmar Eliminación",
            alert=True
        )
        if confirmacion not in ("Yes", "Sí", "Si", True):
            return

        exito, mensaje = self.state_manager.eliminar_incidente(incidente.id)
        if exito:
            Messagebox.show_info(mensaje, title="Incidente Eliminado")
        else:
            Messagebox.show_error(mensaje, title="Error")

    def _on_aplicar_filtro(self) -> None:
        sector = self.var_filtro_sector.get().strip()
        if not sector:
            Messagebox.show_warning("Ingrese el sector territorial que desea filtrar.", title="Filtro")
            return
        self.state_manager.aplicar_filtro_sector(sector)

    def _on_limpiar_filtro(self) -> None:
        self.var_filtro_sector.set("")
        self.state_manager.limpiar_filtro()

    def _on_mostrar_resumenes_map(self) -> None:
        sector = self.state_manager.filtro_sector_actual
        if not sector:
            Messagebox.show_info(
                "Aplique primero un filtro por sector para ver los resúmenes correspondientes.",
                title="Resúmenes por Sector"
            )
            return

        resumenes = self.state_manager.obtener_resumenes_sector()
        if not resumenes:
            Messagebox.show_info(f"No hay incidentes visibles en '{sector}'.", title="Sin Resultados")
            return

        texto = "\n".join(f"• {r}" for r in resumenes)
        Messagebox.show_info(
            f"Resumen de incidencias en '{sector}':\n\n{texto}",
            title=f"Resumen del Sector: {sector}"
        )

    # ========================================================================
    # RENDERIZADO REACTIVO DE DATOS
    # ========================================================================

    def refrescar_tabla(self) -> None:
        """Actualiza la tabla con los incidentes permitidos por filtrar_por_permisos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        incidentes_visibles = self.state_manager.obtener_incidentes_visibles()

        for inc in incidentes_visibles:
            dpto = self.state_manager.obtener_info_departamento(inc)
            self.tree.insert(
                "",
                tk.END,
                values=(
                    inc.id,
                    inc.sector,
                    inc.tipo_incidente,
                    f"★ {inc.nivel_prioridad}",
                    inc.estado,
                    dpto,
                    inc.descripcion
                )
            )

        # Control de Acceso por Rol para el botón Borrar (Solo Admin)
        if self.state_manager.puede_eliminar:
            self.btn_borrar.pack(side=LEFT, padx=(0, 8), after=self.btn_editar)
            self.btn_borrar.configure(state="normal")
        else:
            self.btn_borrar.pack_forget()

        filtro_actual = self.state_manager.filtro_sector_actual
        self.var_filtro_activo_texto.set(f"Filtro: {filtro_actual}" if filtro_actual else "Filtro: Todos")

        prioridad_total = self.state_manager.obtener_prioridad_total_visible()
        self.var_prioridad_total_texto.set(f"Prioridad Total: {prioridad_total}")
        self.var_conteo_incidentes_texto.set(f"Total Visibles: {len(incidentes_visibles)}")

    def _seleccionar_por_id(self, incidente_id: int) -> None:
        for item in self.tree.get_children():
            valores = self.tree.item(item, "values")
            if valores and int(valores[0]) == incidente_id:
                self.tree.selection_set(item)
                self.tree.focus(item)
                break
