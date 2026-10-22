# 🏛️ Sistema de Control de Incidencias Ciudadanas

> **Aplicación de Gestión Urbana con Programación Funcional, Control de Roles (RBAC) y Arquitectura FCIS.**  
> Desarrollado con Python 3.13, `ttkbootstrap` (Tema Pastel Soft Sand & Peachy Delight) y persistencia JSON desacoplada.

---

## 📋 Descripción del Proyecto

El **Sistema de Control de Incidencias Ciudadanas** es una plataforma de software diseñada para registrar, clasificar, validar, priorizar, consultar y resolver problemáticas urbanas en el territorio distrital (tales como choques viales, fallas eléctricas, averías de alcantarillado, infraestructura vial y seguridad pública).

El sistema está construido bajo el paradigma de **Programación Funcional**, cumpliendo rigurosamente con los principios de:
- **Inmutabilidad estricta:** Entidades inmutables respaldadas por `@dataclass(frozen=True)` y actualizaciones no destructivas.
- **Transparencia referencial:** Funciones puras libres de efectos secundarios en el núcleo lógico (`/core/`).
- **Arquitectura FCIS (Functional Core, Imperative Shell):** Confinamiento de la impureza de E/S de disco (`/data/`) y la interfaz visual (`/ui/`) al borde del sistema.
- **Funciones de Orden Superior (HOFs) y Closures:** Uso declarativo de `map()`, `filter()`, `reduce()` y clausuras léxicas.
- **Control de Acceso Basado en Roles (RBAC):** Privilegios diferenciados por sector territorial y tipo de actor (`Admin`, `Gobierno`, `Comunidad`).

---

## 🎨 Identidad Visual (Paleta Pastel)

La interfaz gráfica fue diseñada con una estética moderna, limpia y profesional basada en tonos cálidos y pasteles:
- **Fondo General:** Soft Sand / Linen (`#FAF0E6`) y Warm Ivory (`#FFFDF9`).
- **Acentos Principales:** Peachy Delight (`#FADADD`, `#FFDAB9`) y Soft Mint (`#DDF0DE`).
- **Tipografía y Contraste:** Soft Charcoal (`#2D2A26`) y Warm Muted Gray (`#68615A`) para máxima legibilidad.

---

## 👥 Modelo de Roles y Privilegios (RBAC)

El acceso a las funcionalidades y datos del sistema se encuentra estrictamente delimitado por rol:

| Rol | Alcance Territorial | Permisos Clave |
|---|---|---|
| **Admin** 👑 | Global (Todos los sectores) | Acceso total: registrar incidentes, adherir votos, modificar ciclo de vida, **eliminar registros (inmutable)**, **gestión y creación de usuarios**, y **administración del catálogo dinámico de tipos de incidente**. |
| **Gobierno** 🏛️ | Global (Supervisión distrital) | Consultar todos los incidentes del distrito, registrar nuevos reportes y **modificar estado/prioridad oficial** de las incidencias para su canalización a dependencias públicas. |
| **Comunidad** 🏘️ | Delimitado a su sector de residencia | **Filtrado puro territorial:** solo visualiza incidentes de su sector asignado (ej. Sector Norte, Sector Centro). Puede registrar nuevos reportes y **adherir votos comunitarios (+1 prioridad)**. No puede alterar estados oficiales ni eliminar. |

---

## 🧠 Arquitectura del Sistema (FCIS)

```
proyecto/
├── core/                         # NÚCLEO FUNCIONAL PURO (100% libre de efectos colaterales e I/O)
│   ├── models.py                 # Entidades inmutables (@dataclass(frozen=True)) y Tipos Suma
│   ├── engine.py                 # Reglas de validación anti-spam, pattern matching y transformaciones
│   ├── analisis.py               # HOFs: Closures, filter(), map(), reduce()
│   ├── auth.py                   # Validación pura de credenciales y creación de usuarios
│   └── test_core.py              # Suite de pruebas unitarias del núcleo funcional
│
├── data/                         # CAPA DE PERSISTENCIA (Capa Impura de I/O)
│   ├── file_handler.py           # Lectura/escritura JSON desacoplada con manejo de fallos
│   ├── incidentes.json           # Registro persistente de incidentes ciudadanos
│   ├── usuarios.json             # Catálogo de credenciales y perfiles de usuarios
│   └── tipos_incidente.json      # Catálogo dinámico de categorías de incidencias
│
├── ui/                           # CONCHA IMPERATIVA (Interfaz Gráfica Modular)
│   ├── auth/
│   │   └── login_view.py         # Pantalla de autenticación segura (sin atajos inseguros)
│   ├── dashboard/
│   │   └── main_window.py        # Orquestador del Dashboard y navegación reactiva por pestañas
│   ├── incidents/
│   │   ├── list_view.py          # Tabla Treeview, filtros por sector y métricas
│   │   └── form_view.py          # Formulario reutilizable de registro y edición inmutable
│   ├── admin/
│   │   ├── user_management_view.py   # Panel exclusivo del Admin para creación de usuarios
│   │   └── types_management_view.py  # Panel exclusivo del Admin para extender tipos de incidente
│   ├── metrics/
│   │   └── metrics_view.py           # Tablero de métricas distritales (Admin y Gobierno)
│   ├── state_manager.py          # Gestor de estado mutable, observador reactivo y sesión
│   ├── styles.py                 # Inyección de estilos y paleta de colores pastel
│   └── test_state_manager.py     # Suite de pruebas de integración y gestión de estado
│
├── main.py                       # Punto de entrada de la aplicación
├── requerimientos.txt            # Dependencias oficiales del sistema
├── analisis-funcional.md         # Documento formal de justificación teórica y rúbrica
├── bitacora-ia.md                # Bitácora crítica de decisiones técnicas y uso de IA
└── .gitignore                    # Exclusión de binarios compilados (__pycache__) y temporales
```

---

## ⚙️ Principios Funcionales Aplicados

### 1. Inmutabilidad Estricta
- Las entidades `Usuario`, `Incidente` y `ResultadoValidacion` están decoradas con `@dataclass(frozen=True)`.
- Toda modificación en el ciclo de vida de un incidente o usuario genera una **nueva instancia en memoria** mediante `dataclasses.replace()` o construcción pura, dejando intacto el objeto previo.
- La eliminación de incidentes utiliza la HOF `filter()` para construir una nueva colección sin emplear mutaciones destructivas como `.remove()` o `del`.

### 2. Pattern Matching Estructural
- En `core/engine.py`, la función pura `clasificar_incidente()` utiliza `match/case` para desestructurar la entidad y asignar automáticamente la prioridad base y la secretaría u organismo gubernamental competente (ej. *Secretaría de Movilidad*, *Acueducto*, *Alumbrado Público*).

### 3. Funciones de Orden Superior y Closures
- **Closure (`crear_filtro_por_sector`):** Captura el sector territorial en su ámbito léxico cerrado y retorna un predicado puro evaluable sobre secuencias de incidentes.
- **`filter()`:** Empleado tanto en el filtrado por permisos de rol como en la exclusión no destructiva de registros.
- **`map()`:** Utilizado para proyectar listas de resúmenes estructurados y extraer identificadores numéricos (`extraer_ids_incidentes`).
- **`reduce()`:** Empleado con función lambda pura y elemento neutro `0` para calcular la prioridad acumulada visible sin variables acumuladoras mutables.

### 4. Catálogos Dinámicos (Principio Abierto/Cerrado - OCP)
- Los tipos de incidente no están codificados de manera fija (*hardcoded*). El Administrador puede añadir categorías imprevistas (ej. *Fuga de Gas*, *Árbol Caído*), sincronizando los selectores de los formularios en vivo gracias al patrón Observer.

---

## 🚀 Instalación y Puesta en Marcha

### Prerrequisitos
- **Python 3.10** o superior (probado exhaustivamente en Python 3.13).
- **ttkbootstrap** para los componentes visuales avanzados.

### Pasos de Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/sistema-incidencias-ciudadanas.git
   cd sistema-incidencias-ciudadanas
   ```

2. **Crear y activar un entorno virtual (recomendado):**
   ```bash
   # En Windows
   python -m venv venv
   .\venv\Scripts\activate

   # En Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias requeridas:**
   ```bash
   pip install -r requerimientos.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

---

## 🧪 Ejecución de Pruebas Unitarias

El proyecto cuenta con una cobertura integral de pruebas que validan pureza, inmutabilidad, reglas anti-spam, persistencia y control de accesos por rol:

```bash
python -m unittest core.test_core ui.test_state_manager
```

*Resultado esperado:*
```text
Ran 37 tests in 0.25s - OK
```

---

## 🔐 Cuentas de Acceso Preconfiguradas

Para validar los diferentes niveles de acceso por rol en la pantalla de inicio de sesión:

| Usuario | Contraseña | Rol | Sector Asignado | Alcance |
|---|---|---|---|---|
| `admin` | `admin123` | **Admin** | Todos | Acceso total, gestión de usuarios y tipos de incidente. |
| `gobierno` | `gobierno123` | **Gobierno** | Distrito | Consulta global y modificación oficial de incidentes. |
| `carlos_norte` | `comunidad123` | **Comunidad** | Sector Norte | Reporte y consulta delimitada a Sector Norte (+1 voto). |
| `mariana_centro` | `comunidad123` | **Comunidad** | Sector Centro | Reporte y consulta delimitada a Sector Centro (+1 voto). |
| `jorge_sur` | `comunidad123` | **Comunidad** | Sector Sur | Reporte y consulta delimitada a Sector Sur (+1 voto). |

---

## 📄 Documentación Académica Adicional

- [analisis-funcional.md](analisis-funcional.md): Justificación teórica rigurosa que contrasta el enfoque funcional vs. imperativo, mapas de conceptos y cumplimiento de rúbricas de evaluación.
- [bitacora-ia.md](bitacora-ia.md): Registro transparente de 9 intervenciones críticas donde se corrigieron y rechazaron soluciones automáticas de IA para preservar la integridad arquitectónica.

