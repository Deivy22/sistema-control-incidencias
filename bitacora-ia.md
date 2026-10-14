# Bitácora de Uso de Inteligencia Artificial (IA)
**Proyecto:** Sistema de Control de Incidencias Ciudadanas  
**Asignatura:** Programación Funcional — Unidades 1 y 2  
**Estudiante:** Deivy  
**Herramientas de IA utilizadas:** Gemini (Consultoría Funcional) y Antigravity / Copilot (Asistencia de Código)  

---

## 1. Introducción y Criterio de Uso de IA

En el marco de la actividad integradora de las Unidades 1 y 2, se utilizó inteligencia artificial como herramienta de aceleración sintáctica y prototipado visual. Sin embargo, tal como establece la rúbrica de evaluación: **"La IA es una herramienta, no un sustituto del criterio técnico"**.

A lo largo del ciclo de vida del proyecto, la IA tendió sistemáticamente a generar soluciones imperativas, arquitecturas planas monolíticas, mutaciones de estado destructivas y controles de acceso ficticios. Esta bitácora documenta de manera transparente y técnica las **intervenciones críticas donde el estudiante rechazó, reestructuró y corrigió las propuestas de la IA** para garantizar la pureza funcional, la inmutabilidad y una arquitectura de software desacoplada y robusta.

---

## 2. Matriz Resumen de Intervenciones Críticas

| # | Intervención | Sugerencia Inicial de la IA | Decisión del Estudiante | Concepto Clave Aplicado |
|---|---|---|---|---|
| **1** | Capa de Persistencia `/data/` | Archivos planos en raíz; mezcla de I/O en core y vistas | 🔴 **Rechazado** (Creación de `/data/` aislada) | Efectos secundarios, Functional Core / Imperative Shell |
| **2** | Modularización UI en Subcarpetas | Monolito de 700+ líneas en un único archivo `ui/` | 🔴 **Rechazado** (División en `auth`, `dashboard`, `incidents`) | Principio de Responsabilidad Única (SRP), Modularidad |
| **3** | Autenticación y Control de Roles | `Combobox` estético para "elegir" rol sin clave | 🔴 **Rechazado** (Login real contra `usuarios.json`) | Seguridad, `filter` declarativo por permisos |
| **4** | Corrección de Bugs en Cerrar Sesión | Ocultamiento visual con `pack_forget()` (widgets zombis) | 🟡 **Corregido** (`destroy()` del contenedor y reset limpio) | Ciclo de vida Tkinter, Observer seguro sin fugas |
| **5** | Catálogo Dinámico de Tipos | Lista de tipos hardcodeada en el frontend | 🔴 **Rechazado** (Carga desde `tipos_incidente.json`) | Principio Abierto/Cerrado (OCP), Validación Pura |
| **6** | Eliminación Inmutable de Incidencias | Mutación imperativa in-situ (`lista.remove()`, `del`) | 🔴 **Rechazado** (Uso estricto de `filter()`) | Inmutabilidad (Unidad 2), Funciones de Orden Superior |
| **7** | Limpieza Visual y Experiencia de Usuario | Jerga técnica visible en etiquetas ("FCIS", "HOF map") | 🟡 **Corregido** (Etiquetas orientadas al usuario final) | UX profesional, Abstracción de detalles internos |

---

## Intervención 1: Creación de la Capa de Datos (`/data/`) y Aislamiento de Efectos Secundarios

### Prompt usado:
> *"Genera models.py usando dataclass(frozen=True) para inmutabilidad y engine.py con funciones puras para validar spam y pattern matching con match/case. Prohibido usar Tkinter aquí."*

### Fragmento sugerido por la IA:
La IA propuso generar los scripts de lógica básica dejando los archivos de datos (`incidentes.json`) en la raíz del proyecto, o accediendo directamente a `open()` dentro de los mismos módulos de lógica o callbacks de botones:

```python
# PROPUESTA DEFECTUOSA DE LA IA (Mezcla de I/O y lógica):
def guardar_incidente(incidente):
    # Efecto secundario impuro incrustado sin separación de capas
    with open("incidentes.json", "r+") as f:
        datos = json.load(f)
        datos.append(asdict(incidente))
        f.seek(0)
        json.dump(datos, f)
```

### Decisión:
🔴 **Rechazado y Reestructurado por el Estudiante.**

### Por qué (Justificación técnica):
1. **Violación del paradigma FCIS (Functional Core, Imperative Shell):** Si una función de lógica de negocio realiza operaciones de lectura/escritura en disco, deja de ser referencialmente transparente y se vuelve impura.
2. **Aislamiento de Efectos Secundarios:** Fui yo quien ordenó explícitamente crear una carpeta independiente `/data/` y concentrar toda la persistencia en `data/file_handler.py`. De este modo:
   - `/core/` permanece **100% libre de I/O**, conteniendo únicamente funciones puras y modelos inmutables.
   - `/data/` contiene de forma explícita y justificada las funciones impuras que interactúan con el sistema de archivos del sistema operativo.

---

## Intervención 2: Reestructuración Modular de la Interfaz Visual (De Monolito a Subcarpetas)

### Prompt usado:
> *"Crea la interfaz gráfica con ttkbootstrap. Implementa un sistema de Login, y un panel con pestañas para Registrar, Ver y Modificar incidencias."*

### Fragmento sugerido por la IA:
La IA generó una única clase gigante (`MainWindow`) dentro de un archivo monolítico en `ui/main_window.py` (con más de 700 líneas), donde se mezclaba el formulario de login, el cuaderno de pestañas, las tablas Treeview, los diálogos modales y las validaciones.

```python
# PROPUESTA DEFECTUOSA DE LA IA (Monolito inmanejable):
class MainWindow(tb.Window):
    def __init__(self):
        # 700+ líneas mezclando:
        # - login frame
        # - notebook tabs
        # - treeview construction
        # - edit form
        # - handlers directos sin separación
        ...
```

### Decisión:
🔴 **Rechazado y Refactorizado por el Estudiante.**

### Por qué (Justificación técnica):
1. **Acoplamiento excesivo y deuda técnica:** Un archivo monolítico viola el Principio de Responsabilidad Única (SRP) y hace inviable el mantenimiento y testing unitario de componentes visuales.
2. **Modularización obligatoria en subcarpetas:** Le exigí a la IA reestructurar la carpeta `/ui/` en paquetes especializados por dominio:
   - `/ui/auth/login_view.py`: Vista especializada exclusivamente en autenticación.
   - `/ui/dashboard/main_window.py`: Contenedor maestro orquestador de sesión y pestañas.
   - `/ui/incidents/list_view.py`: Vista tabular de consulta, filtros y métricas funcionales.
   - `/ui/incidents/form_view.py`: Componente reutilizable para creación y modificación.
3. Esto demostró que la IA tiende a generar código "que funciona a corto plazo" sacrificando la arquitectura limpia, requiriendo dirección arquitectónica humana.

---

## Intervención 3: Rechazo de Falsa Seguridad (Login con Combobox vs. Autenticación Real)

### Prompt usado:
> *"El panel actual viola nuestras reglas de negocio. Un menú desplegable para seleccionar el rol es inseguro y poco realista. Refactoriza con autenticación real."*

### Fragmento sugerido por la IA:
Para "simular" los tres roles de usuario (Admin, Gobierno, Comunidad), la IA había colocado un `ttk.Combobox` en la barra superior donde el usuario simplemente seleccionaba qué rol quería tener y la interfaz cambiaba de permisos automáticamente:

```python
# PROPUESTA DEFECTUOSA DE LA IA (Falsa seguridad por Combobox):
self.combo_rol = tb.Combobox(parent, values=["Admin", "Gobierno", "Comunidad"])
self.combo_rol.bind("<<ComboboxSelected>>", self._cambiar_rol_simulado)

def _cambiar_rol_simulado(self, event):
    rol_seleccionado = self.combo_rol.get()
    self.state_manager.usuario_actual = Usuario(id=1, nombre="Test", rol=rol_seleccionado)
```

### Decisión:
🔴 **Rechazado Tajantemente.**

### Por qué (Justificación técnica):
1. **Inseguridad inaceptable:** En un sistema real de control de incidencias gubernamentales, un ciudadano no puede asignarse permisos administrativos eligiendo una opción de un desplegable.
2. **Solución impuesta por el estudiante:**
   - Creación de una base de datos de credenciales en `/data/usuarios.json` con usuarios, hashes de contraseña simulados, roles y sectores.
   - Implementación de la función pura `autenticar_usuario(user, password, base_datos)` en `/core/auth.py`, garantizando verificación determinista sin mutaciones.
   - Pantalla real de Login con campos protegidos (`show="*"`) en `/ui/auth/login_view.py`.

---

## Intervención 4: Corrección de Bugs de Ciclo de Vida y Callbacks Zombis en "Cerrar Sesión"

### Prompt usado:
> *"Al presionar 'Cerrar Sesión' y volver al Login, el botón 'Ingresar al Sistema' queda bloqueado y no hace nada. Soluciona el bug destruyendo completamente el contenedor principal con destroy() y reinstanciando limpiamente."*

### Fragmento sugerido por la IA:
Cuando el usuario cerraba sesión, la IA intentaba ocultar el dashboard con `.pack_forget()` y volver a mostrar el frame previo del login. Esto generaba widgets "zombis": los eventos vinculados con `.bind("<Return>")`, los callbacks de botones y la lista de observadores del `StateManager` mantenían referencias a instancias huérfanas en memoria de Tkinter.

```python
# PROPUESTA DEFECTUOSA DE LA IA (Ocultamiento superficial con fuga de eventos):
def cerrar_sesion(self):
    self.vista_dashboard.pack_forget()
    self.vista_login.pack(fill=BOTH, expand=True)  # Callbacks zombis y memoria duplicada
```

### Decisión:
🟡 **Corregido y Dirigido por el Estudiante.**

### Por qué (Justificación técnica):
1. **Fuga de oyentes (Observer Leak):** Los observadores suscritos al `StateManager` intentaban actualizar widgets que ya no estaban activos en pantalla, provocando excepciones silenciosas o bloqueos de eventos.
2. **Destrucción explícita del ciclo de vida (`destroy()`):** Obligué a la IA a implementar el patrón de ciclo de vida limpio en `main.py` (`AppOrchestrator`):
   ```python
   # SOLUCIÓN TÉCNICA APLICADA:
   def mostrar_login(self) -> None:
       if self.contenedor_principal is not None:
           self.contenedor_principal.destroy()  # Destrucción física del árbol de widgets
       self.contenedor_principal = tb.Frame(self.root, style="Pastel.TFrame")
       self.contenedor_principal.pack(fill=BOTH, expand=True)
       self.vista_login = LoginView(...)
   ```
   Asimismo, en `StateManager.cerrar_sesion()` se agregó la limpieza preventiva `self._subscriptores.clear()`.

---

## Intervención 5: Rechazo de Hardcoding en el Catálogo de Tipos (Tipos Dinámicos y Validación Pura)

### Prompt usado:
> *"Rechazo dejar los tipos de incidentes fijos en el código. Crea tipos_incidente.json, una función pura en core/engine.py que valide si el tipo existe en esa lista, y haz que los Combobox de Registrar y Modificar lo lean en caliente."*

### Fragmento sugerido por la IA:
En la primera versión de los formularios de captura y modificación, la IA había escrito los tipos de incidencia directamente en el código de la vista (hardcoding):

```python
# PROPUESTA DEFECTUOSA DE LA IA (Valores quemados / Hardcoded):
tipos_fijos = ["Choque", "Falla Electrica", "Alcantarillado"]
self.combo_tipo = tb.Combobox(card, values=tipos_fijos)
```

### Decisión:
🔴 **Rechazado por Vulnerabilidad a Escalabilidad.**

### Por qué (Justificación técnica):
1. **Violación del Principio Abierto/Cerrado (OCP):** Si la entidad gubernamental necesita agregar un nuevo tipo de incidencia (ej. "Inundación", "Seguridad Pública", "Infraestructura"), no se debe tener que modificar y recompilar el código fuente de los formularios.
2. **Solución Funcional y Dinámica:**
   - Creación del archivo de configuración `/data/tipos_incidente.json`.
   - Función pura `validar_tipo_incidente(tipo: str, tipos_permitidos: Sequence[str]) -> bool` en `/core/engine.py`.
   - Sincronización reactiva del `Combobox` mediante `StateManager.obtener_tipos_incidente()`, permitiendo que la interfaz se adapte automáticamente al catálogo sin alterar el motor lógico.

---

## Intervención 6: Operación "Borrar Incidencia": Inmutabilidad Estricta con `filter()`

### Prompt usado:
> *"Crea una función pura eliminar_incidente_por_id(lista_incidentes, id_a_borrar). REGLA FUNCIONAL: Está prohibido usar .remove(), del o mutar la lista original. Debes usar filter para retornar una nueva lista. El botón debe ser rojo ('danger') y solo habilitado para 'Admin'."*

### Fragmento sugerido por la IA:
En las sugerencias automáticas de autocompletado y primeros borradores, la IA recurrió de inmediato al hábito imperativo clásico de mutación en caliente:

```python
# PROPUESTA DEFECTUOSA DE LA IA (Mutación destructiva imperativa):
def eliminar_incidente(self, incidente_id):
    for inc in self._incidentes:
        if inc.id == incidente_id:
            self._incidentes.remove(inc)  # ❌ PROHIBIDO: Mutación de la lista in-situ
            del inc                       # ❌ PROHIBIDO: Efecto secundario destructivo
            break
```

### Decisión:
🔴 **Rechazado Tajantemente (Cumplimiento de Unidad 2).**

### Por qué (Justificación técnica):
1. **Destrucción de la Inmutabilidad:** Mutar la lista compartida mediante `.remove()` o `del` destruye el historial de estados, rompe la transparencia referencial y es una fuente conocida de bugs en concurrencia y reactividad.
2. **Solución Funcional Pura:** Forcé a la IA a escribir la función pura en `/core/engine.py`:
   ```python
   # SOLUCIÓN PURA IMPLEMENTADA:
   def eliminar_incidente_por_id(
       lista_incidentes: Sequence[Incidente],
       id_a_borrar: int
   ) -> List[Incidente]:
       """
       Función Pura: Retorna una nueva lista excluyendo el incidente objetivo.
       Cero mutación; utiliza filter() de forma declarativa.
       """
       return list(filter(lambda inc: inc.id != id_a_borrar, lista_incidentes))
   ```
3. **Control de Acceso por Roles (RBAC):** Se condicionó la visibilidad y ejecución mediante la propiedad funcional `StateManager.puede_eliminar`, restringiendo la acción exclusivamente a administradores y ocultando el botón para usuarios de la comunidad.

---

## Intervención 7: Limpieza Visual y Remoción de Jerga Técnica en la Interfaz

### Prompt usado:
> *"Busca y elimina cualquier Label o texto en la barra inferior (statusbar) que diga 'Arquitectura: FCIS...' o 'Cero mutación en edición'. La interfaz debe quedar completamente limpia de jerga técnica en todas las pestañas."*

### Fragmento sugerido por la IA:
La IA había saturado los textos visibles de la interfaz gráfica con frases puramente académicas y técnicas dirigidas al evaluador de código, colocándolas en botones, marcos y en el statusbar:

```python
# PROPUESTA DEFECTUOSA DE LA IA (Jerga técnica en la UI):
tb.Label(status_bar, text="Arquitectura: FCIS + Roles Puros + Paleta Pastel (Soft Sand & Peachy Delight)")
tb.Labelframe(self, text="🔍 Filtro Territorial y Resúmenes Funcionales (Closures & HOFs)")
tb.Label(frame, text="Seleccionar ID del Incidente (HOF map):")
tb.Button(card, text="💾 Guardar Modificación (Inmutable)")
```

### Decisión:
🟡 **Modificado y Pulido por el Estudiante.**

### Por qué (Justificación técnica):
1. **Experiencia de Usuario (UX) Profesional:** La rúbrica exige que la interfaz esté *"pensada para un usuario real"*. Un ciudadano o un funcionario gubernamental que use el sistema no debe ver menciones a "HOFs", "Closures" o "FCIS".
2. **Separación de Niveles de Abstracción:** Los conceptos teóricos y funcionales deben defenderse en el código fuente, en las pruebas unitarias y en el documento de análisis (`analisis-funcional.md`), no ensuciar la experiencia visual del usuario final.

---

## 3. Conclusión y Balance Crítico del Uso de Inteligencia Artificial

### ¿Qué se aceptó de la IA?
- Generación de código repetitivo de interfaz gráfica en `tkinter` y `ttkbootstrap` (definición de frames, paddings, fuentes y paleta pastel).
- Esqueletos base de pruebas unitarias (`unittest`) para acelerar la cobertura de casos límite.
- Reglas sintácticas para el tipado estático (`dataclass`, `Literal`, `Union`, `Sequence`).

### ¿Qué se modificó de la IA?
- La estructura de llamadas entre la UI y el Core, garantizando que los callbacks de botones jamás contengan lógica de negocio y deleguen estrictamente en el `StateManager`.
- Los textos y etiquetas de la interfaz para transformarlos de jerga académica a un producto de software real y profesional.
- El manejo del ciclo de vida de Tkinter para evitar bloqueos por widgets zombis tras cerrar sesión.

### ¿Qué se rechazó por completo de la IA?
- **La arquitectura monolítica plana:** Se rechazó ubicar todo el código en la raíz o en un único archivo de UI.
- **La simulación insegura de roles:** Se rechazó el uso de `Combobox` para saltarse la autenticación.
- **La mutación destructiva imperativa:** Se prohibió terminantemente el uso de `.remove()`, `del` o `.pop()` en las listas de incidentes.
- **El acoplamiento de efectos secundarios:** Se impidió que las funciones de validación o transformación realizaran lecturas directas de archivos.

### Lección Técnica Aprendida
La Inteligencia Artificial es un excelente acelerador sintáctico para tareas mecánicas, pero carece de juicio arquitectónico y tiende por defecto a la programación imperativa y a la mutación de estado. El éxito de un proyecto de Programación Funcional depende de la capacidad del estudiante para identificar estas desviaciones, entender los fundamentos teóricos (pureza, inmutabilidad, closures, HOFs) y forzar a las herramientas a someterse a las restricciones del paradigma.