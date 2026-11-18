from typing import ClassVar, List, Literal, Optional

from pydantic import AfterValidator, BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated

from ids import validar_formato_id, validar_id_para_capa

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

# --- Datos de entrada (POST) ---
#
# Un solo criterio para el dato inválido en todos los endpoints: cualquier id
# que llegue en un body (el del elemento nuevo, proveedor_id, insumo_ids, origen,
# destino) pasa por ids.validar_formato_id, la misma regla de GET /impacto/{id}.
# Pydantic lo rechaza antes de llegar al handler, así que todos responden igual:
# 422 con `detail` en forma de lista y el motivo en `msg`.


def _id_con_formato(valor: str) -> str:
    motivo = validar_formato_id(valor)
    if motivo is not None:
        raise PydanticCustomError("id_invalido", motivo)
    return valor


def _texto_obligatorio(valor: str) -> str:
    if not valor.strip():
        raise PydanticCustomError("texto_vacio", "No puede estar vacío ni tener solo espacios.")
    return valor


IdCatalogo = Annotated[str, AfterValidator(_id_con_formato)]
TextoObligatorio = Annotated[str, AfterValidator(_texto_obligatorio)]


class ElementoCreate(BaseModel):
    """
    Base de los cuatro POST de creación. `CAPA` fija el prefijo que debe
    llevar el id (PRV- para un proveedor, INS- para un insumo...).
    """

    CAPA: ClassVar[str]

    id: str
    nombre: TextoObligatorio
    categoria: Optional[str] = None

    @field_validator("id")
    @classmethod
    def _id_de_su_capa(cls, valor: str) -> str:
        motivo = validar_id_para_capa(valor, cls.CAPA)
        if motivo is not None:
            raise PydanticCustomError("id_invalido", motivo)
        return valor


class ProveedorCreate(ElementoCreate):
    CAPA: ClassVar[str] = "proveedor"


class ProcesoCreate(ElementoCreate):
    """Paso interno de producción (amasar, hornear...). Se conecta luego con POST /dependencias."""

    CAPA: ClassVar[str] = "proceso"


class InsumoCreate(ElementoCreate):
    CAPA: ClassVar[str] = "insumo"

    proveedor_id: IdCatalogo


class ProductoCreate(ElementoCreate):
    CAPA: ClassVar[str] = "producto"

    insumo_ids: List[IdCatalogo] = Field(min_length=1)


class DependenciaCreate(BaseModel):
    """Conecta dos elementos ya existentes: `origen` REQUIERE `destino`."""

    origen: IdCatalogo
    destino: IdCatalogo


# --- Disponibilidad e impacto sobre la red de abastecimiento ---

CasoImpacto = Literal[
    "id_invalido",
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
    - caso: id_invalido | inexistente | sin_dependencias | afecta_cadena
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


class RestaurarOrdenResponse(BaseModel):
    """
    Resultado de POST /orden-produccion/restaurar.

    - quitadas: dependencias proceso -> proceso que se quitaron (agregadas después
      de los datos iniciales y que formaban un ciclo). Vacía si no había ciclo.
    - orden: GET /orden-produccion después del cambio.
    """

    quitadas: List[Arista]
    orden: OrdenProduccionResponse
