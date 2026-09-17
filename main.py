from fastapi import FastAPI 

app = FastAPI() 
node = [
    {'id': 'PRD-AREPA', 'nombre': 'Arepa paisa', 'capa': 'producto', 'categoria': 'Alimento tradicional'},
    {'id': 'PRD-PAN', 'nombre': 'Pan campesino', 'capa': 'producto', 'categoria': 'Panadería'},
    {'id': 'PRD-GALLETA', 'nombre': 'Galleta de avena', 'capa': 'producto', 'categoria': 'Panadería'},
    {'id': 'PRD-BROWNIE', 'nombre': 'Brownie de cacao', 'capa': 'producto', 'categoria': 'Repostería'},
    {'id': 'PRD-PIZZA', 'nombre': 'Pizza paisa', 'capa': 'producto', 'categoria': 'Comida preparada'},
    {'id': 'PRD-CAFE', 'nombre': 'Café molido empacado', 'capa': 'producto', 'categoria': 'Producto empacado'},

    {'id': 'INS-MAIZ', 'nombre': 'Harina de maíz', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'INS-HARINA', 'nombre': 'Harina de trigo', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'INS-AZUCAR', 'nombre': 'Azúcar', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'INS-CACAO', 'nombre': 'Cacao en polvo', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'INS-QUESO', 'nombre': 'Queso campesino', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'INS-CAFE', 'nombre': 'Café verde', 'capa': 'insumo', 'categoria': 'Materia prima'},
    {'id': 'PROC-MEZCLA', 'nombre': 'Mezclado y amasado', 'capa': 'insumo', 'categoria': 'Proceso interno'},
    {'id': 'PROC-HORNEADO', 'nombre': 'Horneado', 'capa': 'insumo', 'categoria': 'Proceso interno'},
    {'id': 'PROC-MOLIENDA', 'nombre': 'Molienda', 'capa': 'insumo', 'categoria': 'Proceso interno'},
    {'id': 'PROC-EMPAQUE', 'nombre': 'Empaque', 'capa': 'insumo', 'categoria': 'Proceso interno'},
    {'id': 'PROC-CALIDAD', 'nombre': 'Control de calidad', 'capa': 'insumo', 'categoria': 'Proceso interno'},
    {'id': 'PROC-DESPACHO', 'nombre': 'Despacho desde Medellín', 'capa': 'insumo', 'categoria': 'Proceso interno'},

    {'id': 'PRV-MAIZ', 'nombre': 'Cooperativa Maicera de Antioquia', 'capa': 'proveedor', 'categoria': 'Granos'},
    {'id': 'PRV-HARINA', 'nombre': 'Molinos del Valle', 'capa': 'proveedor', 'categoria': 'Harinas'},
    {'id': 'PRV-AZUCAR', 'nombre': 'Ingenio del Cauca', 'capa': 'proveedor', 'categoria': 'Endulzantes'},
    {'id': 'PRV-CACAO', 'nombre': 'Cacao de Santander', 'capa': 'proveedor', 'categoria': 'Cacao'},
    {'id': 'PRV-LACTEOS', 'nombre': 'Lácteos del Norte de Antioquia', 'capa': 'proveedor', 'categoria': 'Refrigerados'},
    {'id': 'PRV-SERVICIOS', 'nombre': 'Servicios operativos de Medellín', 'capa': 'proveedor', 'categoria': 'Calidad y logística'},
]
aristas = [
    # Dirección elegida: A -> B significa "A requiere B".
    # Producto -> proceso o insumo
    {"id": "e01", "origen": "PRD-AREPA", "destino": "PROC-MEZCLA", "tipo": "REQUIERE"},
    {"id": "e02", "origen": "PRD-AREPA", "destino": "PROC-EMPAQUE", "tipo": "REQUIERE"},
    {"id": "e03", "origen": "PRD-PAN", "destino": "PROC-HORNEADO", "tipo": "REQUIERE"},
    {"id": "e04", "origen": "PRD-PAN", "destino": "PROC-EMPAQUE", "tipo": "REQUIERE"},
    {"id": "e05", "origen": "PRD-GALLETA", "destino": "PROC-HORNEADO", "tipo": "REQUIERE"},
    {"id": "e06", "origen": "PRD-GALLETA", "destino": "INS-AZUCAR", "tipo": "REQUIERE"},
    {"id": "e07", "origen": "PRD-BROWNIE", "destino": "PROC-HORNEADO", "tipo": "REQUIERE"},
    {"id": "e08", "origen": "PRD-BROWNIE", "destino": "INS-CACAO", "tipo": "REQUIERE"},
    {"id": "e09", "origen": "PRD-PIZZA", "destino": "PROC-MEZCLA", "tipo": "REQUIERE"},
    {"id": "e10", "origen": "PRD-PIZZA", "destino": "INS-QUESO", "tipo": "REQUIERE"},
    {"id": "e11", "origen": "PRD-CAFE", "destino": "PROC-MOLIENDA", "tipo": "REQUIERE"},
    {"id": "e12", "origen": "PRD-CAFE", "destino": "PROC-EMPAQUE", "tipo": "REQUIERE"},
    # Proceso -> insumo/proceso/proveedor
    {"id": "e13", "origen": "PROC-MEZCLA", "destino": "INS-MAIZ", "tipo": "REQUIERE"},
    {"id": "e14", "origen": "PROC-MEZCLA", "destino": "INS-QUESO", "tipo": "REQUIERE"},
    {"id": "e15", "origen": "PROC-HORNEADO", "destino": "INS-HARINA", "tipo": "REQUIERE"},
    {"id": "e16", "origen": "PROC-HORNEADO", "destino": "INS-AZUCAR", "tipo": "REQUIERE"},
    {"id": "e17", "origen": "PROC-MOLIENDA", "destino": "INS-CAFE", "tipo": "REQUIERE"},
    {"id": "e18", "origen": "PROC-EMPAQUE", "destino": "PROC-CALIDAD", "tipo": "REQUIERE"},
    {"id": "e19", "origen": "PROC-CALIDAD", "destino": "PRV-SERVICIOS", "tipo": "REQUIERE"},
    {"id": "e20", "origen": "PROC-DESPACHO", "destino": "PRV-SERVICIOS", "tipo": "REQUIERE"},
    {"id": "e21", "origen": "INS-MAIZ", "destino": "PRV-MAIZ", "tipo": "REQUIERE"},
    {"id": "e22", "origen": "INS-HARINA", "destino": "PRV-HARINA", "tipo": "REQUIERE"},
    {"id": "e23", "origen": "INS-AZUCAR", "destino": "PRV-AZUCAR", "tipo": "REQUIERE"},
    {"id": "e24", "origen": "INS-CACAO", "destino": "PRV-CACAO", "tipo": "REQUIERE"},
    {"id": "e25", "origen": "INS-QUESO", "destino": "PRV-LACTEOS", "tipo": "REQUIERE"},
    {"id": "e26", "origen": "INS-CAFE", "destino": "PRV-MAIZ", "tipo": "REQUIERE"},
    {"id": "e27", "origen": "PROC-HORNEADO", "destino": "PRV-SERVICIOS", "tipo": "REQUIERE"},
    {"id": "e28", "origen": "PROC-EMPAQUE", "destino": "PROC-DESPACHO", "tipo": "REQUIERE"},
]
@app.get("/list-nodos") 
def read_root(): 
    return {'node': node, 'aristas': aristas} 
