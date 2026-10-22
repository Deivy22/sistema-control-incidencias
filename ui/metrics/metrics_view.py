"""
metrics_view.py - Tablero de Métricas y Rendimiento Distrital
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Peachy Delight)
Acceso: Exclusivo para 'Admin' y 'Gobierno'

Este módulo presenta los indicadores clave de desempeño (KPIs) y resúmenes analíticos:
1. Tasa porcentual de resolución de incidentes.
2. Detección de reportes críticos pendientes de atención.
3. Distribución territorial por sector y tipología urbana.
4. Total de prioridad acumulada (calculada mediante la HOF reduce).
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, VERTICAL, W, X, Y

from ui.state_manager import StateManager


class MetricsDashboardView(tb.Frame):
    """
    Vista analítica exclusiva para autoridades (Admin y Gobierno).
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager

        # Variables reactivas para los KPIs
        self.var_total_incidentes = tk.StringVar(value="0")
        self.var_tasa_resolucion = tk.StringVar(value="0.0%")
        self.var_criticos_pendientes = tk.StringVar(value="0")
        self.var_prioridad_resumen = tk.StringVar(value="0 pts")

        self._construir_interfaz()
        self.refrescar_metricas()

    def _construir_interfaz(self) -> None:
        """Construye las tarjetas de KPIs y las tablas de desglose analítico."""
        # 1. Banner superior informativo
        banner = tb.Labelframe(
            self,
            text="📊 Tablero de Mando y Analítica Distrital (Admin / Gobierno)",
            padding=12,
            style="Pastel.TLabelframe"
        )
        banner.pack(fill=X, padx=15, pady=(10, 10))

        tb.Label(
            banner,
            text="Panel de supervisión urbana exclusivo para autoridades y administradores. "
                 "Permite monitorear la efectividad de respuesta, concentración de fallas por sector "
                 "y puntos críticos en tiempo real a través de agregaciones funcionales.",
            style="PastelMuted.TLabel"
        ).pack(anchor=W)

        # 2. Fila de KPIs (Tarjetas destacadas)
        frame_kpis = tb.Frame(self, style="Pastel.TFrame")
        frame_kpis.pack(fill=X, padx=15, pady=(0, 12))

        # KPI 1: Total Reportes
        self._crear_tarjeta_kpi(
            parent=frame_kpis,
            titulo="📌 Total Incidentes",
            variable=self.var_total_incidentes,
            subtexto="Reportes registrados en el sistema"
        )

        # KPI 2: Tasa de Resolución
        self._crear_tarjeta_kpi(
            parent=frame_kpis,
            titulo="✅ Tasa de Resolución",
            variable=self.var_tasa_resolucion,
            subtexto="Efectividad de cierre distrital"
        )

        # KPI 3: Críticos Pendientes
        self._crear_tarjeta_kpi(
            parent=frame_kpis,
            titulo="⚠️ Críticos Pendientes",
            variable=self.var_criticos_pendientes,
            subtexto="Prioridad ≥ 4 sin resolver"
        )

        # KPI 4: Prioridad Acumulada
        self._crear_tarjeta_kpi(
            parent=frame_kpis,
            titulo="⭐ Prioridad Acumulada",
            variable=self.var_prioridad_resumen,
            subtexto="Suma total ponderada (reduce)"
        )

        # 3. Paneles inferiores de distribución analítica
        paneles = tb.Frame(self, style="Pastel.TFrame")
        paneles.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))

        # Panel Izquierdo: Ciclo de Vida y Tipología
        panel_izq = tb.Labelframe(
            paneles,
            text="📈 Estado del Ciclo de Vida y Tipología",
            padding=15,
            style="Pastel.TLabelframe"
        )
        panel_izq.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        # Treeview de Ciclo de Vida (Estados)
        tb.Label(
            panel_izq,
            text="Distribución por Estado del Incidente:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        frame_tree_estados = tb.Frame(panel_izq, style="Pastel.TFrame")
        frame_tree_estados.pack(fill=X, pady=(0, 12))

        self.tree_estados = tb.Treeview(
            frame_tree_estados,
            columns=("estado", "cantidad", "porcentaje"),
            show="headings",
            style="Pastel.Treeview",
            height=4
        )
        self.tree_estados.heading("estado", text="Estado", anchor=W)
        self.tree_estados.heading("cantidad", text="Cantidad", anchor=W)
        self.tree_estados.heading("porcentaje", text="% del Total", anchor=W)
        self.tree_estados.column("estado", width=140)
        self.tree_estados.column("cantidad", width=80)
        self.tree_estados.column("porcentaje", width=90)
        self.tree_estados.pack(fill=X)

        # Treeview de Tipos de Incidente
        tb.Label(
            panel_izq,
            text="Distribución por Tipo de Incidente:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        frame_tree_tipos = tb.Frame(panel_izq, style="Pastel.TFrame")
        frame_tree_tipos.pack(fill=BOTH, expand=True)

        self.tree_tipos = tb.Treeview(
            frame_tree_tipos,
            columns=("tipo", "cantidad", "porcentaje"),
            show="headings",
            style="Pastel.Treeview",
            selectmode="browse"
        )
        self.tree_tipos.heading("tipo", text="Tipo de Incidente", anchor=W)
        self.tree_tipos.heading("cantidad", text="Cantidad", anchor=W)
        self.tree_tipos.heading("porcentaje", text="% del Total", anchor=W)
        self.tree_tipos.column("tipo", width=170)
        self.tree_tipos.column("cantidad", width=70)
        self.tree_tipos.column("porcentaje", width=80)

        scroll_tipos = tb.Scrollbar(frame_tree_tipos, orient=VERTICAL, command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scroll_tipos.set)
        self.tree_tipos.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_tipos.pack(side=RIGHT, fill=Y)

        # Panel Derecho: Concentración Territorial
        panel_der = tb.Labelframe(
            paneles,
            text="🏘️ Concentración Territorial por Sector",
            padding=15,
            style="Pastel.TLabelframe"
        )
        panel_der.pack(side=RIGHT, fill=BOTH, expand=True, padx=(8, 0))

        # Botón de refresco manual
        barra_der = tb.Frame(panel_der, style="Pastel.TFrame")
        barra_der.pack(fill=X, pady=(0, 8))

        tb.Button(
            barra_der,
            text="🔄 Recalcular Métricas",
            style="PastelNeutral.TButton",
            command=self.refrescar_metricas
        ).pack(side=RIGHT)

        frame_tree_sectores = tb.Frame(panel_der, style="Pastel.TFrame")
        frame_tree_sectores.pack(fill=BOTH, expand=True)

        self.tree_sectores = tb.Treeview(
            frame_tree_sectores,
            columns=("sector", "cantidad", "porcentaje"),
            show="headings",
            style="Pastel.Treeview",
            selectmode="browse"
        )
        self.tree_sectores.heading("sector", text="Sector Territorial", anchor=W)
        self.tree_sectores.heading("cantidad", text="Incidentes", anchor=W)
        self.tree_sectores.heading("porcentaje", text="% del Total", anchor=W)
        self.tree_sectores.column("sector", width=180)
        self.tree_sectores.column("cantidad", width=80)
        self.tree_sectores.column("porcentaje", width=90)

        scroll_sectores = tb.Scrollbar(frame_tree_sectores, orient=VERTICAL, command=self.tree_sectores.yview)
        self.tree_sectores.configure(yscrollcommand=scroll_sectores.set)
        self.tree_sectores.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_sectores.pack(side=RIGHT, fill=Y)

    def _crear_tarjeta_kpi(
        self,
        parent: tb.Frame,
        titulo: str,
        variable: tk.StringVar,
        subtexto: str
    ) -> tb.Labelframe:
        card = tb.Labelframe(parent, text=titulo, padding=12, style="Pastel.TLabelframe")
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=4)

        tb.Label(
            card,
            textvariable=variable,
            font=("Segoe UI", 16, "bold"),
            style="PastelBadge.TLabel"
        ).pack(anchor=W, pady=(2, 2))

        tb.Label(
            card,
            text=subtexto,
            style="PastelMuted.TLabel"
        ).pack(anchor=W)

        return card

    def refrescar_metricas(self) -> None:
        """Consulta métricas globales sintetizadas funcionalmente y actualiza la vista."""
        metricas = self.state_manager.obtener_metricas_sistema()
        total = metricas.get("total", 0)

        # Actualización de KPIs
        self.var_total_incidentes.set(f"{total} reportes")
        self.var_tasa_resolucion.set(f"{metricas.get('tasa_resolucion', 0.0)}%")
        self.var_criticos_pendientes.set(f"{metricas.get('criticos_pendientes', 0)} casos")
        self.var_prioridad_resumen.set(
            f"{metricas.get('prioridad_total', 0)} pts (Prom: {metricas.get('promedio_prioridad', 0.0)})"
        )

        # 1. Tabla de Estados
        for item in self.tree_estados.get_children():
            self.tree_estados.delete(item)

        estados_info = [
            ("✅ Resueltos", metricas.get("resueltos", 0)),
            ("⚙️ En Proceso", metricas.get("en_proceso", 0)),
            ("📝 Reportados", metricas.get("reportados", 0)),
            ("🚫 Descartados", metricas.get("descartados", 0)),
        ]
        for nom, cant in estados_info:
            pct = round((cant / total * 100), 1) if total > 0 else 0.0
            self.tree_estados.insert("", tk.END, values=(nom, cant, f"{pct}%"))

        # 2. Tabla de Tipos
        for item in self.tree_tipos.get_children():
            self.tree_tipos.delete(item)

        por_tipo = metricas.get("por_tipo", {})
        for tipo, cant in sorted(por_tipo.items(), key=lambda x: x[1], reverse=True):
            pct = round((cant / total * 100), 1) if total > 0 else 0.0
            self.tree_tipos.insert("", tk.END, values=(tipo, cant, f"{pct}%"))

        # 3. Tabla de Sectores
        for item in self.tree_sectores.get_children():
            self.tree_sectores.delete(item)

        por_sector = metricas.get("por_sector", {})
        for sec, cant in sorted(por_sector.items(), key=lambda x: x[1], reverse=True):
            pct = round((cant / total * 100), 1) if total > 0 else 0.0
            self.tree_sectores.insert("", tk.END, values=(sec, cant, f"{pct}%"))

