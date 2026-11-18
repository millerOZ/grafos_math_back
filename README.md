# AbastecePyme — Backend (grafos_math_back)

API en FastAPI que modela la red de abastecimiento de la panadería **Bake & Brew** como un
grafo dirigido y responde tres preguntas de negocio: qué depende de qué, qué se afecta si
algo falla y en qué orden se prepara la producción.

- Producción: https://grafos-math-back.onrender.com (documentación interactiva en `/docs`)
- Front que la consume: [grafos_math_frontend](../grafos_math_frontend/README.md) — https://grafos-math.netlify.app
- Brief del cliente: [05-brief-abastecepyme.md](../05-brief-abastecepyme.md)

## Contenido

1. [Propósito](#propósito)
2. [Instalación](#instalación)
3. [Ejecución](#ejecución)
4. [Endpoints](#endpoints)
5. [Decisiones de diseño](#decisiones-de-diseño) — incluye [complejidad y estructuras de datos](#9-complejidad-aproximada-y-estructuras-de-datos)

---

## Propósito

AbastecePyme fabrica productos sencillos que dependen de materias primas, proveedores y
procesos internos. Cuando un proveedor falla, el equipo no sabe rápido qué productos se
afectan ni en qué orden preparar. Esta API cubre las features del brief:

| Feature | Qué resuelve | Dónde |
|---|---|---|
| F1 — Catálogo de dependencias | Crear y listar proveedores, insumos, procesos, productos y sus dependencias, con validación de datos repetidos y mal formados | `main.py`, `models.py`, `ids.py`, `data.py` |
| F2 — Análisis de impacto | Si un elemento no está disponible, qué queda comprometido y por qué camino (BFS propio) | `impacto.py`, `recorrido.py` |
| F3 — Orden y ciclos | Un orden de preparación válido o una alerta clara si las dependencias se contradicen (Kahn + Tarjan propios) | `orden.py`, `topologico.py` |
| F4 — Tablero demostrable | `GET /grafo` para cargar todo de una vez, `POST /demo/reset` para empezar la demo siempre igual y aceptación de los cuatro casos del brief | `main.py`, `data.py`, `test_aceptacion.py` |

**Usuarios:** el *responsable de compras* registra proveedores, insumos y dependencias; el
*coordinador de producción* consulta impacto y orden de preparación.

**Alcance:** datos sintéticos. No incluye inventario real, compras, facturación ni
pronósticos, ni autenticación de usuarios.

### Archivos

| Archivo | Rol |
|---|---|
| `main.py` | App FastAPI, CORS y todos los endpoints. |
| `models.py` | Contratos de entrada y salida (pydantic). Aquí se valida el dato inválido. |
| `ids.py` | Regla única del formato de ids (`PREFIJO-NOMBRE`). |
| `data.py` | Datos de ejemplo en memoria, regla de capas y helpers (agregar, buscar, reiniciar). |
| `recorrido.py` | BFS propio sobre la red. |
| `impacto.py` | Casos de impacto y armado de la respuesta. |
| `topologico.py` | Kahn por etapas, Tarjan y ciclo más corto por BFS. |
| `orden.py` | Casos de orden de producción, planes por producto y mensajes. |
| `test_aceptacion.py` | Aceptación de la F4: cadena válida, elemento inexistente, dato inválido, ciclo y el guion de la demo. |
| `test_*.py` | Pruebas unitarias (`unittest`): dependencias, recorrido, orden, ids y reset. |
| `docs/` | Bitácoras de IA en PDF. |

---

## Instalación

Requisitos: **Python 3.9 o superior**.

```bash
cd grafos_math_back
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # fastapi y uvicorn (pydantic v2 viene con fastapi)
```

---

## Ejecución

```bash
uvicorn main:app --reload --port 8000
```

- API: http://127.0.0.1:8000
- Documentación interactiva (Swagger): http://127.0.0.1:8000/docs

Para habilitar el reinicio de la demo en local (ver [Clave del reset](#clave-del-reset)):

```bash
DEMO_RESET_TOKEN=una-clave uvicorn main:app --reload --port 8000
```

El front local (`http://localhost:5173` y `http://127.0.0.1:5173`) y el desplegado en
Netlify ya están permitidos en CORS.

### Pruebas

```bash
python -m unittest                    # 67 pruebas
python -m unittest test_aceptacion -v  # solo la aceptación de la F4 (17 pruebas)
```

Las pruebas llaman directamente a las funciones de los endpoints y aíslan el grafo en
cada caso (`GrafoAisladoTestCase`), así que no necesitan levantar el servidor.

#### Aceptación de la F4

`test_aceptacion.py` cubre los cuatro casos que pide el brief. Cada prueba parte de los datos
de la demo (`reiniciar_grafo`) y restaura el grafo al terminar.

| Caso del brief | Clase | Qué se verifica |
|---|---|---|
| Cadena válida | `TestCadenaValida` | Se carga `PRD-TOSTADAS → PRC-HORNEAR`; queda en `GET /grafo` con el id del back. Si falla `INS-LEVADURA`, la falla llega a los 5 procesos, al pan y a las tostadas (no a galletas ni ponqué), y cada paso del `camino` es una dependencia real. `PRD-PAN` da `sin_dependencias`. El orden es válido y respeta la nueva dependencia. |
| Elemento inexistente | `TestElementoInexistente` | 404 en `GET /impacto/PRV-NO-EXISTE`, en `POST /dependencias` con origen o destino inexistente, al crear un insumo o producto que referencia algo inexistente y en `DELETE /dependencias/e999`. El grafo no cambia (un producto no se crea a medias). |
| Dato inválido | `TestDatoInvalido` | 422 `id_invalido` en impacto para ids mal formados (nunca 404). Los modelos de entrada rechazan id vacío, con espacios, con prefijo de otra capa, nombre vacío y producto sin insumos (FastAPI responde 422). 422 por regla de capas (`PRV-QUIM → PRD-PAN`) y 409 por dependencia o id repetidos. El grafo no cambia. |
| Ciclo | `TestCiclo` | Se carga `PRC-AMASAR → PRC-HORNEAR`: caso `ciclo`, `etapas: null` (sin orden falso), ciclo `[Amasar, Hornear, Fermentar]` con su frase, el pan bloqueado por el ciclo 0 y el resto de productos sin bloquear. El impacto no entra en bucle. Al quitar la dependencia vuelve el orden válido. |
| Criterio de éxito del cliente | `TestGuionDeLaDemo` | El guion completo en orden: cargar dependencia → simular la falla → consecuencias → orden válido → dependencia contradictoria → alerta de ciclo → quitarla → orden válido → `POST /demo/reset` deja el grafo como al inicio. |

Para comprobar que estas pruebas detectan errores reales, se dañó el código a propósito y se
vio que fallan: ignorar los ciclos (`TestCiclo`), recorrer el impacto en la dirección de la
flecha (`TestCadenaValida`), responder 200 a un elemento inexistente (`TestElementoInexistente`)
y desactivar la regla de capas (`TestDatoInvalido`).

### Despliegue

En Render, como *Web Service* de Python:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variable de entorno: `DEMO_RESET_TOKEN` (opcional; sin ella el reset queda deshabilitado).

---

## Endpoints

| Método y ruta | Para qué | Respuestas |
|---|---|---|
| `GET /` | Comprobar que la API responde | 200 |
| `GET /grafo` | Todos los nodos y aristas en una sola respuesta | 200 |
| `GET /productos` · `/procesos` · `/insumos` · `/proveedores` | Nodos de una capa | 200 |
| `GET /aristas` | Todas las dependencias | 200 |
| `POST /proveedores` | Crear proveedor | 201 · 409 · 422 |
| `POST /insumos` | Crear insumo y su dependencia con el proveedor | 201 · 404 · 409 · 422 |
| `POST /productos` | Crear producto y sus dependencias con insumos | 201 · 404 · 409 · 422 |
| `POST /procesos` | Crear proceso interno (sin conexiones) | 201 · 409 · 422 |
| `POST /dependencias` | Registrar `origen REQUIERE destino` | 201 · 404 · 409 · 422 |
| `DELETE /dependencias/{id}` | Quitar una dependencia (para romper un ciclo) | 200 · 404 |
| `GET /impacto/{id}` | Qué se afecta si ese elemento falla | 200 · 404 · 422 |
| `GET /orden-produccion` | Orden de preparación o ciclos | 200 |
| `POST /orden-produccion/restaurar` | Volver a un orden válido quitando solo las dependencias agregadas que forman ciclos | 200 |
| `POST /demo/reset` | Volver a los datos de `data.py` (requiere clave) | 200 · 403 |

### Crear elementos

```http
POST /proveedores   {"id": "PRV-MOLINO", "nombre": "Molino", "categoria": "Materia prima"}
POST /insumos       {"id": "INS-AVENA", "nombre": "Avena", "proveedor_id": "PRV-MOLINO"}
POST /productos     {"id": "PRD-GALLETA-AVENA", "nombre": "Galleta de avena", "insumo_ids": ["INS-AVENA"]}
POST /procesos      {"id": "PRC-HORNEAR", "nombre": "Hornear", "categoria": "Panadería"}
```

`categoria` es opcional. `id` y `nombre` son obligatorios.

- **409** si el `id` ya existe en cualquier capa.
- **404** si `proveedor_id` o algún `insumo_ids` no existen.
- **422** si un dato está mal formado (ver [Formato de los ids](#6-formato-de-los-ids-un-solo-criterio-para-el-dato-inválido)),
  si `insumo_ids` está vacío, o si la referencia es de otra capa (por ejemplo, un
  `proveedor_id` que es un insumo).

Un **proceso** es un paso interno: algo que la empresa *hace*, no que compra (amasar,
fermentar, hornear, empacar). Si se compra es insumo; si se hace es proceso. Se crea sin
conexiones y luego se conecta con `POST /dependencias`.

### Registrar y quitar dependencias

```http
POST /dependencias   {"origen": "PRD-TOSTADAS", "destino": "PRC-HORNEAR"}
DELETE /dependencias/e27
```

| Situación | HTTP |
|---|---|
| Dependencia creada | 201 (devuelve la arista con su `id`) |
| `origen` o `destino` mal formados | 422 |
| `origen` o `destino` no existen | 404 |
| La dependencia ya está registrada | 409 |
| La regla de capas no la permite (ej. proveedor → producto) | 422 |

Pares permitidos (`origen → destino`): `producto → insumo`, `producto → proceso`,
`proceso → proceso`, `proceso → insumo`, `insumo → proveedor`.

`DELETE` quita la arista con ese id (el que devuelve el POST o `GET /aristas`) y la devuelve.
Es la forma de **corregir un ciclo**.

### Impacto

```http
GET /impacto/{elemento_id}
```

| `caso` | HTTP | Significado |
|---|---|---|
| `id_invalido` | 422 | Id vacío, con espacios o sin formato `PREFIJO-NOMBRE`. No se busca en el catálogo |
| `inexistente` | 404 | Buen formato, pero no está en el catálogo |
| `sin_dependencias` | 200 | Existe, pero nadie depende de él |
| `afecta_cadena` | 200 | `afectados` trae cada elemento alcanzado con su `nivel` y su `camino` desde el origen; `visitados`, el orden del recorrido |

Ejemplos con los datos de la demo:

- `/impacto/PRV-MATERIAPRIMA` → `afecta_cadena`
- `/impacto/INS-LEVADURA` → recorre los cinco procesos del pan tajado hasta llegar al pan
- `/impacto/PRD-PAN` → `sin_dependencias` (nadie requiere un producto terminado)
- `/impacto/PRD-NO-EXISTE` → 404
- `/impacto/prv-x` → 422

### Orden de producción

```http
GET /orden-produccion
```

| `caso` | Significado |
|---|---|
| `sin_procesos` | No hay procesos registrados |
| `orden_valido` | `etapas` (todos los procesos) y `planes` (orden por producto) |
| `ciclo` | `ciclos` trae los ids y una frase por ciclo; `etapas` es `null` |

Siempre responde 200: un ciclo no es un error de la petición, es el resultado del análisis.
Con un ciclo, los productos que lo usan traen `etapas: null` y `bloqueado_por` (índices en
`ciclos`); los que no lo usan conservan su orden.

Para probarlo:

1. `GET /orden-produccion` → `orden_valido` (Amasar, Fermentar, Hornear, Tajar, Empacar).
2. `POST /dependencias {"origen": "PRC-AMASAR", "destino": "PRC-HORNEAR"}` → otra vez
   `GET /orden-produccion` → `ciclo` ("Amasar necesita Hornear, Hornear necesita Fermentar…").
3. `DELETE /dependencias/<id devuelto en el paso 2>` → vuelve a `orden_valido`.

#### Volver al orden válido sin reiniciar la demo

```http
POST /orden-produccion/restaurar
```

Quita de una vez las dependencias `proceso → proceso` que **no estaban en los datos
iniciales** y que **unen dos procesos del mismo grupo con ciclo** (Tarjan). Devuelve
`{"quitadas": [...], "orden": <GET /orden-produccion>}`. Si no hay ciclo, `quitadas` es `[]`.

No toca proveedores, insumos, productos ni las dependencias agregadas que no causan ciclos,
a diferencia de `POST /demo/reset`, que borra todo lo registrado. Por eso no pide clave.

**Por qué siempre deja un orden válido:** toda arista de un ciclo une procesos del mismo
grupo de Tarjan, y los datos iniciales no tienen ciclos, así que cada ciclo usa al menos una
dependencia agregada. Al quitarlas todas no queda ningún ciclo. Costo: O(P + E), un Tarjan
más una pasada por las aristas.

### Grafo completo y reinicio de la demo

- `GET /grafo` → `{"nodos": [...], "aristas": [...]}`. Cada nodo trae su `capa`. Es lo que
  usa el front para cargar y para refrescar después de cada POST o DELETE.
- `POST /demo/reset` con el header `X-Demo-Token` → vuelve a los datos de `data.py` y
  devuelve el grafo reiniciado.

```bash
curl -X POST https://grafos-math-back.onrender.com/demo/reset -H "X-Demo-Token: <clave>"
```

#### Clave del reset

El reset borra todo lo registrado, así que está protegido:

1. En el servidor (Render → Environment) se define `DEMO_RESET_TOKEN` con una clave larga.
   Si la variable no existe, el reset queda **deshabilitado** (403): un despliegue sin
   configurar no queda abierto.
2. Quien presenta la demo envía la clave en el header `X-Demo-Token`. Sin el header o con
   una clave incorrecta responde 403 y el grafo no cambia.

La clave no va en el código del front: todo lo que viaja al navegador lo puede leer
cualquiera. El front la pide al presentador y la guarda solo durante la sesión.

---

## Decisiones de diseño

### 1. Dirección de las aristas: `A REQUIERE B`

Cada arista se lee como una frase completa: **"para producir A necesito B"**.

```
Producto ──► Proceso ──► Proceso ──► Insumo ──► Proveedor
Pan tajado → Empacar → Tajar → Hornear → Fermentar → Amasar → Harina, Levadura
                └──► Bolsas de empaque
```

Al invertirla la frase deja de tener sentido ("para producir harina necesito pan tajado"),
así que el grafo es **dirigido**. Se eligió `REQUIERE` (y no "habilita") porque es como habla
el negocio al registrar: compras dice "el ponqué requiere conservante".

**Representación:** el grafo se guarda como lista de nodos y lista de aristas (`Grafo` en
`models.py`), el mismo formato que devuelve `GET /grafo`. Los algoritmos arman la lista de
adyacencia que necesitan en cada consulta: el recorrido de impacto la arma **inversa**
(quién me requiere) y el orden topológico, solo entre procesos.

### 2. Qué significa "alcanzar" (impacto)

Alcanzar significa **"le llega la falla"**, como fichas de dominó. Si la Distribuidora de
químicos deja de entregar:

```
Distribuidora de químicos  ──►  Conservante  ──►  Ponqué
                                            └──►  Tostadas
```

1. Sin la distribuidora no hay **conservante**: la falla lo alcanza directamente.
2. Sin conservante no hay **ponqué** ni **tostadas**: la falla los alcanza a través del conservante.
3. El **pan** no usa conservante: la falla **no lo alcanza** y se sigue produciendo.

Lo alcanzable desde un elemento es todo lo que se cae si ese elemento falla. Como la flecha
es `REQUIERE`, el impacto se recorre **en contra** de la flecha: del elemento no disponible
hacia quienes lo necesitan. No hace falta ningún condicional especial por capa: la dirección
del modelo ya dice hacia dónde se propaga la falla.

Se usa **BFS** (`recorrido.py`) porque recorre por niveles: primero lo afectado directamente
y después lo afectado a través de otros. Cada afectado trae su `nivel` (cuántas flechas hay
desde el origen) y su `camino`, que es lo que el tablero muestra como "por qué se afecta".

### 3. Orden de producción: DAG y algoritmo de Kahn

- **Dirigido:** `A REQUIERE B` no es lo mismo que `B REQUIERE A`.
- **Acíclico:** ningún camino vuelve al punto de partida.

Con `A REQUIERE B`, B se hace **antes** que A. Un orden de trabajo válido (orden topológico)
es una lista donde cada proceso aparece después de todo lo que requiere, y existe **si y
solo si** el grafo es acíclico. Si hay un ciclo, sus procesos se esperan entre sí y
cualquier lista que los incluya rompería alguna dependencia: sería un **orden falso**.

Traza de lo que queda sin requisitos pendientes en cada paso (la pista del brief), que es
exactamente lo que hace `ordenar_por_etapas` en `topologico.py`:

1. Contar, para cada proceso, cuántos procesos requiere que todavía no están hechos.
2. La etapa actual son los procesos con 0 pendientes: se pueden hacer ya, y a la vez entre sí.
3. Al terminarlos, se descuenta 1 a cada proceso que los esperaba.
4. Repetir con los que llegaron a 0 hasta que no quede ninguno.

Solo cuentan los requisitos **entre procesos**. Los insumos los entrega compras y no se
ordenan: se muestran como "Usa ..." en cada paso.

**Caso acíclico (pan tajado):** Fermentar requiere Amasar, Hornear requiere Fermentar, Tajar
requiere Hornear, Empacar requiere Tajar.

| Paso | Pendientes (Amasar, Fermentar, Hornear, Tajar, Empacar) | Sin pendientes → etapa | Se libera |
|---|---|---|---|
| 1 | 0, 1, 1, 1, 1 | **Amasar** | Fermentar |
| 2 | —, 0, 1, 1, 1 | **Fermentar** | Hornear |
| 3 | —, —, 0, 1, 1 | **Hornear** | Tajar |
| 4 | —, —, —, 0, 1 | **Tajar** | Empacar |
| 5 | —, —, —, —, 0 | **Empacar** | — (pan listo) |

Resultado: `etapas = [[Amasar], [Fermentar], [Hornear], [Tajar], [Empacar]]`. Si dos procesos
llegan a 0 en el mismo paso, quedan en la misma etapa.

**Caso cíclico (se agrega `PRC-AMASAR → PRC-HORNEAR`):**

| Paso | Pendientes (Amasar, Fermentar, Hornear, Tajar, Empacar) | Sin pendientes → etapa |
|---|---|---|
| 1 | **1**, 1, 1, 1, 1 | *ninguno* |

Kahn se detiene sin ordenar nada: esa es la señal de que hay un ciclo. Pero no dice
**cuál**, porque Tajar y Empacar también quedaron bloqueados sin ser parte del ciclo. Por
eso se usa un segundo algoritmo para ubicarlo.

### 4. Cómo se detecta y reporta un ciclo

Un ciclo es una cadena `P1 requiere P2, …, Pn requiere P1`.

| Situación | Ejemplo | ¿Ciclo? |
|---|---|---|
| Cadena que se cierra | Amasar → Hornear → Fermentar → Amasar | Sí, de 3 procesos |
| Dependencia mutua | Glasear → Decorar → Glasear | Sí, de 2 |
| Proceso que se requiere a sí mismo | Tajar → Tajar | Sí, de 1 ("esa dependencia sobra") |
| Dos caminos al mismo proceso | Empacar requiere Tajar y Etiquetar; los dos requieren Hornear | **No**: es un rombo |
| Proceso que depende de un ciclo | Tajar requiere Hornear (que está en el ciclo) | **No**; queda **bloqueado** |

`buscar_ciclos` en `topologico.py`:

1. **Tarjan** agrupa los procesos en componentes fuertemente conexas. Un grupo de 2 o más
   procesos, o un proceso que se requiere a sí mismo, contiene un ciclo.
2. De cada grupo se reporta **un** ciclo: el más corto que pasa por su primer proceso (BFS
   dentro del grupo). Así el coordinador ve la contradicción mínima que debe romper.
3. Cada producto que usa un proceso del ciclo queda sin orden (`etapas: null`) y
   `bloqueado_por` dice qué ciclo lo bloquea; los demás conservan su orden.

**No se presenta un orden falso:** con un ciclo, `etapas` es `null`.

### 5. Por qué un ciclo solo puede aparecer en `proceso → proceso`

Si se numeran las capas (proveedor 0, insumo 1, proceso 2, producto 3), la regla de capas
(`REGLAS_CAPAS` en `data.py`) solo permite aristas que **bajan** de nivel, salvo
`proceso → proceso`, que se queda en el mismo:

| Origen REQUIERE destino | Niveles |
|---|---|
| producto → insumo | 3 → 1 |
| producto → proceso | 3 → 2 |
| proceso → proceso | 2 → 2 |
| proceso → insumo | 2 → 1 |
| insumo → proveedor | 1 → 0 |

Un ciclo termina en el nivel donde empezó; si una arista bajara, otra tendría que subir, y
eso no existe. Por lo tanto todas las aristas de un ciclo son `proceso → proceso`. Por eso
`orden.py` solo analiza las aristas entre procesos.

**`POST /dependencias` no rechaza ciclos a propósito:** los acepta para que
`GET /orden-produccion` los detecte y los explique, que es lo que pide la F3. La corrección
la hace el coordinador con `DELETE /dependencias/{id}`.

### 6. Formato de los ids: un solo criterio para el dato inválido

Todo id es `PREFIJO-NOMBRE`: el prefijo de su capa, un guion y uno o más segmentos en
mayúsculas o dígitos separados por guion (`PRV-MOLINO`, `INS-HARINA`, `PRD-GALLETA-AVENA`).

| Capa | Prefijo |
|---|---|
| Producto | `PRD-` |
| Proceso | `PRC-` |
| Insumo | `INS-` |
| Proveedor | `PRV-` |

La regla vive en `ids.py` y se aplica en los modelos de entrada (`models.py`), así que
pydantic la revisa antes de llegar a cualquier handler. Todo id que llega a la API pasa por ella:

| Dónde | Campos | Inválido | Bien escrito pero no existe |
|---|---|---|---|
| `POST /productos`, `/procesos`, `/insumos`, `/proveedores` | `id` (con el prefijo de su capa), `proveedor_id`, `insumo_ids` | 422 | 404 en referencias · 409 si el `id` nuevo ya existe |
| `POST /dependencias` | `origen`, `destino` | 422 | 404 |
| `GET /impacto/{id}` | `id` | 422 | 404 |

Es inválido un id vacío, con espacios, en minúsculas, sin `PREFIJO-NOMBRE` o, al crear, con
el prefijo de otra capa. El `nombre` también es obligatorio: vacío o solo espacios → 422.

Todos los 422 de dato inválido tienen la misma forma (la de FastAPI), con el motivo en `msg`:

```json
{"detail": [{"type": "id_invalido", "loc": ["body", "id"], "msg": "El id 'PRV-x' no tiene un formato válido. ...", "input": "PRV-x"}]}
```

Así se cumple la distinción del brief entre **dato inválido** (422), **elemento inexistente**
(404) y **repetido** (409). Y como crear y consultar usan la misma regla, todo lo que se crea
se puede consultar después.

### 7. Datos en memoria y reinicio de la demo

Los datos viven en memoria (`MOCK_GRAFO` en `data.py`); no hay base de datos porque el
alcance son datos sintéticos. Consecuencias:

- Lo que se agrega o quita dura hasta que el servicio se reinicia, y es compartido por todos
  los que usan la demo al mismo tiempo.
- `POST /demo/reset` restaura una copia profunda de los datos iniciales. Modifica las listas
  **en el mismo objeto** (no lo reemplaza), porque otros módulos importan `MOCK_GRAFO` por nombre.
- El reset compara la clave con `secrets.compare_digest` para no filtrarla por tiempos de
  respuesta, y queda apagado si el servidor no tiene clave configurada.

### 8. `GET /grafo` en lugar de cinco llamadas

El front necesitaba `/productos`, `/procesos`, `/insumos`, `/proveedores` y `/aristas` para
dibujar la red. `GET /grafo` lo entrega en una sola respuesta coherente (todo del mismo
instante), y el front lo vuelve a pedir después de cada cambio en lugar de armar aristas por
su cuenta. Así los ids de las aristas siempre son los que asignó el back.

### 9. Complejidad aproximada y estructuras de datos

Notación: **V** = elementos (nodos), **E** = dependencias (aristas), **P** = procesos,
**Eₚ** = dependencias entre procesos, **R** = productos. Con los datos de la demo todo es
instantáneo (unas decenas de nodos); la tabla dice cómo crecería el costo con una red mayor.

#### Estructuras escogidas

| Estructura | Dónde | Por qué |
|---|---|---|
| **Listas de nodos y aristas** (`Grafo`) | `data.py`, `GET /grafo` | Es el formato que viaja por la API y que el front dibuja. Agregar es O(1) y es fácil de reiniciar y serializar |
| **Lista de adyacencia invertida** `dict[id, list[id]]` (quién me requiere) | `recorrido.construir_adyacencia_impacto` | El impacto va de la causa a la consecuencia; invertir la flecha una vez evita condicionales y deja ver los vecinos de un nodo en O(grado) |
| **Lista de adyacencia de requisitos entre procesos** `dict[id, list[id]]` | `orden.py` → `topologico.py` | Solo los procesos pueden formar ciclos (decisión 5), así que Kahn y Tarjan trabajan sobre un grafo más pequeño |
| **Cola** (`collections.deque`) | BFS de impacto y ciclo más corto | Sacar por delante es O(1); garantiza el recorrido por niveles |
| **Diccionario `padres`** | BFS | Sirve a la vez de conjunto de visitados (`in` en O(1)) y para reconstruir el camino de cada afectado |
| **Diccionario de pendientes** (grado de entrada) | Kahn | Saber en O(1) cuándo un proceso queda sin requisitos |
| **Pila + `indice`/`bajo`** | Tarjan | La pila guarda los procesos del grupo en construcción; `bajo` detecta cuándo se cierra un ciclo |
| **Conjuntos** (`set`) | `alcanzables`, `en_pila`, filtros | Pertenencia en O(1) |

#### Complejidad por consulta

| Operación | Costo | Detalle |
|---|---|---|
| Armar la adyacencia de impacto | O(V + E) | Un recorrido por nodos y otro por aristas |
| BFS de impacto | O(V + E) | Cada nodo entra una vez a la cola y cada arista se mira una vez |
| Reconstruir los caminos de los afectados | O(V · h) | h = profundidad de la red (≤ 5 niveles con las capas actuales); en la práctica O(V) |
| **`GET /impacto/{id}` total** | **O(V + E)** con h acotada | |
| Armar requisitos entre procesos | O(E · d) | d = requisitos por proceso; revisa que no se repitan |
| Kahn por etapas | O(P + Eₚ) | Cada proceso entra una vez a una etapa y cada dependencia se descuenta una vez |
| Tarjan | O(P + Eₚ) | Cada proceso y cada dependencia se visitan una vez |
| Ciclo más corto (BFS por componente) | O(P + Eₚ) en total | Cada BFS se queda dentro de su componente |
| Plan por producto (`alcanzables` + Kahn) | O(R · (E + P + Eₚ)) | Para cada producto se buscan sus procesos y se ordenan |
| **`GET /orden-produccion` total** | **O(R · (E + P + Eₚ))** | Domina el plan por producto; Kahn y Tarjan solos son lineales |

#### Operaciones del catálogo

Los nodos y aristas están en **listas**, así que buscar por id es una búsqueda lineal:

| Operación | Costo |
|---|---|
| `buscar_nodo` / `existe_nodo` (409, 404) | O(V) |
| `existe_arista` (dependencia repetida, 409) | O(E) |
| `quitar_arista`, `siguiente_arista_id` | O(E) |
| `POST /productos` con k insumos | O(k · V) |
| Validar formato del id (`ids.py`) | O(largo del id) |

Se aceptó la búsqueda lineal porque la red es pequeña y las listas mantienen el mismo orden
que se muestra en la interfaz. Si la red creciera a miles de elementos, el cambio sería
agregar un índice `dict[id, Nodo]` y un `set` de pares `(origen, destino)`, que dejan esas
búsquedas en O(1) sin cambiar los algoritmos.

**Límites conocidos:**
- Tarjan está escrito con recursión: con más de ~1000 procesos encadenados se pasaría del
  límite de recursión de Python. Para la demo no aplica; la solución sería la versión
  iterativa con pila explícita.
- **Corrección hecha al revisar la complejidad:** el BFS revisaba `vecino not in visitados`
  sobre una lista, lo que hacía cada revisión O(V) y el recorrido O(V · E). Ahora revisa el
  diccionario `padres` (O(1)) y el recorrido es O(V + E). El orden de visita no cambió y las
  pruebas siguen pasando.
