from typing import Optional

from models import Arista, Grafo, Nodo


MOCK_GRAFO = Grafo(
    nodos=[
        # --- Productos ---
        {"id": "PRD-PAN", "nombre": "Pan tajado", "capa": "producto", "categoria": "Panadería"},
        {"id": "PRD-GALLETA", "nombre": "Galletas dulces", "capa": "producto", "categoria": "Repostería"},
        {"id": "PRD-PONQUE", "nombre": "Ponqué artesanal", "capa": "producto", "categoria": "Repostería"},
        {"id": "PRD-TOSTADAS", "nombre": "Tostadas integrales", "capa": "producto", "categoria": "Panadería"},

        # --- Procesos internos (pasos que la panadería hace, no que compra) ---
        # Por ahora se modela la preparación del pan tajado; sirve de base para la F3.
        {"id": "PRC-AMASAR", "nombre": "Amasar", "capa": "proceso", "categoria": "Panadería"},
        {"id": "PRC-FERMENTAR", "nombre": "Fermentar la masa", "capa": "proceso", "categoria": "Panadería"},
        {"id": "PRC-HORNEAR", "nombre": "Hornear", "capa": "proceso", "categoria": "Panadería"},
        {"id": "PRC-TAJAR", "nombre": "Tajar", "capa": "proceso", "categoria": "Panadería"},
        {"id": "PRC-EMPACAR", "nombre": "Empacar", "capa": "proceso", "categoria": "Panadería"},

        # --- Insumos ---
        {"id": "INS-HARINA", "nombre": "Harina de trigo", "capa": "insumo", "categoria": "Materia prima"},
        {"id": "INS-AZUCAR", "nombre": "Azúcar refinada", "capa": "insumo", "categoria": "Materia prima"},
        {"id": "INS-LEVADURA", "nombre": "Levadura", "capa": "insumo", "categoria": "Materia prima"},
        {"id": "INS-EMPAQUE", "nombre": "Bolsas de empaque", "capa": "insumo", "categoria": "Empaque"},
        {"id": "INS-CONSERVANTE", "nombre": "Conservante alimentario", "capa": "insumo", "categoria": "Insumo químico"},

        # --- Proveedores ---
        {"id": "PRV-MATERIAPRIMA", "nombre": "Distribuidora de materias primas", "capa": "proveedor", "categoria": "Materia prima"},
        {"id": "PRV-EMPAQUES", "nombre": "Empaques Andinos", "capa": "proveedor", "categoria": "Empaque"},
        {"id": "PRV-QUIM", "nombre": "Distribuidora de químicos", "capa": "proveedor", "categoria": "Insumo químico"},
    ],
    aristas=[
        # Producto -> insumo
        # (el pan tajado ya no va directo a sus insumos: los consume a través de sus procesos)
        {"id": "e04", "origen": "PRD-GALLETA", "destino": "INS-HARINA", "tipo": "REQUIERE"},
        {"id": "e05", "origen": "PRD-GALLETA", "destino": "INS-AZUCAR", "tipo": "REQUIERE"},
        {"id": "e06", "origen": "PRD-GALLETA", "destino": "INS-EMPAQUE", "tipo": "REQUIERE"},
        {"id": "e07", "origen": "PRD-PONQUE", "destino": "INS-HARINA", "tipo": "REQUIERE"},
        {"id": "e08", "origen": "PRD-PONQUE", "destino": "INS-AZUCAR", "tipo": "REQUIERE"},
        {"id": "e09", "origen": "PRD-PONQUE", "destino": "INS-CONSERVANTE", "tipo": "REQUIERE"},
        {"id": "e10", "origen": "PRD-PONQUE", "destino": "INS-EMPAQUE", "tipo": "REQUIERE"},
        {"id": "e11", "origen": "PRD-TOSTADAS", "destino": "INS-HARINA", "tipo": "REQUIERE"},
        {"id": "e12", "origen": "PRD-TOSTADAS", "destino": "INS-CONSERVANTE", "tipo": "REQUIERE"},
        {"id": "e13", "origen": "PRD-TOSTADAS", "destino": "INS-EMPAQUE", "tipo": "REQUIERE"},

        # Insumo -> proveedor
        {"id": "e14", "origen": "INS-HARINA", "destino": "PRV-MATERIAPRIMA", "tipo": "REQUIERE"},
        {"id": "e15", "origen": "INS-AZUCAR", "destino": "PRV-MATERIAPRIMA", "tipo": "REQUIERE"},
        {"id": "e16", "origen": "INS-LEVADURA", "destino": "PRV-MATERIAPRIMA", "tipo": "REQUIERE"},
        {"id": "e17", "origen": "INS-EMPAQUE", "destino": "PRV-EMPAQUES", "tipo": "REQUIERE"},
        {"id": "e18", "origen": "INS-CONSERVANTE", "destino": "PRV-QUIM", "tipo": "REQUIERE"},

        # Pan tajado: producto -> proceso -> proceso ... -> insumo
        # "Para producir pan tajado necesito empacarlo; para empacar necesito tajar y bolsas; ..."
        {"id": "e19", "origen": "PRD-PAN", "destino": "PRC-EMPACAR", "tipo": "REQUIERE"},
        {"id": "e20", "origen": "PRC-EMPACAR", "destino": "PRC-TAJAR", "tipo": "REQUIERE"},
        {"id": "e21", "origen": "PRC-EMPACAR", "destino": "INS-EMPAQUE", "tipo": "REQUIERE"},
        {"id": "e22", "origen": "PRC-TAJAR", "destino": "PRC-HORNEAR", "tipo": "REQUIERE"},
        {"id": "e23", "origen": "PRC-HORNEAR", "destino": "PRC-FERMENTAR", "tipo": "REQUIERE"},
        {"id": "e24", "origen": "PRC-FERMENTAR", "destino": "PRC-AMASAR", "tipo": "REQUIERE"},
        {"id": "e25", "origen": "PRC-AMASAR", "destino": "INS-HARINA", "tipo": "REQUIERE"},
        {"id": "e26", "origen": "PRC-AMASAR", "destino": "INS-LEVADURA", "tipo": "REQUIERE"},
    ],
)

# Regla de capas: pares (capa_origen, capa_destino) permitidos para "origen REQUIERE destino".
# proceso -> proceso permite encadenar procesos; eso puede formar ciclos, y a propósito
# no se rechazan aquí: la F3 (orden y ciclos) los detecta y reporta.
REGLAS_CAPAS = {
    ("producto", "insumo"),
    ("producto", "proceso"),
    ("proceso", "proceso"),
    ("proceso", "insumo"),
    ("insumo", "proveedor"),
}


def capas_permitidas(capa_origen: str, capa_destino: str) -> bool:
    return (capa_origen, capa_destino) in REGLAS_CAPAS


def existe_arista(origen: str, destino: str) -> bool:
    return any(a.origen == origen and a.destino == destino for a in MOCK_GRAFO.aristas)


def buscar_nodo(id: str) -> Optional[Nodo]:
    return next((nodo for nodo in MOCK_GRAFO.nodos if nodo.id == id), None)


def existe_nodo(id: str) -> bool:
    return buscar_nodo(id) is not None


def siguiente_arista_id() -> str:
    # Se toma el mayor número usado y no la cantidad de aristas: los ids no son
    # consecutivos (ej. e01-e03 ya no existen), y contar daría ids repetidos.
    numeros = [int(a.id[1:]) for a in MOCK_GRAFO.aristas if a.id[1:].isdigit()]
    return f"e{max(numeros, default=0) + 1:02d}"


def agregar_nodo(nodo: Nodo) -> None:
    MOCK_GRAFO.nodos.append(nodo)


def agregar_arista(origen: str, destino: str) -> Arista:
    arista = Arista(id=siguiente_arista_id(), origen=origen, destino=destino, tipo="REQUIERE")
    MOCK_GRAFO.aristas.append(arista)
    return arista

def quitar_arista(id: str) -> Optional[Arista]:
    """Quita la arista con ese id y la devuelve; None si no existe."""
    arista = next((a for a in MOCK_GRAFO.aristas if a.id == id), None)
    if arista is not None:
        MOCK_GRAFO.aristas.remove(arista)
    return arista
