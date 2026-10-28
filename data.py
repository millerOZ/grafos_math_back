from typing import Optional

from models import Arista, Grafo, Nodo


MOCK_GRAFO = Grafo(
    nodos=[
        # --- Productos ---
        {"id": "PRD-PANDEBONO", "nombre": "Pandebono", "capa": "producto", "categoria": "Panadería tradicional"},
        {"id": "PRD-ALMOJABANA", "nombre": "Almojábana", "capa": "producto", "categoria": "Panadería tradicional"},
        {"id": "PRD-PAN-ALINADO", "nombre": "Pan aliñado", "capa": "producto", "categoria": "Panadería tradicional"},
        {"id": "PRD-CROISSANT", "nombre": "Croissant de mantequilla", "capa": "producto", "categoria": "Panadería artesanal"},
        {"id": "PRD-PAIN-CHOCOLAT", "nombre": "Pain au chocolat", "capa": "producto", "categoria": "Panadería artesanal"},
        {"id": "PRD-MILHOJAS", "nombre": "Milhojas", "capa": "producto", "categoria": "Repostería"},
        {"id": "PRD-CAPPUCCINO", "nombre": "Cappuccino / Latte", "capa": "producto", "categoria": "Cafetería"},
        {"id": "PRD-CHOCOLATE-QUESO", "nombre": "Chocolate caliente con queso", "capa": "producto", "categoria": "Cafetería"},

        # --- Insumos ---
        {"id": "INS-HARINA-FUERZA", "nombre": "Harina de trigo de alta fuerza", "capa": "insumo", "categoria": "Harinas"},
        {"id": "INS-HARINA-MAIZ", "nombre": "Harina de maíz", "capa": "insumo", "categoria": "Harinas"},
        {"id": "INS-ALMIDON-YUCA", "nombre": "Almidón de yuca", "capa": "insumo", "categoria": "Harinas"},
        {"id": "INS-MANTEQUILLA", "nombre": "Mantequilla", "capa": "insumo", "categoria": "Lácteos"},
        {"id": "INS-QUESO-COSTENO", "nombre": "Queso costeño", "capa": "insumo", "categoria": "Lácteos"},
        {"id": "INS-CUAJADA", "nombre": "Cuajada fresca", "capa": "insumo", "categoria": "Lácteos"},
        {"id": "INS-LECHE", "nombre": "Leche y crema de leche", "capa": "insumo", "categoria": "Lácteos"},
        {"id": "INS-LEVADURA", "nombre": "Levadura (Levapan / Saf-Instant)", "capa": "insumo", "categoria": "Materia prima"},
        {"id": "INS-CHOCOLATE", "nombre": "Chocolate", "capa": "insumo", "categoria": "Materia prima"},
       

        # --- Proveedores ---
        {"id": "PRV-HARINERA-VALLE", "nombre": "Organización Cárdenas / Harinera del Valle", "capa": "proveedor", "categoria": "Harinas"},
        {"id": "PRV-COLANTA", "nombre": "Colanta", "capa": "proveedor", "categoria": "Lácteos"},
        {"id": "PRV-INSUPAN", "nombre": "Insupan (Itagüí / Medellín)", "capa": "proveedor", "categoria": "Distribuidor de insumos"},
        {"id": "PRV-PANADERO-MAYORISTA", "nombre": "El Panadero La Mayorista", "capa": "proveedor", "categoria": "Distribuidor de insumos"}
    ],
    aristas=[
        # Producto -> insumo
        {"id": "e01", "origen": "PRD-PANDEBONO", "destino": "INS-ALMIDON-YUCA", "tipo": "REQUIERE"},
        {"id": "e02", "origen": "PRD-PANDEBONO", "destino": "INS-HARINA-MAIZ", "tipo": "REQUIERE"},
        {"id": "e03", "origen": "PRD-PANDEBONO", "destino": "INS-QUESO-COSTENO", "tipo": "REQUIERE"},
        {"id": "e04", "origen": "PRD-ALMOJABANA", "destino": "INS-CUAJADA", "tipo": "REQUIERE"},
        {"id": "e05", "origen": "PRD-ALMOJABANA", "destino": "INS-HARINA-MAIZ", "tipo": "REQUIERE"},
        {"id": "e06", "origen": "PRD-PAN-ALINADO", "destino": "INS-HARINA-FUERZA", "tipo": "REQUIERE"},
        {"id": "e07", "origen": "PRD-PAN-ALINADO", "destino": "INS-MANTEQUILLA", "tipo": "REQUIERE"},
        {"id": "e08", "origen": "PRD-PAN-ALINADO", "destino": "INS-LEVADURA", "tipo": "REQUIERE"},
        {"id": "e09", "origen": "PRD-CROISSANT", "destino": "INS-HARINA-FUERZA", "tipo": "REQUIERE"},
        {"id": "e10", "origen": "PRD-CROISSANT", "destino": "INS-MANTEQUILLA", "tipo": "REQUIERE"},
        {"id": "e11", "origen": "PRD-CROISSANT", "destino": "INS-LEVADURA", "tipo": "REQUIERE"},
        {"id": "e12", "origen": "PRD-PAIN-CHOCOLAT", "destino": "INS-HARINA-FUERZA", "tipo": "REQUIERE"},
        {"id": "e13", "origen": "PRD-PAIN-CHOCOLAT", "destino": "INS-MANTEQUILLA", "tipo": "REQUIERE"},
        {"id": "e14", "origen": "PRD-PAIN-CHOCOLAT", "destino": "INS-CHOCOLATE", "tipo": "REQUIERE"},
        {"id": "e15", "origen": "PRD-MILHOJAS", "destino": "INS-HARINA-FUERZA", "tipo": "REQUIERE"},
        {"id": "e16", "origen": "PRD-MILHOJAS", "destino": "INS-MANTEQUILLA", "tipo": "REQUIERE"},
        {"id": "e17", "origen": "PRD-MILHOJAS", "destino": "INS-LECHE", "tipo": "REQUIERE"},
        {"id": "e18", "origen": "PRD-CAPPUCCINO", "destino": "INS-CAFE", "tipo": "REQUIERE"},
        {"id": "e19", "origen": "PRD-CAPPUCCINO", "destino": "INS-LECHE", "tipo": "REQUIERE"},
        {"id": "e20", "origen": "PRD-CHOCOLATE-QUESO", "destino": "INS-CHOCOLATE", "tipo": "REQUIERE"},
        {"id": "e21", "origen": "PRD-CHOCOLATE-QUESO", "destino": "INS-LECHE", "tipo": "REQUIERE"},
        {"id": "e22", "origen": "PRD-CHOCOLATE-QUESO", "destino": "INS-CUAJADA", "tipo": "REQUIERE"},

        # Insumo -> proveedor
        {"id": "e23", "origen": "INS-HARINA-FUERZA", "destino": "PRV-HARINERA-VALLE", "tipo": "REQUIERE"},
        {"id": "e24", "origen": "INS-HARINA-MAIZ", "destino": "PRV-PANADERO-MAYORISTA", "tipo": "REQUIERE"},
        {"id": "e25", "origen": "INS-ALMIDON-YUCA", "destino": "PRV-PANADERO-MAYORISTA", "tipo": "REQUIERE"},
        {"id": "e26", "origen": "INS-MANTEQUILLA", "destino": "PRV-COLANTA", "tipo": "REQUIERE"},
        {"id": "e27", "origen": "INS-QUESO-COSTENO", "destino": "PRV-COLANTA", "tipo": "REQUIERE"},
        {"id": "e28", "origen": "INS-CUAJADA", "destino": "PRV-COLANTA", "tipo": "REQUIERE"},
        {"id": "e29", "origen": "INS-LECHE", "destino": "PRV-COLANTA", "tipo": "REQUIERE"},
        {"id": "e30", "origen": "INS-LEVADURA", "destino": "PRV-INSUPAN", "tipo": "REQUIERE"},
        {"id": "e31", "origen": "INS-LEVADURA", "destino": "PRV-PANADERO-MAYORISTA", "tipo": "REQUIERE"},
        {"id": "e32", "origen": "INS-CHOCOLATE", "destino": "PRV-INSUPAN", "tipo": "REQUIERE"}
        
    ],
)

def buscar_nodo(id: str) -> Optional[Nodo]:
    return next((nodo for nodo in MOCK_GRAFO.nodos if nodo.id == id), None)


def existe_nodo(id: str) -> bool:
    return buscar_nodo(id) is not None


def siguiente_arista_id() -> str:
    return f"e{len(MOCK_GRAFO.aristas) + 1:02d}"


def agregar_nodo(nodo: Nodo) -> None:
    MOCK_GRAFO.nodos.append(nodo)


def agregar_arista(origen: str, destino: str) -> Arista:
    arista = Arista(id=siguiente_arista_id(), origen=origen, destino=destino, tipo="REQUIERE")
    MOCK_GRAFO.aristas.append(arista)
    return arista
