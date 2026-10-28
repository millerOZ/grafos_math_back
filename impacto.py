"""
Consulta de disponibilidad e impacto sobre la red de abastecimiento.

Propósito de producto
---------------------
Cuando un proveedor, un insumo o un producto deja de estar disponible,
producción necesita saber qué más de la panadería queda comprometido.
Esta capa responde esa pregunta de negocio usando el recorrido BFS de
`recorrido.py`.

Modelo de dependencias
----------------------
Cada arista se interpreta: origen REQUIERE destino
  producto → insumo → proveedor

La falla se propaga en sentido contrario a la flecha:
  si lo requerido no está, quien lo requiere tampoco puede operar.

API HTTP
--------
GET /impacto/{elemento_id}

Contrato de respuesta (`ImpactoResponse`):
  - inexistente       → el id no está en el catálogo
  - sin_dependencias  → existe, pero nadie más queda comprometido
  - afecta_cadena     → hay elementos alcanzados en la red

Recorrido
---------
El caminar del grafo lo hace el BFS de `recorrido.py`, que devuelve
`visitados` (orden de llegada, por niveles) y `padres`. Con `padres` se
reconstruye por qué camino llega la falla a cada elemento afectado.
"""

from __future__ import annotations

from models import Grafo, ImpactoResponse, Nodo, NodoAfectado, NodoImpactado
from recorrido import reconstruir_camino, recorrer_red


def _a_nodo_impactado(nodo: Nodo) -> NodoImpactado:
    return NodoImpactado(id=nodo.id, nombre=nodo.nombre, capa=nodo.capa)


def _a_nodo_afectado(nodo: Nodo, camino: list[str]) -> NodoAfectado:
    return NodoAfectado(id=nodo.id, nombre=nodo.nombre, capa=nodo.capa, nivel=len(camino) - 1, camino=camino)


def _buscar(grafo: Grafo, elemento_id: str) -> Nodo | None:
    for nodo in grafo.nodos:
        if nodo.id == elemento_id:
            return nodo
    return None


def consultar_impacto(grafo: Grafo, elemento_id: str) -> ImpactoResponse:
    """
    Simula que `elemento_id` no está disponible y reporta el impacto
    sobre la cadena de abastecimiento de la panadería.
    """
    origen = _buscar(grafo, elemento_id)

    if origen is None:
        return ImpactoResponse(
            origen=None,
            caso="inexistente",
            mensaje=f"No existe el elemento '{elemento_id}' en el catálogo.",
            visitados=[],
            afectados=[],
        )

    ids_visitados, padres = recorrer_red(grafo, elemento_id)

    nodos_por_id = {nodo.id: nodo for nodo in grafo.nodos}
    afectados = [
        _a_nodo_afectado(nodos_por_id[vid], reconstruir_camino(padres, vid))
        for vid in ids_visitados[1:]  # el primero es el origen
    ]

    if not afectados:
        return ImpactoResponse(
            origen=_a_nodo_impactado(origen),
            caso="sin_dependencias",
            mensaje=(
                f"'{origen.nombre}' ({origen.id}) está en el catálogo, pero "
                "ningún otro elemento de la red depende de él: su "
                "indisponibilidad no compromete la producción."
            ),
            visitados=ids_visitados,
            afectados=[],
        )

    return ImpactoResponse(
        origen=_a_nodo_impactado(origen),
        caso="afecta_cadena",
        mensaje=(
            f"Si '{origen.nombre}' ({origen.id}) no está disponible, "
            f"quedan comprometidos {len(afectados)} elemento(s) de la red."
        ),
        visitados=ids_visitados,
        afectados=afectados,
    )


def simular_indisponibilidad(grafo: Grafo, elemento_id: str) -> ImpactoResponse:
    """Alias de negocio: consultar impacto = simular indisponibilidad."""
    return consultar_impacto(grafo, elemento_id)
