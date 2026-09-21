from typing import Literal, Optional, List
from pydantic import BaseModel

Capa = Literal["producto", "insumo", "proveedor"]


class Nodo(BaseModel):
    id: str
    nombre: str
    capa: Capa
    categoria: Optional[str] = None


class Arista(BaseModel):
    id: str
    origen: str   
    destino: str  
    tipo: Literal["REQUIERE"]


class Grafo(BaseModel):
    nodos: List[Nodo]
    aristas: List[Arista]