from typing import List

from fastapi import FastAPI

from data import MOCK_GRAFO
from models import Nodo

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
