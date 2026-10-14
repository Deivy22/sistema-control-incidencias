# Análisis funcional del Sistema de Control de Incidencias Ciudadanas

## 1. Problema que resuelve la aplicación

El proyecto implementa un **Sistema de Control de Incidencias Ciudadanas**. Su propósito es registrar, consultar, validar, clasificar, modificar y eliminar reportes urbanos como choques, fallas eléctricas y problemas de alcantarillado.

La aplicación separa el acceso según tres roles:

- **Admin:** administra globalmente los incidentes y los catálogos del sistema.
- **Gobierno:** consulta y gestiona incidentes con alcance territorial global.
- **Comunidad:** reporta incidentes y consulta los que pertenecen a su sector.

La separación de roles evita que cualquier usuario modifique información fuera de sus permisos. Además, las validaciones anti-spam rechazan descripciones demasiado cortas, repetitivas o con poca diversidad de caracteres. La clasificación asigna una prioridad base y un departamento responsable, lo que permite priorizar problemas urbanos relevantes y dirigirlos a la entidad correspondiente.

Desde la perspectiva funcional, la aplicación transforma datos de entrada en nuevos estados válidos, dejando la persistencia y la interacción visual fuera del núcleo de reglas de negocio.

## 2. Estructuras de datos utilizadas

El modelado principal está en [`core/models.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/models.py).

### Entidades inmutables

`Usuario` se declara como:

```python
@dataclass(frozen=True)
class Usuario:
    id: int
    nombre: str
    rol: RolUsuario
    sector: str = ""
```

`Incidente` se declara de forma equivalente con sus datos de identificación, sector, descripción, tipo, estado y nivel de prioridad.

El uso de `@dataclass` evita escribir manualmente métodos habituales como `__init__`, `__repr__` y la comparación por valor. El parámetro `frozen=True` agrega una garantía esencial para el paradigma funcional: una instancia creada no puede modificarse mediante asignación de atributos. Por ejemplo, una actualización no se hace con `incidente.estado = ...`, sino creando otra instancia mediante `dataclasses.replace`.

El mismo principio se aplica a `ResultadoValidacion` en [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:44), también declarado con `@dataclass(frozen=True)`. Este tipo representa un resultado enriquecido con `es_valido` y `motivo`, en lugar de limitar la validación a un booleano sin contexto.

### Uniones y literales

El archivo [`core/models.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/models.py:23) define dominios restringidos mediante `Union` y `Literal`:

- `RolUsuario` en las líneas 23-27: `"Comunidad"`, `"Gobierno"` o `"Admin"`.
- `TipoIncidente` en las líneas 31-35: `"Choque"`, `"FallaElectrica"` o `"Alcantarillado"`.
- `EstadoIncidente` en las líneas 38-42: `"Reportado"`, `"EnProceso"`, `"Resuelto"` o `"Descartado"`.

Estas declaraciones funcionan como tipos suma aproximados en Python: documentan las variantes permitidas y permiten que las funciones operen sobre un dominio conocido. En una revisión estricta, las variantes adicionales que `clasificar_incidente` contempla (`"Infraestructura"` y `"Seguridad Pública"`) deberían incorporarse también a `TipoIncidente` o retirarse del `match` para mantener alineado el modelo estático con el comportamiento.

## 3. Dónde se aplicó Unidad 1

La Unidad 1 se aplica en los siguientes puntos:

### Funciones de orden superior

- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:24): `crear_filtro_por_sector` retorna una función predicado.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:97): `filter` recibe el predicado creado por la closure.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:100): `map` recibe `_formatear_resumen_incidente`.
- [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:295): `filtrar_por_permisos` define una función local (`pertenece_a_sector_usuario`, líneas 319-322) como predicado de `filter`.

Una función de orden superior es aquella que recibe funciones como argumentos o retorna funciones como valores. Por eso `crear_filtro_por_sector` y el uso de `filter`/`map` constituyen aplicaciones directas del concepto.

### Modelado de datos

- [`core/models.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/models.py:50): `Usuario` con `@dataclass(frozen=True)`.
- [`core/models.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/models.py:66): `Incidente` con `@dataclass(frozen=True)`.
- [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:44): `ResultadoValidacion` con `@dataclass(frozen=True)`.
- [`core/models.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/models.py:23): uniones de literales para restringir roles, tipos y estados.

### Pattern matching estructural real

La aplicación de `match/case` se encuentra principalmente en [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:170), dentro de `clasificar_incidente`:

```python
match incidente:
    case Incidente(tipo_incidente="Choque") | "Choque":
        ...
```

Las líneas 171-184 usan **class patterns** como `Incidente(tipo_incidente="Choque")`, que inspeccionan el tipo y el atributo de la instancia, junto con patrones literales y patrones OR (`|`). La línea 186 (`case Incidente()`) reconoce cualquier instancia de `Incidente` no capturada previamente y la línea 189 (`case _`) funciona como caso de respaldo.

También aparece `match` en [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:57), en `_etiqueta_prioridad`, para clasificar niveles concretos y usar una guarda (`case p if p >= 4`).

Esto es pattern matching estructural válido de Python 3.10 o superior, no una simple sustitución textual de `if/elif`: el patrón puede descomponer la estructura de un `Incidente` y examinar sus atributos declarativamente.

### Comparación: Enfoque funcional vs. imperativo

En cumplimiento con los contenidos obligatorios de la Unidad 1 de la rúbrica, el proyecto contrasta de manera explícita el paradigma funcional frente al imperativo clásico:

- **Mutación de estado vs. Transformaciones no destructivas:** En un modelo imperativo convencional, una modificación se realizaría mediante asignación directa sobre atributos mutables (`incidente.estado = "EnProceso"`) o la eliminación se haría mutando la colección *in-situ* (`lista.remove(incidente)` o `del lista[indice]`). En nuestro núcleo funcional, las entidades son inmutables (`@dataclass(frozen=True)`), las actualizaciones generan copias persistentes con `dataclasses.replace` ([`core/engine.py:329`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:329)) y la eliminación produce una nueva colección materializada a través de `filter` ([`core/engine.py:365`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:365)), garantizando que el estado previo permanezca inalterado.
- **Acumuladores iterativos vs. Plegado declarativo:** En lugar de implementar bucles `for` imperativos con variables de estado acumulativas reasignadas continuamente (`total = 0; for x in lista: total += x.prioridad`), se utiliza `reduce` ([`core/analisis.py:110`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:110)) con una función lambda pura y elemento neutro `0`, eliminando el estado mutable intermedio.
- **Estructura monolítica con efectos colaterales vs. Núcleo Funcional aislado:** Mientras que un diseño imperativo acopla las decisiones lógicas a los callbacks de eventos Tkinter y a la lectura directa de archivos en disco, aquí la lógica reside íntegramente en funciones puras sin dependencias del entorno exterior.

## 4. Dónde se aplicó Unidad 2

### `lambda`

Las expresiones lambda se utilizaron en transformaciones breves:

- [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:378): `lambda inc: inc.id != id_a_borrar` como predicado de eliminación con `filter`.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:125): lambda acumuladora de `reduce`.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:145): `lambda inc: inc.id` como proyección de `map`.
- [`ui/auth/login_view.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/ui/auth/login_view.py:147), líneas 152-153: lambdas breves como callbacks de eventos Tkinter.

En cambio, la validación anti-spam de [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:212) usa una función nombrada. Es una decisión correcta: necesita varias etapas, variables intermedias, retornos tempranos y mensajes de error diferentes. Una lambda de Python solo admite una expresión y no puede contener naturalmente sentencias, `return` temprano, asignaciones normales, bloques `try/except` ni una secuencia de guard clauses.

### Inmutabilidad

La inmutabilidad se aplica mediante:

- `@dataclass(frozen=True)` en los modelos.
- `replace(...)` en [`adherir_voto_incidente`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:140) y [`actualizar_incidente`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:329).
- `filter` y construcción de una nueva lista en [`eliminar_incidente_por_id`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:365).
- Transformaciones que no alteran las secuencias recibidas en `core/analisis.py`.

La implementación del núcleo no modifica los objetos `Incidente` ni las colecciones de entrada. Estrictamente, las listas retornadas siguen siendo contenedores mutables desde el exterior; la garantía central es que las funciones no mutan sus entradas y que las entidades de dominio son frozen.

### `filter`, `map` y `reduce`

- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:97): `filter(predicado_sector, incidentes)` conserva incidentes del sector.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:100): `map(_formatear_resumen_incidente, incidentes_filtrados)` proyecta incidentes a textos.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:124): `reduce` suma los niveles de prioridad con acumulador inicial `0`.
- [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:145): `map` extrae los identificadores.
- [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:322): `filter` implementa el filtrado por sector y permisos.
- [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:378): `filter` implementa la eliminación no destructiva.

## 5. Partes puras e impuras

### Funciones puras de `core/`

Las funciones de [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py) son puras cuando:

- dependen exclusivamente de sus parámetros;
- no leen ni escriben archivos;
- no interactúan con Tkinter;
- no modifican objetos recibidos;
- retornan resultados determinados por sus entradas.

En esta categoría están `validar_descripcion`, `es_descripcion_valida`, `adherir_voto_incidente`, `clasificar_incidente`, `validar_tipo_incidente`, `validar_incidente_complejo`, `filtrar_por_permisos`, `actualizar_incidente` y `eliminar_incidente_por_id`.

En [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py) son puras `crear_filtro_por_sector`, `_etiqueta_prioridad`, `_formatear_resumen_incidente`, `filtrar_y_resumir_por_sector`, `calcular_prioridad_total` y `extraer_ids_incidentes`. La closure no tiene estado global mutable; captura un `str` normalizado e inmutable.

En [`core/auth.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/auth.py:14) es pura `autenticar_usuario`: evalúa credenciales comparando valores de texto contra una colección inmutable recibida por argumento (`base_datos`), retornando de forma determinista una nueva instancia inmutable de `Usuario` o `None`, sin realizar operaciones de I/O en disco ni alterar variables globales.

### Funciones impuras de `data/`

En [`data/file_handler.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/data/file_handler.py), `guardar_incidentes`, `cargar_incidentes`, `cargar_usuarios`, `guardar_usuarios`, `cargar_tipos_incidente` y `guardar_tipos_incidente` son impuras porque dependen del sistema de archivos. Usan `Path.exists`, `mkdir`, `open`, `json.load`, `json.dump` y logging. Una carga puede retornar valores distintos con los mismos argumentos si otro proceso cambia el archivo.

`obtener_datos_semilla` es una excepción localmente pura: construye datos deterministas en memoria. También son puras, consideradas de forma aislada, las conversiones de serialización y reconstrucción; la función que las contiene es impura cuando además realiza I/O.

### Funciones impuras de `ui/`

La carpeta [`ui/`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/ui) contiene callbacks de eventos, construcción de widgets, actualización de variables Tkinter, diálogos y renderizado. Por ejemplo, `mostrar_vista_login`, `mostrar_vista_principal`, los manejadores `_on_*` y `refrescar_ui` interactúan con la pantalla y con el ciclo de eventos, por lo que son impuros.

[`ui/state_manager.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/ui/state_manager.py) coordina sesión, callbacks, persistencia y estado de la aplicación. Aunque usa transformaciones funcionales como `filter`, su responsabilidad global incluye cambiar el estado de la interfaz y solicitar lecturas o escrituras, por lo que no debe confundirse con el núcleo puro.

## 6. Efectos secundarios existentes

Los efectos secundarios no se eliminaron artificialmente: se **aislaron intencionalmente** en los bordes de la aplicación.

En [`data/file_handler.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/data/file_handler.py), la lectura y escritura de JSON constituyen I/O:

- `cargar_incidentes` lee el archivo y puede crear datos persistentes si no existe.
- `guardar_incidentes` serializa y escribe incidentes.
- `cargar_usuarios` y `guardar_usuarios` acceden a credenciales y perfiles.
- `cargar_tipos_incidente` y `guardar_tipos_incidente` mantienen el catálogo dinámico.

En la capa visual, Tkinter produce otros efectos secundarios: crea ventanas, modifica widgets, actualiza `Treeview`, muestra diálogos, recibe eventos y ejecuta el bucle principal de la interfaz. Estos efectos están en `ui/`, no en las reglas de `core/`.

Este diseño sigue el patrón **Functional Core, Imperative Shell**: el núcleo calcula valores y la concha imperativa ejecuta I/O, renderiza y coordina eventos.

## 7. Manejo inmutable del estado

La eliminación se implementa en [`core/engine.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:365):

```python
return list(filter(lambda inc: inc.id != id_a_borrar, lista_incidentes))
```

`filter` conserva los elementos cuyo identificador no coincide y `list` materializa una nueva colección. No se usa `.remove()`, `.pop()` ni `del`, por lo que `lista_incidentes` permanece intacta. La operación es una transformación no destructiva:

```text
lista_nueva = eliminar(lista_original, id)
```

La modificación está en [`actualizar_incidente`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/engine.py:329):

```python
return replace(incidente_original, **cambios)
```

`dataclasses.replace` crea otra instancia conservando los campos que no se modificaron. Como `Incidente` es `frozen`, el objeto original no puede alterarse mediante asignación de atributos.

Este enfoque permite que el estado anterior siga existiendo y que el nuevo estado sea un valor explícito. Reduce el aliasing, facilita las pruebas y evita que una vista de Tkinter observe cambios ocultos producidos por otra parte del programa. La capa visual o el `StateManager` pueden reemplazar la referencia que utilizan y persistir el nuevo valor, pero la transformación central sigue siendo pura.

## 8. Closure implementado

La closure se encuentra en [`core/analisis.py`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:24):

```python
def crear_filtro_por_sector(sector: str) -> Callable[[Incidente], bool]:
    sector_objetivo = sector.strip().casefold()

    def pertenece_a_sector(incidente: Incidente) -> bool:
        return incidente.sector.strip().casefold() == sector_objetivo

    return pertenece_a_sector
```

`sector_objetivo` pertenece al ámbito local de `crear_filtro_por_sector`, pero es una variable libre para `pertenece_a_sector`. Python conserva su valor en el entorno léxico de la función retornada, incluso después de que la función externa termina.

Por ejemplo:

```python
filtro_norte = crear_filtro_por_sector(" Norte ")
```

El closure conserva `"norte"` normalizado. Después puede utilizarse como predicado independiente:

```python
list(filter(filtro_norte, incidentes))
```

La utilidad es fabricar filtros especializados sin duplicar funciones ni recurrir a variables globales. En [`filtrar_y_resumir_por_sector`](C:/Users/HOME/Documents/deivy/programacion_funcional/proyecto/core/analisis.py:76), la closure se pasa a `filter` y luego los resultados se proyectan con `map`. La prueba correspondiente verifica que el resultado sea invocable y que posea `__closure__`.

## 9. Qué partes sugirió la IA (Antigravity/Gemini)

Durante el desarrollo, la IA Antigravity/Gemini sugirió elementos iniciales de implementación que luego fueron revisados técnicamente:

- la sintaxis base para construir la interfaz con `Tkinter` y organizar ventanas, formularios, tablas, botones y callbacks;
- las expresiones `lambda` iniciales para callbacks de eventos y transformaciones cortas;
- el esqueleto de los algoritmos de filtrado;
- la estructura inicial de operaciones con `map`, `filter` y `reduce`;
- el esqueleto de la interfaz visual y la conexión preliminar entre acciones de usuario y operaciones del sistema.

Estas sugerencias funcionaron como punto de partida, no como sustituto del diseño arquitectónico ni de la verificación conceptual. El código final se ajustó a los requisitos de pureza, inmutabilidad, tipos y separación de responsabilidades.

## 10. Qué se corrigió o rechazó de la IA

### a) Rechazo del diseño monolítico inicial

Se rechazó el diseño inicial monolítico porque mezclaba interfaz, reglas de negocio, estado y persistencia en un mismo módulo. Se forzó una arquitectura multicapa:

- `core/`: modelos y lógica de negocio pura;
- `data/`: persistencia y operaciones de archivos;
- `ui/`: Tkinter, eventos, sesión y renderizado.

Esta decisión evita que una regla como validar una descripción dependa de una ventana o de un archivo JSON. También permite probar el núcleo en aislamiento.

### b) Rechazo de un Login simulado inseguro

Se rechazó un sistema de Login simulado e inseguro basado únicamente en datos embebidos en la interfaz o en validaciones superficiales. La autenticación y los perfiles se integraron con una capa de estado y con la carga de usuarios desde `data/`, manteniendo la interfaz como consumidora del resultado y no como responsable de la regla de autenticación.

Esto no convierte automáticamente el sistema en una solución de seguridad de producción: para ese contexto todavía serían necesarios almacenamiento seguro de contraseñas, hashing, gestión de sesiones y controles de acceso robustos. La corrección aplicada corresponde al alcance académico y evita presentar un mecanismo visual simulado como autenticación real.

### c) Corrección de borrado y modificación impuros

Se corrigieron funciones impuras que la IA intentó utilizar para borrar o modificar datos directamente. En lugar de mutar listas con `.remove()` o modificar atributos de un incidente, se impuso:

- `filter` para producir una lista sin el identificador eliminado;
- `dataclasses.replace` para producir una copia modificada;
- `@dataclass(frozen=True)` para impedir mutaciones de las entidades;
- actualización explícita de la referencia en la capa coordinadora;
- persistencia separada después de calcular el nuevo estado.

Así, la IA puede proponer la operación, pero la implementación final debe demostrar por qué no introduce efectos de estado ocultos.

## 11. Qué se aprendió técnicamente

El proyecto muestra que la programación funcional en Python no consiste en eliminar toda interacción con el mundo exterior, sino en ubicarla correctamente. Las reglas de negocio se expresan como funciones puras que reciben valores y retornan valores nuevos. La lectura y escritura de JSON, la autenticación coordinada, los callbacks y el renderizado de Tkinter quedan confinados a las capas externas.

El manejo inmutable del estado evita que una modificación realizada desde una pantalla cambie silenciosamente un objeto compartido por otra vista. `filter`, `map`, `reduce`, closures, `match/case` y `dataclass(frozen=True)` permiten declarar transformaciones y hacer explícitas las variantes del dominio.

Esta separación hace el código más predecible: para los mismos argumentos, el núcleo produce el mismo resultado. También facilita el testing, como se observa en `core/test_core.py` y `ui/test_state_manager.py`, donde se comprueban pureza, inmutabilidad, closures, filtrado, reducción, permisos y actualización de incidentes sin depender necesariamente de la interacción manual con la ventana.

La conclusión arquitectónica es que aislar los efectos secundarios y tratar el estado como valores reemplazables reduce los bugs de estado ocultos en la interfaz gráfica, mejora la trazabilidad de cada operación y permite modificar la persistencia o la presentación sin reescribir las reglas centrales del sistema.
