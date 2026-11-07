"""
Consulta de orden y ciclos de producción.

Propósito de producto
---------------------
El coordinador de producción necesita saber en qué orden preparar los
procesos internos (amasar, fermentar, hornear...) o, si las dependencias se
contradicen, dónde está la contradicción. Esta capa responde esa pregunta
usando los algoritmos de `topologico.py`.

Modelo de dependencias
----------------------
Cada arista se interpreta: origen REQUIERE destino
  "Para hornear necesito fermentar" → Fermentar va antes que Hornear.

Solo se analizan las aristas proceso -> proceso: es la única combinación de
capas que puede formar un ciclo (ver `data.REGLAS_CAPAS`).

API HTTP
--------
GET /orden-produccion

Contrato de respuesta (`OrdenProduccionResponse`):
  - sin_procesos  → no hay procesos registrados; no hay nada que ordenar
  - orden_valido  → `etapas` y `planes` traen el orden de preparación
  - ciclo         → `ciclos` dice dónde está la contradicción; `etapas` es
                    None y los productos afectados no traen orden (no se
                    presenta un orden falso)
"""

from __future__ import annotations

from models import Ciclo, Grafo, Nodo, NodoImpactado, OrdenProduccionResponse, PlanProducto
from topologico import Requisitos, alcanzables, buscar_ciclos, ordenar_por_etapas


def _a_nodo_impactado(nodo: Nodo) -> NodoImpactado:
    return NodoImpactado(id=nodo.id, nombre=nodo.nombre, capa=nodo.capa)


def _describir_ciclo(ids: list[str], nombres: dict[str, str]) -> str:
    if len(ids) == 1:
        return f"{nombres[ids[0]]} se necesita a sí mismo: esa dependencia sobra."
    frases = [f"{nombres[id]} necesita {nombres[ids[(i + 1) % len(ids)]]}" for i, id in enumerate(ids)]
    return ", ".join(frases) + ": ninguno puede empezar primero."


def consultar_orden_produccion(grafo: Grafo) -> OrdenProduccionResponse:
    """Ordena los procesos por etapas o reporta los ciclos que lo impiden."""
    nombres = {nodo.id: nodo.nombre for nodo in grafo.nodos}
    procesos = [nodo.id for nodo in grafo.nodos if nodo.capa == "proceso"]
    es_proceso = set(procesos)

    # requisitos[A] = procesos que A requiere (A -> B), sin repetidos.
    requisitos: Requisitos = {id: [] for id in procesos}
    for arista in grafo.aristas:
        if arista.origen in es_proceso and arista.destino in es_proceso:
            if arista.destino not in requisitos[arista.origen]:
                requisitos[arista.origen].append(arista.destino)

    ciclos = buscar_ciclos(procesos, requisitos)
    en_ciclo = {id for ciclo in ciclos for id in ciclo}

    planes = []
    sin_procesos = []
    for producto in (nodo for nodo in grafo.nodos if nodo.capa == "producto"):
        directos = [a.destino for a in grafo.aristas if a.origen == producto.id and a.destino in es_proceso]
        if not directos:
            sin_procesos.append(_a_nodo_impactado(producto))
            continue
        usados = alcanzables(directos, requisitos)
        bloqueado_por = [i for i, ciclo in enumerate(ciclos) if any(id in usados for id in ciclo)]
        # Se conserva el orden del catálogo para que las etapas sean estables.
        usados_en_orden = [id for id in procesos if id in usados]
        planes.append(PlanProducto(
            producto=_a_nodo_impactado(producto),
            etapas=None if bloqueado_por else ordenar_por_etapas(usados_en_orden, requisitos),
            bloqueado_por=bloqueado_por,
        ))

    respuesta = dict(
        ciclos=[Ciclo(ids=ciclo, descripcion=_describir_ciclo(ciclo, nombres)) for ciclo in ciclos],
        en_ciclo=[id for id in procesos if id in en_ciclo],
        planes=planes,
        sin_procesos=sin_procesos,
    )

    if not procesos:
        return OrdenProduccionResponse(
            caso="sin_procesos",
            mensaje="Todavía no hay procesos registrados: no hay un orden de preparación que calcular.",
            etapas=[],
            **respuesta,
        )

    if ciclos:
        bloqueados = [p.producto.nombre for p in planes if p.bloqueado_por]
        mensaje = (
            f"Hay {len(ciclos)} contradicción(es) entre procesos: algunos pasos terminan "
            "esperando por sí mismos y no existe un orden válido."
        )
        if bloqueados:
            mensaje += f" Productos sin orden posible: {', '.join(bloqueados)}."
        return OrdenProduccionResponse(caso="ciclo", mensaje=mensaje, etapas=None, **respuesta)

    return OrdenProduccionResponse(
        caso="orden_valido",
        mensaje=(
            f"Los {len(procesos)} proceso(s) no se contradicen: cada producto "
            "tiene un orden de preparación posible."
        ),
        etapas=ordenar_por_etapas(procesos, requisitos),
        **respuesta,
    )
