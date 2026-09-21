from models import Grafo

MOCK_GRAFO = Grafo(
    nodos=[
        # --- Productos ---
        {"id": "PRD-PAN", "nombre": "Pan tajado", "capa": "producto", "categoria": "Panadería"},
        {"id": "PRD-GALLETA", "nombre": "Galletas dulces", "capa": "producto", "categoria": "Repostería"},
        {"id": "PRD-PONQUE", "nombre": "Ponqué artesanal", "capa": "producto", "categoria": "Repostería"},
        {"id": "PRD-TOSTADAS", "nombre": "Tostadas integrales", "capa": "producto", "categoria": "Panadería"},

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
        {"id": "e01", "origen": "PRD-PAN", "destino": "INS-HARINA", "tipo": "REQUIERE"},
        {"id": "e02", "origen": "PRD-PAN", "destino": "INS-LEVADURA", "tipo": "REQUIERE"},
        {"id": "e03", "origen": "PRD-PAN", "destino": "INS-EMPAQUE", "tipo": "REQUIERE"},
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
    ],
)