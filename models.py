from typing import Literal, Optional, List
from pydantic import BaseModel, Field

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

class ProveedorCreate(BaseModel):
    id: str
    nombre: str
    categoria: Optional[str] = None


class InsumoCreate(BaseModel):
    id: str
    nombre: str
    categoria: Optional[str] = None
    proveedor_id: str


class ProductoCreate(BaseModel):
    id: str
    nombre: str
    categoria: Optional[str] = None
    insumo_ids: List[str] = Field(min_length=1)