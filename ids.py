"""
Formato de los ids del catálogo.

Un id es el prefijo de su capa, un guion y uno o más segmentos en
mayúsculas o dígitos separados por guion:
    PRD-PAN, PRC-HORNEAR, INS-HARINA, PRV-MATERIAPRIMA, PRC-PRUEBA-A

La misma regla se usa al crear elementos (POST /productos, /procesos,
/insumos, /proveedores) y al consultar GET /impacto/{id}: así todo lo que
se crea se puede consultar, y un id mal escrito no se confunde con uno
que simplemente no existe.
"""

from __future__ import annotations

import re

PREFIJO_CAPA = {
    "producto": "PRD",
    "proceso": "PRC",
    "insumo": "INS",
    "proveedor": "PRV",
}

PATRON_ID = re.compile(r"(PRD|PRC|INS|PRV)-[A-Z0-9]+(-[A-Z0-9]+)*")


def validar_formato_id(elemento_id: str) -> str | None:
    """Devuelve el motivo por el que el id es inválido, o None si es válido."""
    if elemento_id.strip() == "":
        return "El id no puede estar vacío."
    if any(c.isspace() for c in elemento_id):
        return f"El id '{elemento_id}' no puede contener espacios."
    if not PATRON_ID.fullmatch(elemento_id):
        return (
            f"El id '{elemento_id}' no tiene un formato válido. Se espera "
            "PREFIJO-NOMBRE en mayúsculas, con prefijo PRD, PRC, INS o PRV "
            "(ej. PRV-MATERIAPRIMA)."
        )
    return None


def validar_id_para_capa(elemento_id: str, capa: str) -> str | None:
    """Como validar_formato_id, y además exige el prefijo de la capa (PRV- para un proveedor)."""
    motivo = validar_formato_id(elemento_id)
    if motivo is not None:
        return motivo
    prefijo = PREFIJO_CAPA[capa]
    if not elemento_id.startswith(f"{prefijo}-"):
        return f"El id de un {capa} debe empezar con '{prefijo}-' (ej. {prefijo}-NUEVO), no '{elemento_id}'."
    return None
