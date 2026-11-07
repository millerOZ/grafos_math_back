"""
Orden topológico y ciclos sobre los procesos (algoritmos propios, sin librerías de grafos).

Lo usa la consulta de orden de producción (`orden.py`). Es un port de lo que
antes calculaba el front (`domain/ciclos.ts`); el front ahora consume
`GET /orden-produccion`.

Contrato
--------
Todas las funciones reciben `requisitos`: lista de adyacencia en la dirección
del catálogo,

  requisitos[A] = [B, ...]   significa   "A REQUIERE B"  (B va antes que A)

  - ordenar_por_etapas(ids, requisitos) -> etapas
  - buscar_ciclos(ids, requisitos)      -> ciclos
  - alcanzables(inicio, requisitos)     -> todo lo que hace falta desde `inicio`

Por qué solo procesos
---------------------
La regla de capas (`data.REGLAS_CAPAS`) solo permite que una capa se requiera
a sí misma en `proceso -> proceso`. Cualquier ciclo de la red tiene que estar
formado por procesos, así que basta con analizar esas aristas.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Hashable, List, Optional, Set

Requisitos = Dict[Hashable, List[Hashable]]


def alcanzables(inicio: List[Hashable], requisitos: Requisitos) -> Set[Hashable]:
    """Todos los elementos que hacen falta, directa o indirectamente, desde `inicio`."""
    vistos: Set[Hashable] = set()
    pila = list(inicio)
    while pila:
        actual = pila.pop()
        if actual in vistos:
            continue
        vistos.add(actual)
        pila.extend(requisitos.get(actual, []))
    return vistos


def ordenar_por_etapas(ids: List[Hashable], requisitos: Requisitos) -> List[List[Hashable]]:
    """
    Kahn por niveles: en cada etapa entran los elementos cuyos requisitos ya se
    hicieron. Solo cuenta los requisitos que están en `ids`. Se asume que `ids`
    no tiene ciclos.
    """
    conjunto = set(ids)
    pendientes = {id: len([r for r in requisitos.get(id, []) if r in conjunto]) for id in ids}
    # Quién espera a cada elemento (arista invertida).
    esperan: Requisitos = {id: [] for id in ids}
    for id in ids:
        for r in requisitos.get(id, []):
            if r in conjunto:
                esperan[r].append(id)

    etapas = []
    actual = [id for id in ids if pendientes[id] == 0]
    while actual:
        etapas.append(actual)
        siguiente = []
        for id in actual:
            for otro in esperan[id]:
                pendientes[otro] -= 1
                if pendientes[otro] == 0:
                    siguiente.append(otro)
        actual = siguiente
    return etapas


def buscar_ciclos(ids: List[Hashable], requisitos: Requisitos) -> List[List[Hashable]]:
    """
    Componentes fuertemente conexas (Tarjan). Cada componente con más de un
    elemento, o con uno que se requiere a sí mismo, contiene un ciclo; de cada
    una se reporta el ciclo más corto que pasa por su primer elemento (según `ids`).
    """
    contador = 0
    indice: Dict[Hashable, int] = {}
    bajo: Dict[Hashable, int] = {}
    pila: List[Hashable] = []
    en_pila: Set[Hashable] = set()
    componentes: List[List[Hashable]] = []

    def visitar(v: Hashable) -> None:
        nonlocal contador
        indice[v] = contador
        bajo[v] = contador
        contador += 1
        pila.append(v)
        en_pila.add(v)
        for w in requisitos.get(v, []):
            if w not in indice:
                visitar(w)
                bajo[v] = min(bajo[v], bajo[w])
            elif w in en_pila:
                bajo[v] = min(bajo[v], indice[w])
        if bajo[v] == indice[v]:
            componente = []
            while True:
                w = pila.pop()
                en_pila.discard(w)
                componente.append(w)
                if w == v:
                    break
            componentes.append(componente)

    for id in ids:
        if id not in indice:
            visitar(id)

    orden = {id: i for i, id in enumerate(ids)}
    ciclos = []
    for componente in componentes:
        if len(componente) > 1 or componente[0] in requisitos.get(componente[0], []):
            raiz = min(componente, key=lambda id: orden[id])
            ciclos.append(ciclo_mas_corto(raiz, set(componente), requisitos))
    ciclos.sort(key=lambda ciclo: orden[ciclo[0]])
    return ciclos


def ciclo_mas_corto(raiz: Hashable, componente: Set[Hashable], requisitos: Requisitos) -> List[Hashable]:
    """BFS desde `raiz` dentro de la componente hasta volver a ella."""
    padres: Dict[Hashable, Optional[Hashable]] = {raiz: None}
    Q = deque([raiz])
    while Q:
        actual = Q.popleft()
        for vecino in requisitos.get(actual, []):
            if vecino == raiz:
                camino = []
                paso: Optional[Hashable] = actual
                while paso is not None:
                    camino.append(paso)
                    paso = padres[paso]
                camino.reverse()
                return camino
            if vecino in componente and vecino not in padres:
                padres[vecino] = actual
                Q.append(vecino)
    return [raiz]
