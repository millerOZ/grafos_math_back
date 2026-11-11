"""
Pruebas de aceptación — Feature 3 (Orden y ciclos de producción)
AbastecePyme / grafos_math_back

Qué hace
--------
Le manda peticiones a la API, como lo haría cualquier cliente, y revisa
si responde lo esperado. Hay un escenario por cada caso que pide la guía
para esta feature:

  1. Escenario normal (acíclico)  -> orden de trabajo válido
  2. Nodo inexistente             -> conectar un proceso que no está en el catálogo
  3. Relación no permitida        -> un proveedor no puede requerir un producto
  4. Ciclo                        -> alerta útil y SIN lista de pasos (no hay orden falso)
  5. Se corrige el ciclo          -> vuelve el orden válido

Cómo ejecutarlo
---------------
1. En una terminal, levanta la API (desde esta carpeta):

   py -m uvicorn main:app --port 8000

2. En OTRA terminal:

   py aceptacion_feature3.py

El grafo vive en memoria: si un ensayo anterior dejó un ciclo, reinicia
uvicorn antes de correr el script.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"

resultados = []

ETAPAS_PAN = [
    ["PRC-AMASAR"],
    ["PRC-FERMENTAR"],
    ["PRC-HORNEAR"],
    ["PRC-TAJAR"],
    ["PRC-EMPACAR"],
]


def pedir(metodo: str, ruta: str, cuerpo: dict | None = None):
    """Hace GET, POST o DELETE. Devuelve (codigo_http, cuerpo_de_la_api)."""
    data = None if cuerpo is None else json.dumps(cuerpo).encode("utf-8")
    headers = {"Content-Type": "application/json"} if cuerpo is not None else {}
    req = urllib.request.Request(
        f"{BASE}{ruta}",
        data=data,
        method=metodo,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            texto = resp.read().decode("utf-8")
            return resp.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as e:
        texto = e.read().decode("utf-8")
        try:
            respuesta = json.loads(texto)
        except json.JSONDecodeError:
            return e.code, texto
        return e.code, respuesta.get("detail", respuesta)
    except urllib.error.URLError:
        return None, "No se pudo conectar. ¿Está corriendo uvicorn?"


def escenario(numero: int, titulo: str, que_hacemos: str, metodo: str, ruta: str,
              cuerpo, codigo_esperado: int, por_que: str, revisar=None):
    codigo, mensaje = pedir(metodo, ruta, cuerpo)
    paso = codigo == codigo_esperado
    extra = ""
    if paso and revisar is not None:
        ok_extra, extra = revisar(mensaje)
        paso = paso and ok_extra

    resultados.append(paso)

    enviado = f"{metodo} {ruta}"
    if cuerpo is not None:
        enviado += f" {json.dumps(cuerpo, ensure_ascii=False)}"

    print("-" * 70)
    print(f"[{numero}] {titulo}")
    print(f"Qué hacemos : {que_hacemos}")
    print(f"Enviamos    : {enviado}")
    print(f"Esperábamos : {codigo_esperado} ({por_que})")
    print(f"Obtuvimos   : {codigo} {mensaje}")
    if extra:
        print(f"Revisamos   : {extra}")
    print(f"Resultado   : {'PASÓ' if paso else 'FALLÓ'}")
    return codigo, mensaje, paso


def es_orden_del_pan(cuerpo):
    etapas = cuerpo.get("etapas") if isinstance(cuerpo, dict) else None
    caso = cuerpo.get("caso") if isinstance(cuerpo, dict) else None
    if caso == "orden_valido" and etapas == ETAPAS_PAN:
        return True, "caso orden_valido y etapas Amasar → … → Empacar"
    return False, f"se esperaba orden_valido con las 5 etapas del pan, llegó caso={caso} etapas={etapas}"


def es_ciclo_sin_orden_falso(cuerpo):
    if not isinstance(cuerpo, dict):
        return False, "la respuesta no es un JSON de orden"
    caso = cuerpo.get("caso")
    etapas = cuerpo.get("etapas")
    ciclos = cuerpo.get("ciclos") or []
    ids = ciclos[0].get("ids") if ciclos else []
    if caso == "ciclo" and etapas is None and ids:
        return True, f"caso ciclo, etapas=null (no hay orden falso), ciclo={ids}"
    return False, f"se esperaba ciclo con etapas null, llegó caso={caso} etapas={etapas} ciclos={ciclos}"


def main():
    print("=" * 70)
    print("ACEPTACIÓN FEATURE 3 — Orden de trabajo válido o alerta de ciclo")
    print(f"API: {BASE}")
    print("=" * 70)

    escenario(
        1, "Escenario normal (acíclico): orden de trabajo válido",
        "Consultar el orden de preparación del pan tajado (Amasar, Fermentar, Hornear, Tajar, Empacar)",
        "GET", "/orden-produccion", None,
        200, "las dependencias no forman ciclo: hay un orden topológico",
        es_orden_del_pan,
    )

    escenario(
        2, "Nodo inexistente",
        "Intentar que un proceso que no existe requiera Amasar",
        "POST", "/dependencias",
        {"origen": "PRC-NO-EXISTE", "destino": "PRC-AMASAR"},
        404, "no se puede depender de un elemento que no está en el catálogo",
    )

    escenario(
        3, "Relación no permitida",
        "Un proveedor no puede requerir un producto (la flecha iría al revés del negocio)",
        "POST", "/dependencias",
        {"origen": "PRV-QUIM", "destino": "PRD-PAN"},
        422, "un proveedor no puede requerir un producto",
    )

    _, arista, creo_ciclo = escenario(
        4, "Ciclo: alerta útil y sin orden falso",
        "Registrar que Amasar requiere Hornear, lo que cierra el círculo con Fermentar",
        "POST", "/dependencias",
        {"origen": "PRC-AMASAR", "destino": "PRC-HORNEAR"},
        201, "la API acepta la flecha; el ciclo lo reporta el orden, no el registro",
    )

    if creo_ciclo and isinstance(arista, dict) and arista.get("id"):
        escenario(
            5, "Tras el ciclo: consultar el orden",
            "Volver a pedir el orden: debe avisar el ciclo y no inventar una lista de pasos",
            "GET", "/orden-produccion", None,
            200, "hay contradicción: caso ciclo y etapas vacías (null)",
            es_ciclo_sin_orden_falso,
        )

        escenario(
            6, "Se quita la flecha del ciclo y vuelve el orden válido",
            "Quitar la dependencia Amasar → Hornear y consultar el orden otra vez",
            "DELETE", f"/dependencias/{arista['id']}", None,
            200, "al romper el ciclo, el grafo vuelve a ser acíclico",
        )

        escenario(
            7, "Orden válido otra vez",
            "Confirmar que el orden del pan tajado volvió a ser el de siempre",
            "GET", "/orden-produccion", None,
            200, "sin ciclo, otra vez hay orden de trabajo",
            es_orden_del_pan,
        )
    else:
        print("-" * 70)
        print("[5-7] No se corrieron: no se pudo crear la dependencia del ciclo.")
        resultados.extend([False, False, False])

    print("=" * 70)
    print(f"Resumen: {sum(resultados)} de {len(resultados)} escenarios PASARON")
    print("=" * 70)


if __name__ == "__main__":
    main()
