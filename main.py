from typing import List

from fastapi import FastAPI, HTTPException

from data import agregar_arista, agregar_nodo, buscar_nodo, existe_nodo, MOCK_GRAFO
from models import InsumoCreate, Nodo, ProductoCreate, ProveedorCreate

app = FastAPI()


@app.get("/")
def read_root():
    return {"mensaje": "API funcionando"}


@app.get("/productos", response_model=List[Nodo])
def listar_productos():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "producto"]


@app.get("/insumos", response_model=List[Nodo])
def listar_insumos():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "insumo"]


@app.get("/proveedores", response_model=List[Nodo])
def listar_proveedores():
    return [nodo for nodo in MOCK_GRAFO.nodos if nodo.capa == "proveedor"]


@app.post("/proveedores", response_model=Nodo, status_code=201)
def crear_proveedor(datos: ProveedorCreate):
    if existe_nodo(datos.id):
        raise HTTPException(status_code=409, detail=f"Ya existe un nodo con id '{datos.id}'")

    nodo = Nodo(id=datos.id, nombre=datos.nombre, capa="proveedor", categoria=datos.categoria)
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