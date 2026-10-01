from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data import MOCK_GRAFO
from models import Arista, Nodo

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.get("/aristas", response_model=List[Arista])
def listar_aristas():
    return MOCK_GRAFO.aristas