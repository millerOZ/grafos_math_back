# Brief de cliente — AbastecePyme

## Cliente y problema

AbastecePyme fabrica productos sencillos y depende de materias primas, proveedores y procesos internos. Cuando un proveedor falla, el equipo no puede identificar rápidamente qué productos se afectan ni el orden correcto de preparación. Necesita visualizar dependencias y detectar configuraciones imposibles.

## Usuarios

- **Responsable de compras:** registra proveedores, insumos y dependencias.
- **Coordinador de producción:** consulta impacto y orden de preparación.

## Alcance

Datos sintéticos de proveedores, insumos, productos y relaciones de dependencia. No incluye inventario real, compras, facturación ni pronósticos. Cada relación debe tener una interpretación clara: “A requiere B” o “B habilita A”; documenten la dirección elegida.

## Feature 1 — Catálogo de dependencias

### Valor de negocio
El equipo puede registrar productos, insumos/proveedores y sus dependencias.

### Debe permitir

- crear/listar elementos con tipo y identificador único;
- registrar dependencias solo entre elementos válidos;
- validar relaciones repetidas y datos mal formados;
- mostrar la red de dependencias mediante API e interfaz mínima;
- justificar dirección de aristas y representación principal.

### Pistas, no receta

Escriban una frase completa para cada arista: “Para producir ___ necesito ___”. Si esa frase deja de tener sentido al invertirla, el grafo debe reflejarlo.

## Feature 2 — Análisis de impacto

### Valor de negocio
Ante la indisponibilidad de un elemento, producción identifica qué productos o procesos quedan afectados.

### Debe permitir

- consultar impacto desde un proveedor/insumo o hacia un producto, según su dirección definida;
- usar un recorrido propio y devolver elementos visitados de manera comprensible;
- diferenciar entre elemento inexistente, elemento sin dependencias y elemento que afecta una cadena;
- explicar en README qué significa “alcanzar” en este negocio.

### Pistas, no receta

La dirección de la relación define si recorren desde causa a consecuencia o al revés. No arreglen una dirección confusa con condicionales: revisen el modelo.

## Feature 3 — Orden y ciclos de producción

### Valor de negocio
El coordinador obtiene un orden válido de preparación o una alerta cuando las dependencias se contradicen.

### Debe permitir

- generar un orden de trabajo válido cuando las dependencias no formen ciclos;
- detectar y reportar un ciclo con información útil;
- no presentar un orden falso si hay contradicción;
- incluir pruebas de aceptación de un caso acíclico y uno cíclico.

### Pistas, no receta

Investiguen grafos dirigidos acíclicos y ordenamiento topológico. Antes de codificar, tracen qué elementos quedan sin requisitos pendientes en cada paso.

## Feature 4 — Tablero de abastecimiento demostrable

### Valor de negocio
El cliente comprende qué falla, qué se afecta y cómo debería organizar producción.

### Debe permitir

- integrar catálogo, impacto y orden/alerta de ciclo;
- visualizar dependencias y destacar la consulta relevante;
- adaptar el cambio de requisito docente;
- ejecutar aceptación para cadena válida, elemento inexistente, dato inválido y ciclo;
- entregar documentación, bitácora IA, video y pitch.

## Criterio de éxito del cliente

Durante la demo se carga una dependencia, se simula una indisponibilidad y se identifican consecuencias. Después se muestra un orden válido o una alerta clara de ciclo.

---

## Disponibilidad e impacto (producto)

Cuando un proveedor o un insumo deja de entregar, la panadería necesita saber qué productos o procesos quedan comprometidos. La API responde esa consulta de negocio.

### Qué significa “alcanzar” en este negocio

Alcanzar significa **“le llega la falla”**. Funciona como fichas de dominó.

Si la Distribuidora de químicos deja de entregar:

```
Distribuidora de químicos  ──►  Conservante  ──►  Ponqué
                                            └──►  Tostadas
```

1. Sin la distribuidora no hay **conservante**: la falla lo alcanza directamente.
2. Sin conservante no se pueden hacer el **ponqué** ni las **tostadas**: la falla los alcanza a través del conservante.
3. El **pan** no usa conservante, así que la falla **no lo alcanza** y se sigue produciendo.

Es decir, lo que se alcanza desde un elemento es todo lo que se cae si ese elemento falla.

La flecha del grafo es `A REQUIERE B` (producto → insumo → proveedor). El impacto se calcula **en contra** de esa flecha: del elemento no disponible hacia quienes lo necesitan.

### Endpoint

```
GET /impacto/{elemento_id}
```

| Caso | HTTP | Significado |
|---|---|---|
| `inexistente` | 404 | El id no está en el catálogo |
| `sin_dependencias` | 200 | Existe, pero nadie depende de él |
| `afecta_cadena` | 200 | Hay elementos alcanzados en `afectados` |

### Piezas del backend

| Archivo | Rol |
|---|---|
| `impacto.py` | Disponibilidad e impacto: distingue los tres casos y arma la respuesta. |
| `recorrido.py` | Recorrido BFS propio sobre la red de dependencias. |
| `main.py` | Expone `GET /impacto/{id}` junto al resto de la API. |
| `models.py` | Contratos de respuesta (`ImpactoResponse`, etc.). |

La interfaz debe consumir `GET /impacto/{id}` y usar `afectados` para resaltar la cadena.

### Cómo probar

```powershell
py -m uvicorn main:app --port 8000
```

Abrir http://127.0.0.1:8000/docs y probar, por ejemplo:

- `/impacto/PRV-MATERIAPRIMA` → afecta cadena
- `/impacto/PRD-PAN` → sin dependencias (nadie requiere al producto)
- `/impacto/NO-EXISTE` → 404


---

## Registrar procesos (catálogo, F1)

Un **proceso** es un paso interno de producción: algo que la empresa *hace*, no que compra
(amasar, fermentar, hornear, empacar). Si se compra es insumo; si se hace es proceso.

```
POST /procesos
{"id": "PRC-HORNEAR", "nombre": "Hornear", "categoria": "Panadería"}
```

Los datos de ejemplo modelan la preparación del **pan tajado** con procesos
(los demás productos siguen yendo directo a sus insumos):

```
Pan tajado → Empacar → Tajar → Hornear → Fermentar → Amasar → Harina, Levadura
                └──► Bolsas de empaque
```

Por eso, si falla la levadura, la falla recorre los cinco procesos hasta llegar al pan
(`GET /impacto/INS-LEVADURA`).

Se crea sin conexiones (201). Si el id ya existe en cualquier capa responde 409; si faltan
datos, 422. `GET /procesos` lista los procesos. Las conexiones se registran luego con `POST /dependencias`.

## Registrar dependencias (catálogo, F1)

```
POST /dependencias
{"origen": "PRD-TOSTADAS", "destino": "PRC-HORNEAR"}
```

Conecta dos elementos **que ya existen** con la relación `origen REQUIERE destino`.

| Situación | HTTP |
|---|---|
| Dependencia creada | 201 (devuelve la arista) |
| `origen` o `destino` no existen | 404 |
| La dependencia ya está registrada | 409 |
| La regla de capas no lo permite, o faltan datos | 422 |

Pares de capas permitidos (`origen → destino`): `producto → insumo`, `producto → proceso`,
`proceso → proceso`, `proceso → insumo`, `insumo → proveedor`.

**Los ciclos no se rechazan.** Con `proceso → proceso` se puede formar un ciclo
(ej. Amasar → Hornear → Amasar). Eso se acepta a propósito: la F3 debe detectarlo y reportarlo.

### Quitar una dependencia

```
DELETE /dependencias/{id}        ej. DELETE /dependencias/e27
```

Quita la arista con ese id (el que devuelve `POST /dependencias` o `GET /aristas`) y la
devuelve (200). Si no existe, 404. Es la forma de **corregir un ciclo**: basta con quitar
una de sus dependencias para que `GET /orden-produccion` vuelva a dar un orden válido.

Los datos viven en memoria: lo que se agrega o quita en Render dura hasta que el servicio
se reinicia. Por eso la demo debe terminar quitando la dependencia que formó el ciclo.

---

## Orden y ciclos de producción (F3)

El coordinador pregunta: *¿en qué orden preparo los procesos?* La API responde con un
orden válido o con una alerta que dice dónde se contradicen las dependencias.

### Qué es un grafo dirigido acíclico (DAG)

- **Dirigido:** cada arista tiene sentido. `A REQUIERE B` no es lo mismo que `B REQUIERE A`
  ("para hornear necesito fermentar" es cierto; "para fermentar necesito hornear", no).
- **Acíclico:** no existe ningún camino que, siguiendo las flechas, vuelva al punto de partida.

Con la flecha `A REQUIERE B`, B tiene que hacerse **antes** que A. Un **orden de trabajo
válido** (orden topológico) es una lista donde cada proceso aparece después de todo lo que
requiere. Ese orden existe **si y solo si** el grafo es acíclico:

- Si es acíclico, siempre hay al menos un proceso sin requisitos pendientes para empezar,
  y al hacerlo se liberan otros; así hasta terminar.
- Si hay un ciclo, sus procesos se esperan entre sí y ninguno puede ir primero. Cualquier
  lista que los incluya rompería alguna dependencia: sería un **orden falso**.

### Traza a mano: qué queda sin requisitos pendientes en cada paso

Es la pista del brief y es exactamente lo que hace el algoritmo de Kahn
(`ordenar_por_etapas` en `topologico.py`):

1. Contar, para cada proceso, cuántos procesos requiere y todavía no están hechos (*pendientes*).
2. La etapa actual son los procesos con 0 pendientes: se pueden hacer ya (y a la vez entre sí).
3. Al terminarlos, se descuenta 1 a cada proceso que los esperaba.
4. Repetir con los que llegaron a 0, hasta que no quede ninguno.

Solo cuentan los requisitos **entre procesos**. Los insumos (harina, levadura, bolsas) los
entrega compras y no se ordenan: se muestran como "Usa ..." en cada paso.

**Caso acíclico — datos de la demo (pan tajado):**

Dependencias: Fermentar requiere Amasar, Hornear requiere Fermentar, Tajar requiere Hornear,
Empacar requiere Tajar.

| Paso | Pendientes antes del paso (Amasar, Fermentar, Hornear, Tajar, Empacar) | Sin pendientes → etapa | Se libera |
|---|---|---|---|
| 1 | 0, 1, 1, 1, 1 | **Amasar** | Fermentar |
| 2 | —, 0, 1, 1, 1 | **Fermentar** | Hornear |
| 3 | —, —, 0, 1, 1 | **Hornear** | Tajar |
| 4 | —, —, —, 0, 1 | **Tajar** | Empacar |
| 5 | —, —, —, —, 0 | **Empacar** | — (pan listo) |

Se ordenaron los 5 procesos: `etapas = [[Amasar], [Fermentar], [Hornear], [Tajar], [Empacar]]`.
Si dos procesos llegan a 0 en el mismo paso (por ejemplo Amasar y un Etiquetar que no
requiere nada), quedan en la misma etapa: se pueden hacer a la vez.

**Caso cíclico — se agrega `PRC-AMASAR → PRC-HORNEAR`** ("para amasar necesito hornear"):

| Paso | Pendientes (Amasar, Fermentar, Hornear, Tajar, Empacar) | Sin pendientes → etapa |
|---|---|---|
| 1 | **1**, 1, 1, 1, 1 | *ninguno* |

El recorrido se detiene sin haber ordenado nada: es la señal de que hay un ciclo. Pero la
traza no dice **cuál**: Tajar y Empacar también quedaron bloqueados y no forman parte del
ciclo, solo dependen de él. Por eso se usa un segundo algoritmo para ubicarlo (siguiente sección).

### Qué se considera un ciclo

Un ciclo es una cadena de procesos `P1 requiere P2, P2 requiere P3, …, Pn requiere P1`:
cada uno espera al siguiente y el último espera al primero. Casos:

| Situación | Ejemplo | ¿Ciclo? |
|---|---|---|
| Cadena que se cierra | Amasar → Hornear → Fermentar → Amasar | Sí, de 3 procesos |
| Dependencia mutua | Glasear → Decorar → Glasear | Sí, de 2 procesos |
| Proceso que se requiere a sí mismo | Tajar → Tajar | Sí, de 1 proceso ("esa dependencia sobra") |
| Dos caminos que llegan al mismo proceso | Empacar requiere Tajar y Etiquetar; los dos requieren Hornear | **No**: es un rombo; ningún camino vuelve al inicio |
| Proceso que depende de un ciclo | Tajar requiere Hornear (que está en el ciclo) | **No** está en el ciclo; queda **bloqueado** |

Cómo se detecta y reporta (`buscar_ciclos` en `topologico.py`):

1. **Tarjan** agrupa los procesos en *componentes fuertemente conexas*: grupos donde desde
   cualquier proceso se puede llegar a cualquier otro siguiendo las flechas. Un grupo con
   2 o más procesos, o un proceso que se requiere a sí mismo, contiene un ciclo.
2. De cada grupo se reporta **un** ciclo: el más corto que pasa por su primer proceso (BFS
   dentro del grupo). Así el coordinador ve la contradicción mínima que tiene que romper.
3. Para cada producto se revisa si usa algún proceso de un ciclo (directa o indirectamente).
   Si lo usa, queda sin orden (`etapas: null`) y `bloqueado_por` dice qué ciclo lo bloquea;
   si no, conserva su orden.

### Por qué un ciclo solo puede aparecer en `proceso → proceso`

La regla de capas (`REGLAS_CAPAS` en `data.py`) permite estas dependencias:

| Origen REQUIERE destino | Nivel origen → nivel destino |
|---|---|
| producto → insumo | 3 → 1 |
| producto → proceso | 3 → 2 |
| proceso → proceso | 2 → 2 |
| proceso → insumo | 2 → 1 |
| insumo → proveedor | 1 → 0 |

Si se numeran las capas (proveedor 0, insumo 1, proceso 2, producto 3), **ninguna arista
sube de nivel**: todas bajan, salvo `proceso → proceso`, que se queda en el mismo nivel.

Un ciclo vuelve al elemento donde empezó, así que termina en el mismo nivel en el que
arrancó. Si alguna de sus aristas bajara de nivel, otra tendría que subir para compensar, y
eso no existe. Por lo tanto **todas las aristas de un ciclo son `proceso → proceso`**.

En lenguaje de negocio: un proveedor nunca necesita un insumo, un insumo nunca necesita un
producto y nada necesita un producto terminado; la única forma de "volver atrás" es entre
pasos internos. Por eso `orden.py` solo analiza las aristas entre procesos, y
`POST /dependencias` no rechaza ciclos: los acepta para que esta consulta los detecte y reporte.

### Endpoint

```
GET /orden-produccion
```

| Caso | HTTP | Significado |
|---|---|---|
| `sin_procesos` | 200 | No hay procesos registrados |
| `orden_valido` | 200 | `etapas` (todos los procesos) y `planes` (orden por producto) |
| `ciclo` | 200 | `ciclos` trae los ids y una frase por ciclo; `etapas` es `null` |

**No se presenta un orden falso:** con un ciclo, `etapas` es `null` y los productos que usan
el ciclo traen `etapas: null` y `bloqueado_por` (índices en `ciclos`). Los productos que no
lo usan conservan su orden.

### Piezas del backend

| Archivo | Rol |
|---|---|
| `topologico.py` | Algoritmos propios: Kahn por etapas, Tarjan (componentes fuertemente conexas) y ciclo más corto por BFS. El front consume el resultado con `useOrdenProduccion`. |
| `orden.py` | Arma la respuesta de negocio: casos, planes por producto y mensajes. |
| `test_orden.py` | Pruebas: caso acíclico, cíclico, autociclo, ciclo que bloquea solo a algunos productos y aceptación sobre los datos de la demo. |

### Cómo probar

- `GET /orden-produccion` → `orden_valido` (Amasar, Fermentar, Hornear, Tajar, Empacar)
- `POST /dependencias {"origen": "PRC-AMASAR", "destino": "PRC-HORNEAR"}` y de nuevo
  `GET /orden-produccion` → `ciclo` (Amasar necesita Hornear, Hornear necesita Fermentar…)
- `DELETE /dependencias/<id devuelto por el POST>` y de nuevo `GET /orden-produccion` →
  `orden_valido`: la contradicción quedó corregida.
