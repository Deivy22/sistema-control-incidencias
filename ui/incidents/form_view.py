"""
form_view.py - Formulario Modular para Registro y Edición de Incidencias
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Peachy Delight)

Garantías Funcionales:
1. Inmutabilidad en Edición: Al guardar, delega en 'actualizar_incidente' (/core/engine.py),
   generando una nueva copia inmutable sin mutar el objeto original.
2. Tipos Dinámicos: El catálogo de tipos se lee de /data/tipos_incidente.json.
3. Selección de ID Reactiva: En modo edición, el ID se selecciona mediante un ttk.Combobox
   alimentado por la función pura de orden superior 'extraer_ids_incidentes' (map) de /core/analisis.py.
"""

import tkinter as tk
from typing import Callable, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, W, X
from ttkbootstrap.dialogs import Messagebox

from core.models import EstadoIncidente, Incidente
from ui.state_manager import StateManager


class IncidenteFormView(tb.Frame):
    """
    Formulario modular reusable tanto para 'crear' nuevos reportes como para
    'editar' incidencias existentes.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager,
        modo: str = "crear",  # "crear" o "editar"
        on_accion_completada: Optional[Callable[[], None]] = None
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager
        self.modo = modo
        self.on_accion_completada = on_accion_completada

        # Variables de formulario
        self.var_id = tk.StringVar(value="")
        self.var_sector = tk.StringVar()
        self.var_tipo = tk.StringVar()
        self.var_estado = tk.StringVar(value="Reportado")
        self.var_prioridad = tk.IntVar(value=1)
        self.var_justificacion = tk.StringVar(value="")

        self._construir_interfaz()
        self.sincronizar_con_estado()

    def _construir_interfaz(self) -> None:
        """Construye los campos del formulario con estética pastel."""
        titulo_tarjeta = (
            "⚙️ Modificación Oficial de Incidencia"
            if self.modo == "editar"
            else "📝 Registro de Nuevo Reporte Ciudadano"
        )

        card = tb.Labelframe(
            self,
            text=titulo_tarjeta,
            padding=25,
            style="Pastel.TLabelframe"
        )
        card.pack(fill=BOTH, expand=True)

        # 1. Campo ID: Combobox dinámico en modo edición
        if self.modo == "editar":
            frame_id = tb.Frame(card, style="Pastel.TFrame")
            frame_id.pack(fill=X, pady=(0, 15))

            tb.Label(
                frame_id,
                text="Seleccionar ID del Incidente:",
                font=("Segoe UI", 10, "bold"),
                style="Pastel.TLabel"
            ).pack(side=LEFT, padx=(0, 10))

            # COMBOBOX DE SELECCIÓN DE ID DINÁMICO
            self.combo_id = tb.Combobox(
                frame_id,
                textvariable=self.var_id,
                width=18,
                font=("Segoe UI", 9)
            )
            self.combo_id.pack(side=LEFT, padx=(0, 10))
            self.combo_id.bind("<<ComboboxSelected>>", self._on_id_seleccionado)
            self.combo_id.bind("<Return>", self._on_id_seleccionado)

            tb.Label(
                frame_id,
                text="(Seleccione de la lista desplegable o escriba el ID)",
                style="PastelMuted.TLabel"
            ).pack(side=LEFT)

        # 2. Campo Sector Territorial
        tb.Label(
            card,
            text="Sector Territorial:",
            font=("Segoe UI", 10, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        sectores = ["Sector Norte", "Sector Centro", "Sector Sur", "Sector Occidental", "Sector Oriental"]
        self.combo_sector = tb.Combobox(
            card,
            textvariable=self.var_sector,
            values=sectores,
            width=35,
            font=("Segoe UI", 9)
        )
        self.combo_sector.pack(fill=X, pady=(0, 12))

        # 3. Campo Tipo de Incidente
        tb.Label(
            card,
            text="Tipo de Incidente:",
            font=("Segoe UI", 10, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        tipos_disponibles = self.state_manager.obtener_tipos_incidente()
        self.combo_tipo = tb.Combobox(
            card,
            textvariable=self.var_tipo,
            values=tipos_disponibles,
            state="readonly",
            width=35,
            font=("Segoe UI", 9)
        )
        self.combo_tipo.pack(fill=X, pady=(0, 12))
        if tipos_disponibles and not self.var_tipo.get():
            self.var_tipo.set(tipos_disponibles[0])

        # 4. Campos exclusivos de edición (Estado y Prioridad)
        if self.modo == "editar":
            frame_fila_doble = tb.Frame(card, style="Pastel.TFrame")
            frame_fila_doble.pack(fill=X, pady=(0, 12))

            # Estado
            col1 = tb.Frame(frame_fila_doble, style="Pastel.TFrame")
            col1.pack(side=LEFT, expand=True, fill=X, padx=(0, 8))
            tb.Label(
                col1,
                text="Estado del Incidente:",
                font=("Segoe UI", 10, "bold"),
                style="Pastel.TLabel"
            ).pack(anchor=W, pady=(0, 4))

            estados = ["Reportado", "EnProceso", "Resuelto", "Descartado"]
            self.combo_estado = tb.Combobox(
                col1,
                textvariable=self.var_estado,
                values=estados,
                state="readonly",
                font=("Segoe UI", 9)
            )
            self.combo_estado.pack(fill=X)

            # Prioridad
            col2 = tb.Frame(frame_fila_doble, style="Pastel.TFrame")
            col2.pack(side=RIGHT, expand=True, fill=X, padx=(8, 0))
            tb.Label(
                col2,
                text="Nivel de Prioridad (1-10):",
                font=("Segoe UI", 10, "bold"),
                style="Pastel.TLabel"
            ).pack(anchor=W, pady=(0, 4))

            spin_prioridad = tb.Spinbox(
                col2,
                from_=1,
                to=10,
                textvariable=self.var_prioridad,
                font=("Segoe UI", 9)
            )
            spin_prioridad.pack(fill=X)

            # Justificación del cambio de estado
            tb.Label(
                card,
                text="Justificación del Cambio de Estado (obligatoria para reaperturas o descartes):",
                font=("Segoe UI", 9, "bold"),
                style="Pastel.TLabel"
            ).pack(anchor=W, pady=(0, 4))

            self.entry_justificacion = tb.Entry(
                card,
                textvariable=self.var_justificacion,
                font=("Segoe UI", 9)
            )
            self.entry_justificacion.pack(fill=X, pady=(0, 12))

        # 5. Campo Descripción Detallada
        tb.Label(
            card,
            text="Descripción del Incidente:",
            font=("Segoe UI", 10, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        self.txt_descripcion = tb.Text(card, height=5, font=("Segoe UI", 10), wrap="word")
        self.txt_descripcion.pack(fill=BOTH, expand=True, pady=(0, 18))

        # 6. Botones de Acción
        frame_botones = tb.Frame(card, style="Pastel.TFrame")
        frame_botones.pack(fill=X)

        texto_boton = "💾 Guardar Modificación" if self.modo == "editar" else "➕ Registrar Incidente"
        estilo_boton = "PastelPeach.TButton" if self.modo == "editar" else "PastelMint.TButton"

        btn_guardar = tb.Button(
            frame_botones,
            text=texto_boton,
            style=estilo_boton,
            command=self._on_guardar
        )
        btn_guardar.pack(side=LEFT, expand=True, fill=X, padx=(0, 4), ipady=5)

        if self.modo == "editar":
            btn_limpiar = tb.Button(
                frame_botones,
                text="Limpiar Formulario",
                style="PastelNeutral.TButton",
                command=self.limpiar_formulario
            )
            btn_limpiar.pack(side=RIGHT, padx=(4, 0), ipady=5)

    def _on_id_seleccionado(self, event=None) -> None:
        """
        Al seleccionar un ID en el Combobox, busca el incidente correspondiente
        y autocompleta el formulario.
        """
        raw_id = self.var_id.get().strip()
        if not raw_id.isdigit():
            return

        incidente_id = int(raw_id)
        incidente = self.state_manager.obtener_incidente_por_id(incidente_id)
        if incidente:
            self.cargar_incidente(incidente)
        else:
            Messagebox.show_warning(
                f"No se encontró ningún incidente con el ID #{incidente_id}.",
                title="ID no encontrado"
            )

    def sincronizar_con_estado(self) -> None:
        """Sincroniza los valores desplegables y campos con el StateManager."""
        # 1. Actualizar catálogo dinámico de tipos
        tipos_actualizados = self.state_manager.obtener_tipos_incidente()
        self.combo_tipo["values"] = tipos_actualizados

        # 2. Si estamos en modo editar, actualizar la lista de IDs proyectados con map()
        if self.modo == "editar":
            ids_existentes = self.state_manager.obtener_ids_incidentes()
            self.combo_id["values"] = [str(i) for i in ids_existentes]

            # Si hay un incidente en el búfer de edición, cargarlo
            inc_edit = self.state_manager.incidente_en_edicion
            if inc_edit:
                self.cargar_incidente(inc_edit)
        else:
            usuario = self.state_manager.usuario_actual
            if usuario and usuario.rol == "Comunidad" and usuario.sector:
                self.var_sector.set(usuario.sector)
            elif not self.var_sector.get():
                self.var_sector.set("Sector Norte")

            if tipos_actualizados and not self.var_tipo.get():
                self.var_tipo.set(tipos_actualizados[0])

    def cargar_incidente(self, inc: Incidente) -> None:
        """Carga los atributos de una instancia Incidente en el formulario."""
        self.var_id.set(str(inc.id))
        self.var_sector.set(inc.sector)
        self.var_tipo.set(inc.tipo_incidente)
        self.var_estado.set(inc.estado)
        self.var_prioridad.set(inc.nivel_prioridad)
        self.var_justificacion.set(inc.justificacion_estado)
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_descripcion.insert("1.0", inc.descripcion)

    def limpiar_formulario(self) -> None:
        """Limpia los campos del formulario."""
        self.var_id.set("")
        self.var_sector.set("Sector Norte")
        tipos = self.state_manager.obtener_tipos_incidente()
        self.var_tipo.set(tipos[0] if tipos else "Choque")
        self.var_estado.set("Reportado")
        self.var_prioridad.set(1)
        self.var_justificacion.set("")
        self.txt_descripcion.delete("1.0", tk.END)
        self.state_manager.limpiar_edicion()

    def _on_guardar(self) -> None:
        """Procesa el envío del formulario delegando en el StateManager."""
        sector = self.var_sector.get().strip()
        tipo = self.var_tipo.get().strip()
        descripcion = self.txt_descripcion.get("1.0", tk.END).strip()

        if not sector:
            Messagebox.show_warning("El sector territorial es requerido.", title="Validación")
            return
        if not descripcion:
            Messagebox.show_warning("La descripción no puede estar vacía.", title="Validación")
            return

        if self.modo == "crear":
            # CREACIÓN
            exito, mensaje = self.state_manager.agregar_incidente(
                sector=sector,
                descripcion=descripcion,
                tipo_incidente=tipo
            )
            if exito:
                Messagebox.show_info(mensaje, title="Registro Exitoso")
                self.txt_descripcion.delete("1.0", tk.END)
                if self.on_accion_completada:
                    self.on_accion_completada()
            else:
                Messagebox.show_error(mensaje, title="Error de Validación")

        else:
            # EDICIÓN INMUTABLE
            raw_id = self.var_id.get().strip()
            if not raw_id.isdigit():
                Messagebox.show_warning(
                    "Por favor seleccione un ID válido en el desplegable para modificar.",
                    title="Atención"
                )
                return

            incidente_id = int(raw_id)
            estado = self.var_estado.get()
            prioridad = self.var_prioridad.get()
            justificacion = self.var_justificacion.get().strip()

            # DELEGACIÓN A STATE MANAGER (QUE INVOCA actualizar_incidente DE FORMA PURA)
            exito, mensaje = self.state_manager.modificar_incidente(
                incidente_id=incidente_id,
                sector=sector,
                descripcion=descripcion,
                tipo_incidente=tipo,
                estado=estado,
                nivel_prioridad=prioridad,
                justificacion=justificacion
            )

            if exito:
                Messagebox.show_info(mensaje, title="Modificación Exitosa")
                self.limpiar_formulario()
                if self.on_accion_completada:
                    self.on_accion_completada()
            else:
                Messagebox.show_error(mensaje, title="Error en Modificación")
