# Brief de cliente — AbastecePyme

## Cliente y problema

AbastecePyme fabrica productos sencillos y depende de materias primas, proveedores y procesos internos. Cuando un proveedor falla, el equipo no puede identificar rápidamente qué productos se afectan ni el orden correcto de preparación. Necesita visualizar dependencias y detectar configuraciones imposibles.

## Usuarios

- **Responsable de compras:** registra proveedores, insumos y dependencias.
- **Coordinador de producción:** consulta impacto y orden de preparación.

## Alcance

Datos sintéticos de proveedores, insumos, productos y relaciones de dependencia. No incluye inventario real, compras, facturación ni pronósticos. Cada relación debe tener una interpretación clara: “A requiere B” o “B habilita A”; documenten la dirección elegida.

## Feature 1 — Catálogo de dependencias

### Valor de negocio
El equipo puede registrar productos, insumos/proveedores y sus dependencias.

### Debe permitir

- crear/listar elementos con tipo y identificador único;
- registrar dependencias solo entre elementos válidos;
- validar relaciones repetidas y datos mal formados;
- mostrar la red de dependencias mediante API e interfaz mínima;
- justificar dirección de aristas y representación principal.

### Pistas, no receta

Escriban una frase completa para cada arista: “Para producir ___ necesito ___”. Si esa frase deja de tener sentido al invertirla, el grafo debe reflejarlo.

## Feature 2 — Análisis de impacto

### Valor de negocio
Ante la indisponibilidad de un elemento, producción identifica qué productos o procesos quedan afectados.

### Debe permitir

- consultar impacto desde un proveedor/insumo o hacia un producto, según su dirección definida;
- usar un recorrido propio y devolver elementos visitados de manera comprensible;
- diferenciar entre elemento inexistente, elemento sin dependencias y elemento que afecta una cadena;
- explicar en README qué significa “alcanzar” en este negocio.

### Pistas, no receta

La dirección de la relación define si recorren desde causa a consecuencia o al revés. No arreglen una dirección confusa con condicionales: revisen el modelo.

## Feature 3 — Orden y ciclos de producción

### Valor de negocio
El coordinador obtiene un orden válido de preparación o una alerta cuando las dependencias se contradicen.

### Debe permitir

- generar un orden de trabajo válido cuando las dependencias no formen ciclos;
- detectar y reportar un ciclo con información útil;
- no presentar un orden falso si hay contradicción;
- incluir pruebas de aceptación de un caso acíclico y uno cíclico.

### Pistas, no receta

Investiguen grafos dirigidos acíclicos y ordenamiento topológico. Antes de codificar, tracen qué elementos quedan sin requisitos pendientes en cada paso.

## Feature 4 — Tablero de abastecimiento demostrable

### Valor de negocio
El cliente comprende qué falla, qué se afecta y cómo debería organizar producción.

### Debe permitir

- integrar catálogo, impacto y orden/alerta de ciclo;
- visualizar dependencias y destacar la consulta relevante;
- adaptar el cambio de requisito docente;
- ejecutar aceptación para cadena válida, elemento inexistente, dato inválido y ciclo;
- entregar documentación, bitácora IA, video y pitch.

## Criterio de éxito del cliente

Durante la demo se carga una dependencia, se simula una indisponibilidad y se identifican consecuencias. Después se muestra un orden válido o una alerta clara de ciclo.

---

## Disponibilidad e impacto (producto)

Cuando un proveedor o un insumo deja de entregar, la panadería necesita saber qué productos o procesos quedan comprometidos. La API responde esa consulta de negocio.

### Qué significa “alcanzar” en este negocio

Alcanzar significa **“le llega la falla”**. Funciona como fichas de dominó.

Si la Distribuidora de químicos deja de entregar:

```
Distribuidora de químicos  ──►  Conservante  ──►  Ponqué
                                            └──►  Tostadas
```

1. Sin la distribuidora no hay **conservante**: la falla lo alcanza directamente.
2. Sin conservante no se pueden hacer el **ponqué** ni las **tostadas**: la falla los alcanza a través del conservante.
3. El **pan** no usa conservante, así que la falla **no lo alcanza** y se sigue produciendo.

Es decir, lo que se alcanza desde un elemento es todo lo que se cae si ese elemento falla.

La flecha del grafo es `A REQUIERE B` (producto → insumo → proveedor). El impacto se calcula **en contra** de esa flecha: del elemento no disponible hacia quienes lo necesitan.

### Endpoint

```
GET /impacto/{elemento_id}
```

| Caso | HTTP | Significado |
|---|---|---|
| `inexistente` | 404 | El id no está en el catálogo |
| `sin_dependencias` | 200 | Existe, pero nadie depende de él |
| `afecta_cadena` | 200 | Hay elementos alcanzados en `afectados` |

### Piezas del backend

| Archivo | Rol |
|---|---|
| `impacto.py` | Disponibilidad e impacto: distingue los tres casos y arma la respuesta. |
| `recorrido.py` | Recorrido BFS propio sobre la red de dependencias. |
| `main.py` | Expone `GET /impacto/{id}` junto al resto de la API. |
| `models.py` | Contratos de respuesta (`ImpactoResponse`, etc.). |

La interfaz debe consumir `GET /impacto/{id}` y usar `afectados` para resaltar la cadena.

### Cómo probar

```powershell
py -m uvicorn main:app --port 8000
```

Abrir http://127.0.0.1:8000/docs y probar, por ejemplo:

- `/impacto/PRV-MATERIAPRIMA` → afecta cadena
- `/impacto/PRD-PAN` → sin dependencias (nadie requiere al producto)
- `/impacto/NO-EXISTE` → 404

