import unittest

from data import MOCK_GRAFO
from impacto import consultar_impacto
from recorrido import bfs, construir_adyacencia_impacto, reconstruir_camino


class TestBFS(unittest.TestCase):
    def test_ejemplo_del_enunciado(self):
        adyacencia = {1: [2, 6, 5, 4], 2: [3]}

        visitados, padres = bfs(adyacencia, 1)

        self.assertEqual(visitados, [1, 2, 6, 5, 4, 3])
        self.assertEqual(padres, {1: None, 2: 1, 6: 1, 5: 1, 4: 1, 3: 2})

    def test_grafo_con_ciclo_no_entra_en_bucle_infinito(self):
        adyacencia = {1: [2], 2: [3], 3: [1, 4], 4: [2]}

        visitados, padres = bfs(adyacencia, 1)

        self.assertEqual(visitados, [1, 2, 3, 4])
        self.assertEqual(padres, {1: None, 2: 1, 3: 2, 4: 3})

    def test_reconstruir_camino(self):
        padres = {1: None, 2: 1, 6: 1, 5: 1, 4: 1, 3: 2}

        self.assertEqual(reconstruir_camino(padres, 3), [1, 2, 3])
        self.assertEqual(reconstruir_camino(padres, 1), [1])


class TestAdyacenciaImpacto(unittest.TestCase):
    def test_va_de_causa_a_consecuencia(self):
        adyacencia = construir_adyacencia_impacto(MOCK_GRAFO)

        # Si falla la distribuidora de químicos, se afecta el conservante...
        self.assertEqual(adyacencia["PRV-QUIM"], ["INS-CONSERVANTE"])
        # ...y sin conservante se afectan el ponqué y las tostadas.
        self.assertEqual(adyacencia["INS-CONSERVANTE"], ["PRD-PONQUE", "PRD-TOSTADAS"])
        # Nadie depende de un producto terminado.
        self.assertEqual(adyacencia["PRD-PAN"], [])


class TestConsultarImpacto(unittest.TestCase):
    def test_elemento_inexistente(self):
        resultado = consultar_impacto(MOCK_GRAFO, "PRV-NO-EXISTE")

        self.assertEqual(resultado.caso, "inexistente")
        self.assertIsNone(resultado.origen)
        self.assertEqual(resultado.afectados, [])

    def test_elemento_sin_dependencias(self):
        resultado = consultar_impacto(MOCK_GRAFO, "PRD-PAN")

        self.assertEqual(resultado.caso, "sin_dependencias")
        self.assertEqual(resultado.origen.id, "PRD-PAN")
        self.assertEqual(resultado.visitados, ["PRD-PAN"])
        self.assertEqual(resultado.afectados, [])

    def test_cadena_de_varios_niveles(self):
        resultado = consultar_impacto(MOCK_GRAFO, "PRV-QUIM")

        self.assertEqual(resultado.caso, "afecta_cadena")
        self.assertEqual(resultado.origen.id, "PRV-QUIM")
        self.assertEqual(resultado.visitados, ["PRV-QUIM", "INS-CONSERVANTE", "PRD-PONQUE", "PRD-TOSTADAS"])
        self.assertEqual(
            [n.id for n in resultado.afectados],
            ["INS-CONSERVANTE", "PRD-PONQUE", "PRD-TOSTADAS"],  # el origen no es un afectado
        )

        afectados = {n.id: n for n in resultado.afectados}
        self.assertEqual(afectados["INS-CONSERVANTE"].nivel, 1)
        self.assertEqual(afectados["PRD-TOSTADAS"].nivel, 2)
        self.assertEqual(afectados["PRD-TOSTADAS"].camino, ["PRV-QUIM", "INS-CONSERVANTE", "PRD-TOSTADAS"])

    def test_proveedor_compartido_afecta_por_niveles(self):
        resultado = consultar_impacto(MOCK_GRAFO, "PRV-MATERIAPRIMA")

        niveles = [(n.id, n.nivel) for n in resultado.afectados]
        self.assertEqual(niveles, [
            ("INS-HARINA", 1), ("INS-AZUCAR", 1), ("INS-LEVADURA", 1),
            ("PRD-PAN", 2), ("PRD-GALLETA", 2), ("PRD-PONQUE", 2), ("PRD-TOSTADAS", 2),
        ])


if __name__ == "__main__":
    unittest.main()
