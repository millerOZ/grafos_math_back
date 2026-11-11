import unittest

from fastapi import HTTPException
from pydantic import ValidationError

from data import MOCK_GRAFO
from main import crear_dependencia, crear_proceso, eliminar_dependencia, listar_procesos
from models import DependenciaCreate, ProcesoCreate


class GrafoAisladoTestCase(unittest.TestCase):
    """El grafo es global en memoria: se guarda y se restaura en cada prueba."""

    def setUp(self):
        self._nodos = list(MOCK_GRAFO.nodos)
        self._aristas = list(MOCK_GRAFO.aristas)

    def tearDown(self):
        MOCK_GRAFO.nodos[:] = self._nodos
        MOCK_GRAFO.aristas[:] = self._aristas


class TestCrearProceso(GrafoAisladoTestCase):
    def test_crea_proceso_sin_aristas(self):
        total_aristas = len(MOCK_GRAFO.aristas)
        nodo = crear_proceso(ProcesoCreate(id="PRC-GLASEAR", nombre="Glasear", categoria="Panadería"))

        self.assertEqual((nodo.id, nodo.capa, nodo.categoria), ("PRC-GLASEAR", "proceso", "Panadería"))
        self.assertEqual(listar_procesos()[-1].id, "PRC-GLASEAR")
        self.assertTrue(all(n.capa == "proceso" for n in listar_procesos()))
        self.assertEqual(len(MOCK_GRAFO.aristas), total_aristas)

    def test_id_repetido(self):
        crear_proceso(ProcesoCreate(id="PRC-GLASEAR", nombre="Glasear"))
        for id_repetido in ["PRC-GLASEAR", "INS-HARINA"]:  # también choca con otras capas
            with self.assertRaises(HTTPException) as ctx:
                crear_proceso(ProcesoCreate(id=id_repetido, nombre="Otro"))
            self.assertEqual(ctx.exception.status_code, 409)

    def test_datos_mal_formados(self):
        with self.assertRaises(ValidationError):
            ProcesoCreate(id="PRC-X")
        with self.assertRaises(ValidationError):
            ProcesoCreate(id="", nombre="Sin id")


class TestCrearDependencia(GrafoAisladoTestCase):
    def setUp(self):
        super().setUp()
        crear_proceso(ProcesoCreate(id="PRC-PRUEBA-A", nombre="Proceso A"))
        crear_proceso(ProcesoCreate(id="PRC-PRUEBA-B", nombre="Proceso B"))

    def post(self, origen, destino):
        return crear_dependencia(DependenciaCreate(origen=origen, destino=destino))

    def assert_error(self, status, origen, destino):
        with self.assertRaises(HTTPException) as ctx:
            self.post(origen, destino)
        self.assertEqual(ctx.exception.status_code, status, f"{origen} -> {destino}")
        return ctx.exception.detail

    def test_crea_dependencias_validas_por_capa(self):
        for origen, destino in [
            ("PRD-PAN", "PRC-PRUEBA-B"),      # producto -> proceso
            ("PRC-PRUEBA-B", "PRC-PRUEBA-A"),   # proceso -> proceso
            ("PRC-PRUEBA-A", "INS-HARINA"),    # proceso -> insumo
            ("PRD-GALLETA", "INS-LEVADURA"),  # producto -> insumo
            ("INS-AZUCAR", "PRV-QUIM"),       # insumo -> proveedor
        ]:
            arista = self.post(origen, destino)
            self.assertEqual((arista.origen, arista.destino, arista.tipo), (origen, destino, "REQUIERE"))
            self.assertIn(arista, MOCK_GRAFO.aristas)

    def test_origen_inexistente(self):
        self.assertIn("origen", self.assert_error(404, "NO-EXISTE", "INS-HARINA"))

    def test_destino_inexistente(self):
        self.assertIn("destino", self.assert_error(404, "PRD-PAN", "NO-EXISTE"))

    def test_arista_repetida(self):
        total = len(MOCK_GRAFO.aristas)
        self.assert_error(409, "PRD-GALLETA", "INS-HARINA")  # ya existe en los datos (e04)
        self.assertEqual(len(MOCK_GRAFO.aristas), total)

    def test_regla_de_capas(self):
        for origen, destino in [
            ("PRV-QUIM", "INS-CONSERVANTE"),  # dirección invertida
            ("INS-HARINA", "PRD-PAN"),
            ("PRD-PAN", "PRV-QUIM"),          # se salta capas
            ("PRD-PAN", "PRD-GALLETA"),
            ("PRC-PRUEBA-A", "PRD-PAN"),
            ("INS-HARINA", "PRC-PRUEBA-A"),
        ]:
            self.assert_error(422, origen, destino)

    def test_datos_mal_formados(self):
        with self.assertRaises(ValidationError):
            DependenciaCreate(origen="PRD-PAN")
        with self.assertRaises(ValidationError):
            DependenciaCreate(origen="", destino="INS-HARINA")

    def test_no_rechaza_ciclos(self):
        # La F3 debe detectar y reportar ciclos; el catálogo no los impide.
        self.post("PRC-PRUEBA-A", "PRC-PRUEBA-B")
        self.post("PRC-PRUEBA-B", "PRC-PRUEBA-A")
        self.post("PRC-PRUEBA-A", "PRC-PRUEBA-A")
        self.assertTrue(any(a.origen == "PRC-PRUEBA-B" and a.destino == "PRC-PRUEBA-A" for a in MOCK_GRAFO.aristas))


class TestEliminarDependencia(GrafoAisladoTestCase):
    def test_quita_la_arista_y_la_devuelve(self):
        arista = crear_dependencia(DependenciaCreate(origen="PRD-GALLETA", destino="INS-LEVADURA"))

        quitada = eliminar_dependencia(arista.id)

        self.assertEqual(quitada, arista)
        self.assertNotIn(arista, MOCK_GRAFO.aristas)

    def test_dependencia_inexistente(self):
        total = len(MOCK_GRAFO.aristas)
        with self.assertRaises(HTTPException) as ctx:
            eliminar_dependencia("e999")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(len(MOCK_GRAFO.aristas), total)

    def test_los_ids_siguen_siendo_unicos_despues_de_quitar(self):
        arista = crear_dependencia(DependenciaCreate(origen="PRD-GALLETA", destino="INS-LEVADURA"))
        eliminar_dependencia(arista.id)
        nueva = crear_dependencia(DependenciaCreate(origen="PRD-GALLETA", destino="INS-LEVADURA"))

        self.assertEqual(len({a.id for a in MOCK_GRAFO.aristas}), len(MOCK_GRAFO.aristas))
        self.assertIn(nueva, MOCK_GRAFO.aristas)


if __name__ == "__main__":
    unittest.main()
