"""
Pruebas de aceptación — Feature 1 (Catálogo de dependencias)
AbastecePyme / grafos_math_back

Qué hace
--------
Le manda peticiones a la API, como lo haría cualquier cliente, y revisa
si responde lo esperado. Hay un escenario por cada caso que pide la guía:

  1. Escenario normal       -> registrar una dependencia válida
  2. Nodo inexistente       -> depender de algo que no está en el catálogo
  3. Relación no permitida  -> depender de un elemento de la capa equivocada
  4. Dato inválido          -> usar un id que ya existe
  5. Ciclo                  -> intentar una flecha que no baja de capa

Cómo ejecutarlo
---------------
1. En una terminal, levanta la API (desde esta carpeta):

   py -3 -m uvicorn main:app --port 8000

2. En OTRA terminal:

   py -3 aceptacion_feature1.py
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"

resultados = []


def enviar(ruta: str, cuerpo: dict):
    """Hace un POST a la API. Devuelve (codigo_http, mensaje_de_la_api)."""
    req = urllib.request.Request(
        f"{BASE}{ruta}",
        data=json.dumps(cuerpo).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        respuesta = json.loads(e.read().decode("utf-8"))
        return e.code, respuesta.get("detail", respuesta)
    except urllib.error.URLError:
        return None, "No se pudo conectar. ¿Está corriendo uvicorn?"


def escenario(numero: int, titulo: str, que_hacemos: str, ruta: str, cuerpo: dict, codigo_esperado: int, por_que: str):
    codigo, mensaje = enviar(ruta, cuerpo)
    paso = codigo == codigo_esperado
    resultados.append(paso)

    print("-" * 70)
    print(f"[{numero}] {titulo}")
    print(f"Qué hacemos : {que_hacemos}")
    print(f"Enviamos    : POST {ruta} {json.dumps(cuerpo, ensure_ascii=False)}")
    print(f"Esperábamos : {codigo_esperado} ({por_que})")
    print(f"Obtuvimos   : {codigo} {mensaje}")
    print(f"Resultado   : {'PASÓ' if paso else 'FALLÓ'}")


def main():
    arepa = f"PRD-AREPA-{int(time.time()) % 10000}"

    print("=" * 70)
    print("ACEPTACIÓN FEATURE 1 — Registrar dependencias solo entre elementos válidos")
    print(f"API: {BASE}")
    print("=" * 70)

    escenario(
        1, "Escenario normal: registrar una dependencia válida",
        "Crear el producto Arepa, que requiere harina de trigo (un insumo que sí existe)",
        "/productos", {"id": arepa, "nombre": "Arepa", "insumo_ids": ["INS-HARINA"]},
        201, "se crea el producto y su dependencia Arepa -> Harina",
    )

    escenario(
        2, "Nodo inexistente",
        "Crear una arepa de maíz, pero el maíz no está en el catálogo",
        "/productos", {"id": "PRD-AREPA-MAIZ", "nombre": "Arepa de maíz", "insumo_ids": ["INS-MAIZ"]},
        404, "no se puede depender de algo que no existe: primero hay que registrar el maíz",
    )

    escenario(
        3, "Relación no permitida",
        "Crear un producto que requiere directamente a un proveedor (se salta el insumo)",
        "/productos", {"id": "PRD-GALLETA-QUIMICA", "nombre": "Galleta", "insumo_ids": ["PRV-QUIM"]},
        422, "un producto solo puede requerir insumos",
    )

    escenario(
        4, "Dato inválido: identificador repetido",
        "Crear un producto con el id PRD-PAN, que ya existe",
        "/productos", {"id": "PRD-PAN", "nombre": "Otro pan", "insumo_ids": ["INS-HARINA"]},
        409, "cada elemento tiene un id único",
    )

    escenario(
        5, "Ciclo",
        "Crear un insumo que requiere otro insumo (harina), en vez de un proveedor",
        "/insumos", {"id": "INS-MASA", "nombre": "Masa", "proveedor_id": "INS-HARINA"},
        422, "las flechas solo bajan de capa, así que no se puede cerrar un ciclo",
    )

    print("=" * 70)
    print(f"Resumen: {sum(resultados)} de {len(resultados)} escenarios PASARON")
    print("=" * 70)


if __name__ == "__main__":
    main()
