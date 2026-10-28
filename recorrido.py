"""
Recorrido sobre la red de dependencias (BFS propio, sin librerías de grafos).

Lo usa la consulta de impacto (`impacto.py`).

Contrato
--------
Función: recorrer_red(grafo, id_inicio) -> (visitados, padres)

  1. Parte del elemento que se supone no disponible.
  2. Si lo requerido cayó, quien lo requiere también queda no operable.
  3. `visitados`: ids sin duplicados; el primero es siempre id_inicio.
     Orden comprensible: por niveles (orden de descubrimiento del BFS).
  4. `padres`: desde qué elemento se llegó a cada uno (id_inicio → None).
     Con `reconstruir_camino` se obtiene el camino completo de la falla.

Dirección del grafo
-------------------
El catálogo guarda cada arista como:

  origen REQUIERE destino        producto → insumo → proveedor

Esa flecha va de la consecuencia a la causa. En lugar de recorrerla "al
revés" con condicionales, el recorrido construye su propia lista de
adyacencia con una única convención:

  A → B  significa  "B depende de A"  (si A falla, B queda afectado)

Cada arista `origen REQUIERE destino` se convierte en `destino → origen`.

Ejemplo: PRV-MATERIAPRIMA → INS-HARINA → PRD-PAN
  "Si falla el proveedor, falta harina; sin harina no hay pan."
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Hashable, List, Optional, Tuple

from models import Grafo

Adyacencia = Dict[Hashable, List[Hashable]]


def construir_adyacencia_impacto(grafo: Grafo) -> Adyacencia:
    """Lista de adyacencia causa → consecuencia: A → B si B depende de A."""
    adyacencia: Adyacencia = {nodo.id: [] for nodo in grafo.nodos}
    for arista in grafo.aristas:
        adyacencia[arista.destino].append(arista.origen)
    return adyacencia


def bfs(adyacencia: Adyacencia, inicio: Hashable) -> Tuple[List[Hashable], Dict[Hashable, Optional[Hashable]]]:
    """Recorrido en anchura desde `inicio`. Devuelve (visitados, padres)."""
    Q = deque([inicio])
    visitados = [inicio]
    padres: Dict[Hashable, Optional[Hashable]] = {inicio: None}

    while len(Q) != 0:
        actual = Q.popleft()
        for vecino in adyacencia.get(actual, []):
            if vecino not in visitados:
                visitados.append(vecino)
                padres[vecino] = actual
                Q.append(vecino)

    return visitados, padres


def recorrer_red(grafo: Grafo, id_inicio: str) -> Tuple[List[str], Dict[str, Optional[str]]]:
    """BFS sobre el grafo de impacto desde `id_inicio`. Devuelve (visitados, padres)."""
    return bfs(construir_adyacencia_impacto(grafo), id_inicio)


def reconstruir_camino(padres: Dict[Hashable, Optional[Hashable]], destino: Hashable) -> List[Hashable]:
    """Camino desde la raíz del BFS hasta `destino`, siguiendo `padres` hacia atrás."""
    camino = []
    actual: Optional[Hashable] = destino
    while actual is not None:
        camino.append(actual)
        actual = padres[actual]
    camino.reverse()
    return camino
