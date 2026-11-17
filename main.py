import os
import secrets
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data import (
    agregar_arista,
    agregar_nodo,
    buscar_nodo,
    capas_permitidas,
    existe_arista,
    existe_nodo,
    MOCK_GRAFO,
    quitar_arista,
    reiniciar_grafo,
)
from impacto import consultar_impacto
from orden import consultar_orden_produccion
from models import (
    Arista,
    DependenciaCreate,
    Grafo,
    ImpactoResponse,
    InsumoCreate,
    Nodo,
    OrdenProduccionResponse,
    ProcesoCreate,
    ProductoCreate,
    ProveedorCreate,
)

app = FastAPI()

# CORS: se agrega (no reemplaza nada) para que el front en Netlify / local
# pueda llamar a esta API. Misma idea que en feature/catalogo-dependencias.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://grafos-math.netlify.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rechazar_id_repetido(elemento_id: str) -> None:
    """
    409 si ya existe un elemento con ese id.

    El formato del id (422) no se revisa aquí: lo valida el modelo de
    entrada (models.ElementoCreate) antes de llegar al handler.
    """
    if existe_nodo(elemento_id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{elemento_id}'")


def error_id_invalido(elemento_id: str, motivo: str) -> HTTPException:
    """
    422 de GET /impacto con la misma forma que los 422 de pydantic en los POST,
    para que el front lea el dato inválido igual en todos los endpoints.
    """
    return HTTPException(
        status_code=422,
        detail=[{"type": "id_invalido", "loc": ["path", "elemento_id"], "msg": motivo, "input": elemento_id}],
    )


@app.get("/")
def read_root():
    return {"mensaje": "API funcionando"}


@app.get("/productos", response_model=List[Nodo])
def listar_productos():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "producto"]


@app.get("/procesos", response_model=List[Nodo])
def listar_procesos():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "proceso"]


@app.get("/insumos", response_model=List[Nodo])
def listar_insumos():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "insumo"]


@app.get("/proveedores", response_model=List[Nodo])
def listar_proveedores():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "proveedor"]


@app.get("/aristas", response_model=List[Arista])
def listar_aristas():
    """Lista las dependencias (misma ruta que ya consume el front desplegado)."""
    return MOCK_GRAFO.aristas


@app.get("/grafo", response_model=Grafo)
def obtener_grafo():
    """
    Devuelve todos los nodos (productos, procesos, insumos y proveedores)
    y todas las aristas en una sola respuesta.

    Reemplaza las llamadas separadas a /productos, /procesos, /insumos,
    /proveedores y /aristas. Cada nodo trae su `capa` para que el front
    los agrupe.
    """
    return MOCK_GRAFO


@app.post("/demo/reset", response_model=Grafo)
def reiniciar_demo(x_demo_token: Optional[str] = Header(default=None)):
    """
    Descarta los cambios hechos por la API (nodos y dependencias creadas o
    eliminadas) y vuelve a cargar los datos de data.py.

    Requiere el header `X-Demo-Token` con el valor de la variable de entorno
    DEMO_RESET_TOKEN. Si esa variable no está configurada, el reset queda
    deshabilitado: así un despliegue sin configurar no queda abierto.

    - 403 si falta el header, no coincide, o el reset está deshabilitado.

    Devuelve el grafo ya reiniciado, con el mismo formato que GET /grafo.
    """
    esperado = os.environ.get("DEMO_RESET_TOKEN", "")
    if not esperado:
        raise HTTPException(
            status_code=403,
            detail="El reset de la demo está deshabilitado: falta configurar DEMO_RESET_TOKEN en el servidor.",
        )
    # compare_digest compara en tiempo constante, para no filtrar la clave por tiempos de respuesta.
    if not x_demo_token or not secrets.compare_digest(x_demo_token.encode(), esperado.encode()):
        raise HTTPException(status_code=403, detail="Clave de reset inválida o ausente (header X-Demo-Token).")

    reiniciar_grafo()
    return MOCK_GRAFO


@app.get("/impacto/{elemento_id}", response_model=ImpactoResponse)
def obtener_impacto(elemento_id: str):
    """
    Simula que un proveedor, insumo o producto no está disponible y
    responde qué elementos de la red de abastecimiento quedan
    comprometidos.

    Casos en el cuerpo (`caso`):
      - id_invalido       → HTTP 422, id vacío, con espacios o mal formado
      - inexistente       → HTTP 404, buen formato pero no está en el catálogo
      - sin_dependencias  → 200, nadie más depende de él
      - afecta_cadena     → 200, ver `afectados` / `visitados`

    Ejemplo: GET /impacto/PRV-MATERIAPRIMA
    """
    resultado = consultar_impacto(MOCK_GRAFO, elemento_id)
    if resultado.caso == "id_invalido":
        raise error_id_invalido(elemento_id, resultado.mensaje)
    if resultado.caso == "inexistente":
        raise HTTPException(status_code=404, detail=resultado.mensaje)
    return resultado


@app.get("/impacto", include_in_schema=False)
@app.get("/impacto/", include_in_schema=False)
def obtener_impacto_sin_id():
    """Sin esta ruta, un id vacío caería en el 404 genérico de "ruta no encontrada"."""
    return obtener_impacto("")


@app.get("/orden-produccion", response_model=OrdenProduccionResponse)
def obtener_orden_produccion():
    """
    Responde en qué orden se preparan los procesos internos o, si las
    dependencias se contradicen, qué ciclo lo impide.

    Casos en el cuerpo (`caso`), siempre HTTP 200:
      - sin_procesos  → no hay procesos registrados
      - orden_valido  → ver `etapas` y `planes`
      - ciclo         → ver `ciclos`; `etapas` es null (no hay orden falso)
    """
    return consultar_orden_produccion(MOCK_GRAFO)


@app.post("/proveedores", response_model=Nodo, status_code=201)
def crear_proveedor(datos: ProveedorCreate):
    rechazar_id_repetido(datos.id)

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="proveedor", categoria=datos.categoria)
    agregar_nodo(nodo)
    return nodo


@app.post("/procesos", response_model=Nodo, status_code=201)
def crear_proceso(datos: ProcesoCreate):
    """
    Crea un proceso interno sin conexiones. Sus dependencias
    (producto -> proceso, proceso -> proceso, proceso -> insumo)
    se registran después con POST /dependencias.
    """
    rechazar_id_repetido(datos.id)

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="proceso", categoria=datos.categoria)
    agregar_nodo(nodo)
    return nodo


@app.post("/insumos", response_model=Nodo, status_code=201)
def crear_insumo(datos: InsumoCreate):
    rechazar_id_repetido(datos.id)

    proveedor = buscar_nodo(datos.proveedor_id)
    if proveedor is None:
        raise HTTPException(status_code=404, detail=f"No existe el proveedor '{datos.proveedor_id}'")
    if proveedor.capa != "proveedor":
        raise HTTPException(status_code=422, detail=f"'{datos.proveedor_id}' no es un proveedor")

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="insumo", categoria=datos.categoria)
    agregar_nodo(nodo)
    agregar_arista(origen=nodo.id, destino=proveedor.id)
    return nodo


@app.post("/productos", response_model=Nodo, status_code=201)
def crear_producto(datos: ProductoCreate):
    rechazar_id_repetido(datos.id)

    insumos = []
    for insumo_id in datos.insumo_ids:
        insumo = buscar_nodo(insumo_id)
        if insumo is None:
            raise HTTPException(status_code=404, detail=f"No existe el insumo '{insumo_id}'")
        if insumo.capa != "insumo":
            raise HTTPException(status_code=422, detail=f"'{insumo_id}' no es un insumo")
        insumos.append(insumo)

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="producto", categoria=datos.categoria)
    agregar_nodo(nodo)
    for insumo in insumos: 
        agregar_arista(origen=nodo.id, destino=insumo.id)
    return nodo


@app.post("/dependencias", response_model=Arista, status_code=201)
def crear_dependencia(datos: DependenciaCreate):
    """
    Registra "origen REQUIERE destino" entre dos elementos que ya existen.

    - 404 si origen o destino no existen.
    - 409 si la dependencia ya está registrada.
    - 422 si la regla de capas no lo permite (ej. proveedor -> producto).

    No rechaza ciclos: la detección y el reporte de ciclos es tarea de la F3.
    """
    origen = buscar_nodo(datos.origen)
    if origen is None:
        raise HTTPException(status_code=404, detail=f"No existe el elemento origen '{datos.origen}'")
    destino = buscar_nodo(datos.destino)
    if destino is None:
        raise HTTPException(status_code=404, detail=f"No existe el elemento destino '{datos.destino}'")

    if existe_arista(origen.id, destino.id):
        raise HTTPException(
            status_code=409,
            detail=f"La dependencia '{origen.id}' -> '{destino.id}' ya existe",
        )

    if not capas_permitidas(origen.capa, destino.capa):
        raise HTTPException(
            status_code=422,
            detail=f"Un {origen.capa} no puede requerir un {destino.capa} ('{origen.id}' -> '{destino.id}')",
        )

    return agregar_arista(origen=origen.id, destino=destino.id)


@app.delete("/dependencias/{arista_id}", response_model=Arista)
def eliminar_dependencia(arista_id: str):
    """
    Quita una dependencia por su id y devuelve la arista eliminada.

    Sirve para corregir una contradicción: si GET /orden-produccion reporta
    un ciclo, quitar una de sus dependencias lo rompe.

    - 404 si no existe una dependencia con ese id.
    """
    arista = quitar_arista(arista_id)
    if arista is None:
        raise HTTPException(status_code=404, detail=f"No existe la dependencia '{arista_id}'")
    return arista
