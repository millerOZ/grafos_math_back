from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data import (
    agregar_arista,
    agregar_nodo,
    buscar_nodo,
    capas_permitidas,
    existe_arista,
    existe_nodo,
    MOCK_GRAFO,
)
from impacto import consultar_impacto
from orden import consultar_orden_produccion
from models import (
    Arista,
    DependenciaCreate,
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


@app.get("/impacto/{elemento_id}", response_model=ImpactoResponse)
def obtener_impacto(elemento_id: str):
    """
    Simula que un proveedor, insumo o producto no está disponible y
    responde qué elementos de la red de abastecimiento quedan
    comprometidos.

    Casos en el cuerpo (`caso`):
      - inexistente       → HTTP 404
      - sin_dependencias  → 200, nadie más depende de él
      - afecta_cadena     → 200, ver `afectados` / `visitados`

    Ejemplo: GET /impacto/PRV-MATERIAPRIMA
    """
    resultado = consultar_impacto(MOCK_GRAFO, elemento_id)
    if resultado.caso == "inexistente":
        raise HTTPException(status_code=404, detail=resultado.mensaje)
    return resultado


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
    if existe_nodo(datos.id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{datos.id}'")

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
    if existe_nodo(datos.id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{datos.id}'")

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="proceso", categoria=datos.categoria)
    agregar_nodo(nodo)
    return nodo


@app.post("/insumos", response_model=Nodo, status_code=201)
def crear_insumo(datos: InsumoCreate):
    if existe_nodo(datos.id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{datos.id}'")

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
    if existe_nodo(datos.id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{datos.id}'")

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
