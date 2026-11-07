from typing import Literal, Optional, List
from pydantic import BaseModel, Field

Capa = Literal["producto", "proceso", "insumo", "proveedor"]


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


class ProcesoCreate(BaseModel):
    """Paso interno de producción (amasar, hornear...). Se conecta luego con POST /dependencias."""

    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
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


class DependenciaCreate(BaseModel):
    """Conecta dos elementos ya existentes: `origen` REQUIERE `destino`."""

    origen: str = Field(min_length=1)
    destino: str = Field(min_length=1)


# --- Disponibilidad e impacto sobre la red de abastecimiento ---

CasoImpacto = Literal[
    "inexistente",
    "sin_dependencias",
    "afecta_cadena",
]


class NodoImpactado(BaseModel):
    """Elemento de la red (id, nombre y capa)."""

    id: str
    nombre: str
    capa: Capa


class NodoAfectado(NodoImpactado):
    """
    Elemento al que le llega la falla.

    - nivel: cuántas flechas hay desde el origen hasta este elemento.
    - camino: ids desde el origen hasta este elemento.
    """

    nivel: int
    camino: List[str]


class ImpactoResponse(BaseModel):
    """
    Resultado de preguntar: si este elemento no está disponible,
    ¿qué queda comprometido en la panadería?

    - origen: elemento consultado (None si el id no existe).
    - caso: inexistente | sin_dependencias | afecta_cadena
    - visitados: ids en el orden en que los visitó el recorrido
      (el primero es el origen).
    - afectados: elementos alcanzados, en el orden de visita del
      recorrido (por niveles), sin incluir el origen.
    """

    origen: Optional[NodoImpactado] = None
    caso: CasoImpacto
    mensaje: str
    visitados: List[str] = []
    afectados: List[NodoAfectado] = []


# --- Orden y ciclos de producción (F3) ---

CasoOrden = Literal[
    "sin_procesos",
    "orden_valido",
    "ciclo",
]


class Ciclo(BaseModel):
    """
    Cadena de procesos que termina esperando por sí misma.

    - ids: cada proceso requiere al siguiente, y el último al primero.
    - descripcion: el ciclo en frases ("Amasar necesita Hornear, ...").
    """

    ids: List[str]
    descripcion: str


class PlanProducto(BaseModel):
    """
    Orden de preparación de un producto que usa procesos.

    - etapas: procesos por etapa, requisitos primero; los de una misma
      etapa se pueden hacer a la vez. None si algún proceso está en un ciclo.
    - bloqueado_por: índices de `ciclos` que impiden ordenar este producto.
    """

    producto: NodoImpactado
    etapas: Optional[List[List[str]]] = None
    bloqueado_por: List[int] = []


class OrdenProduccionResponse(BaseModel):
    """
    Resultado de preguntar: ¿en qué orden se preparan los procesos, o
    dónde se contradicen?

    - caso: sin_procesos | orden_valido | ciclo
    - etapas: etapas de todos los procesos. None si hay ciclos: no se
      presenta un orden falso.
    - ciclos / en_ciclo: contradicciones encontradas y procesos que las forman.
    - planes: orden por producto (solo productos que usan procesos).
    - sin_procesos: productos que todavía no tienen procesos registrados.
    """

    caso: CasoOrden
    mensaje: str
    etapas: Optional[List[List[str]]] = None
    ciclos: List[Ciclo] = []
    en_ciclo: List[str] = []
    planes: List[PlanProducto] = []
    sin_procesos: List[NodoImpactado] = []
