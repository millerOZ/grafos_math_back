"""
Pruebas de aceptación de la Feature 4 (tablero demostrable).

El brief pide ejecutar aceptación para cuatro casos:

  1. cadena válida        → TestCadenaValida
  2. elemento inexistente → TestElementoInexistente
  3. dato inválido        → TestDatoInvalido
  4. ciclo                → TestCiclo

y un criterio de éxito del cliente: "se carga una dependencia, se simula una
indisponibilidad y se identifican consecuencias. Después se muestra un orden
válido o una alerta clara de ciclo" → TestGuionDeLaDemo.

Igual que el resto de las pruebas, se llama directamente a las funciones de
los endpoints de `main.py` (no se levanta el servidor). Cada prueba empieza
desde los datos de la demo (`reiniciar_grafo`) y al terminar restaura el grafo.

Sobre los códigos HTTP:
  - Las funciones de los endpoints lanzan `HTTPException` con el código (404,
    409, 422) y eso es lo que se verifica.
  - Los 422 por cuerpo mal formado (id vacío, sin prefijo...) los produce
    FastAPI cuando el modelo de entrada (pydantic) no valida: aquí se verifica
    que el modelo lance `ValidationError`, que FastAPI convierte en 422.
"""

import os
import unittest
from unittest import mock

from fastapi import HTTPException
from pydantic import ValidationError

from data import MOCK_GRAFO, reiniciar_grafo
from main import (
    crear_dependencia,
    crear_insumo,
    crear_producto,
    crear_proveedor,
    eliminar_dependencia,
    obtener_grafo,
    obtener_impacto,
    obtener_impacto_sin_id,
    obtener_orden_produccion,
    reiniciar_demo,
)
from models import DependenciaCreate, InsumoCreate, ProductoCreate, ProveedorCreate
from test_dependencias import GrafoAisladoTestCase


ORDEN_PAN = [["PRC-AMASAR"], ["PRC-FERMENTAR"], ["PRC-HORNEAR"], ["PRC-TAJAR"], ["PRC-EMPACAR"]]


class AceptacionTestCase(GrafoAisladoTestCase):
    """Parte siempre de los datos de la demo y ofrece verificaciones comunes."""

    def setUp(self):
        super().setUp()
        reiniciar_grafo()

    def assert_http(self, codigo, llamada):
        with self.assertRaises(HTTPException) as ctx:
            llamada()
        self.assertEqual(ctx.exception.status_code, codigo)
        return ctx.exception.detail

    def assert_grafo_sin_cambios(self, antes):
        self.assertEqual(MOCK_GRAFO.model_dump(), antes)

    def assert_caminos_siguen_las_dependencias(self, impacto):
        """Cada paso del camino de la falla es una dependencia real: el siguiente REQUIERE al anterior."""
        requiere = {(a.origen, a.destino) for a in MOCK_GRAFO.aristas}
        for afectado in impacto.afectados:
            self.assertEqual(afectado.camino[0], impacto.origen.id)
            self.assertEqual(afectado.camino[-1], afectado.id)
            self.assertEqual(afectado.nivel, len(afectado.camino) - 1)
            for causa, consecuencia in zip(afectado.camino, afectado.camino[1:]):
                self.assertIn((consecuencia, causa), requiere, f"{consecuencia} no requiere {causa}")


class TestCadenaValida(AceptacionTestCase):
    """Se carga una dependencia válida: el impacto la recorre y el orden la respeta."""

    def setUp(self):
        super().setUp()
        # "Para producir tostadas integrales necesito hornear."
        self.arista = crear_dependencia(DependenciaCreate(origen="PRD-TOSTADAS", destino="PRC-HORNEAR"))

    def test_la_dependencia_queda_en_el_grafo_con_el_id_del_back(self):
        grafo = obtener_grafo()

        self.assertIn(self.arista, grafo.aristas)
        self.assertEqual(self.arista.tipo, "REQUIERE")
        self.assertEqual(len({a.id for a in grafo.aristas}), len(grafo.aristas))

    def test_la_falla_recorre_la_cadena_hasta_los_productos(self):
        r = obtener_impacto("INS-LEVADURA")

        self.assertEqual(r.caso, "afecta_cadena")
        self.assertEqual(r.visitados[0], "INS-LEVADURA")
        afectados = {a.id: a for a in r.afectados}
        self.assertEqual(
            set(afectados),
            {"PRC-AMASAR", "PRC-FERMENTAR", "PRC-HORNEAR", "PRC-TAJAR", "PRC-EMPACAR", "PRD-PAN", "PRD-TOSTADAS"},
        )
        # Las tostadas ahora se afectan a través del horneado que se acaba de cargar.
        self.assertEqual(
            afectados["PRD-TOSTADAS"].camino,
            ["INS-LEVADURA", "PRC-AMASAR", "PRC-FERMENTAR", "PRC-HORNEAR", "PRD-TOSTADAS"],
        )
        # Lo que no usa levadura sigue produciéndose.
        self.assertNotIn("PRD-GALLETA", afectados)
        self.assertNotIn("PRD-PONQUE", afectados)
        self.assert_caminos_siguen_las_dependencias(r)

    def test_sin_dependientes_se_distingue_de_afecta_cadena(self):
        r = obtener_impacto("PRD-PAN")

        self.assertEqual(r.caso, "sin_dependencias")
        self.assertEqual(r.afectados, [])

    def test_el_orden_de_produccion_es_valido(self):
        r = obtener_orden_produccion()

        self.assertEqual(r.caso, "orden_valido")
        self.assertEqual(r.etapas, ORDEN_PAN)
        self.assertEqual(r.ciclos, [])
        planes = {p.producto.id: p for p in r.planes}
        self.assertEqual(planes["PRD-TOSTADAS"].etapas, [["PRC-AMASAR"], ["PRC-FERMENTAR"], ["PRC-HORNEAR"]])
        self.assertEqual(planes["PRD-PAN"].etapas, ORDEN_PAN)


class TestElementoInexistente(AceptacionTestCase):
    """Un id con buen formato que no está en el catálogo da 404 y no cambia nada."""

    def test_impacto_de_un_elemento_inexistente(self):
        detalle = self.assert_http(404, lambda: obtener_impacto("PRV-NO-EXISTE"))
        self.assertIn("PRV-NO-EXISTE", detalle)

    def test_dependencia_con_origen_o_destino_inexistente(self):
        antes = MOCK_GRAFO.model_dump()

        self.assert_http(404, lambda: crear_dependencia(DependenciaCreate(origen="PRD-NO-EXISTE", destino="INS-HARINA")))
        self.assert_http(404, lambda: crear_dependencia(DependenciaCreate(origen="PRD-PAN", destino="INS-NO-EXISTE")))

        self.assert_grafo_sin_cambios(antes)

    def test_elementos_que_referencian_algo_inexistente(self):
        antes = MOCK_GRAFO.model_dump()

        self.assert_http(404, lambda: crear_insumo(
            InsumoCreate(id="INS-MANTEQUILLA", nombre="Mantequilla", proveedor_id="PRV-NO-EXISTE")))
        self.assert_http(404, lambda: crear_producto(
            ProductoCreate(id="PRD-CROISSANT", nombre="Croissant", insumo_ids=["INS-HARINA", "INS-NO-EXISTE"])))

        # El producto no se crea a medias: ni el nodo ni la arista hacia la harina.
        self.assert_grafo_sin_cambios(antes)

    def test_quitar_una_dependencia_inexistente(self):
        antes = MOCK_GRAFO.model_dump()

        self.assert_http(404, lambda: eliminar_dependencia("e999"))

        self.assert_grafo_sin_cambios(antes)


class TestDatoInvalido(AceptacionTestCase):
    """Datos mal formados o que contradicen las reglas: 422/409, nunca se confunden con 404."""

    def test_impacto_con_id_mal_formado_es_422_y_no_404(self):
        for elemento_id in ["   ", "PRV QUIM", "prv-quim", "PRV-", "XYZ-HARINA"]:
            with self.subTest(elemento_id=elemento_id):
                detalle = self.assert_http(422, lambda: obtener_impacto(elemento_id))
                self.assertEqual(detalle[0]["type"], "id_invalido")

        self.assert_http(422, obtener_impacto_sin_id)

    def test_crear_elementos_con_datos_mal_formados(self):
        casos = [
            lambda: ProveedorCreate(id="", nombre="Molino"),
            lambda: ProveedorCreate(id="PRV MOLINO", nombre="Molino"),
            lambda: ProveedorCreate(id="INS-MOLINO", nombre="Molino"),  # prefijo de otra capa
            lambda: ProveedorCreate(id="PRV-MOLINO", nombre=""),
            lambda: InsumoCreate(id="INS-MANTEQUILLA", nombre="Mantequilla", proveedor_id="prv-quim"),
            lambda: ProductoCreate(id="PRD-CROISSANT", nombre="Croissant", insumo_ids=[]),
            lambda: DependenciaCreate(origen="", destino="INS-HARINA"),
        ]
        for i, crear in enumerate(casos):
            with self.subTest(caso=i):
                with self.assertRaises(ValidationError):
                    crear()

    def test_dependencia_que_rompe_la_regla_de_capas(self):
        antes = MOCK_GRAFO.model_dump()

        # "Para producir la distribuidora necesito pan tajado" no tiene sentido.
        self.assert_http(422, lambda: crear_dependencia(DependenciaCreate(origen="PRV-QUIM", destino="PRD-PAN")))
        # Un insumo no requiere un producto.
        self.assert_http(422, lambda: crear_dependencia(DependenciaCreate(origen="INS-HARINA", destino="PRD-PAN")))

        self.assert_grafo_sin_cambios(antes)

    def test_dependencia_y_elemento_repetidos(self):
        antes = MOCK_GRAFO.model_dump()

        self.assert_http(409, lambda: crear_dependencia(DependenciaCreate(origen="PRD-GALLETA", destino="INS-HARINA")))
        self.assert_http(409, lambda: crear_proveedor(ProveedorCreate(id="PRV-QUIM", nombre="Otra distribuidora")))

        self.assert_grafo_sin_cambios(antes)


class TestCiclo(AceptacionTestCase):
    """Una dependencia contradictoria se acepta, se reporta con información útil y se puede corregir."""

    def setUp(self):
        super().setUp()
        # "Para amasar necesito hornear": contradice Hornear → Fermentar → Amasar.
        self.arista = crear_dependencia(DependenciaCreate(origen="PRC-AMASAR", destino="PRC-HORNEAR"))

    def test_alerta_de_ciclo_sin_orden_falso(self):
        r = obtener_orden_produccion()

        self.assertEqual(r.caso, "ciclo")
        self.assertIsNone(r.etapas)
        self.assertEqual([c.ids for c in r.ciclos], [["PRC-AMASAR", "PRC-HORNEAR", "PRC-FERMENTAR"]])
        self.assertEqual(r.en_ciclo, ["PRC-AMASAR", "PRC-FERMENTAR", "PRC-HORNEAR"])
        self.assertIn("Amasar necesita Hornear", r.ciclos[0].descripcion)
        self.assertIn("Pan tajado", r.mensaje)

    def test_solo_se_bloquean_los_productos_que_usan_el_ciclo(self):
        r = obtener_orden_produccion()

        pan = next(p for p in r.planes if p.producto.id == "PRD-PAN")
        self.assertIsNone(pan.etapas)
        self.assertEqual(pan.bloqueado_por, [0])
        # Galletas, ponqué y tostadas no usan procesos: no quedan bloqueados.
        self.assertEqual({p.id for p in r.sin_procesos}, {"PRD-GALLETA", "PRD-PONQUE", "PRD-TOSTADAS"})

    def test_el_impacto_no_entra_en_bucle(self):
        r = obtener_impacto("INS-LEVADURA")

        self.assertEqual(r.caso, "afecta_cadena")
        self.assertEqual(len(r.visitados), len(set(r.visitados)))
        self.assertIn("PRD-PAN", r.visitados)
        self.assert_caminos_siguen_las_dependencias(r)

    def test_quitar_la_dependencia_contradictoria_recupera_el_orden(self):
        eliminar_dependencia(self.arista.id)

        r = obtener_orden_produccion()
        self.assertEqual(r.caso, "orden_valido")
        self.assertEqual(r.etapas, ORDEN_PAN)


class TestGuionDeLaDemo(AceptacionTestCase):
    """El criterio de éxito del cliente, en el mismo orden en que se muestra en la demo."""

    def test_guion_completo(self):
        inicial = obtener_grafo().model_dump()

        # 1. Se carga una dependencia.
        nueva = crear_dependencia(DependenciaCreate(origen="PRD-TOSTADAS", destino="PRC-HORNEAR"))
        self.assertIn(nueva, obtener_grafo().aristas)

        # 2. Se simula una indisponibilidad y se identifican consecuencias.
        impacto = obtener_impacto("INS-LEVADURA")
        self.assertEqual(impacto.caso, "afecta_cadena")
        self.assertTrue({"PRD-PAN", "PRD-TOSTADAS"} <= {a.id for a in impacto.afectados})

        # 3. Se muestra un orden válido.
        self.assertEqual(obtener_orden_produccion().caso, "orden_valido")

        # 4. Se carga una dependencia contradictoria y aparece la alerta clara de ciclo.
        contradiccion = crear_dependencia(DependenciaCreate(origen="PRC-AMASAR", destino="PRC-HORNEAR"))
        orden = obtener_orden_produccion()
        self.assertEqual(orden.caso, "ciclo")
        self.assertIsNone(orden.etapas)
        self.assertTrue(orden.ciclos[0].descripcion)

        # 5. Se corrige quitando esa dependencia y vuelve el orden válido.
        eliminar_dependencia(contradiccion.id)
        self.assertEqual(obtener_orden_produccion().caso, "orden_valido")

        # 6. Reiniciar la demo deja todo como al principio.
        with mock.patch.dict(os.environ, {"DEMO_RESET_TOKEN": "clave-demo"}):
            reiniciar_demo(x_demo_token="clave-demo")
        self.assertEqual(obtener_grafo().model_dump(), inicial)


if __name__ == "__main__":
    unittest.main()
