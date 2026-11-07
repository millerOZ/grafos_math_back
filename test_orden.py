import unittest

from data import MOCK_GRAFO
from main import crear_dependencia, obtener_orden_produccion
from models import DependenciaCreate, Grafo
from orden import consultar_orden_produccion
from test_dependencias import GrafoAisladoTestCase
from topologico import buscar_ciclos, ordenar_por_etapas


def nodo(id, capa):
    return {"id": id, "nombre": id, "capa": capa}


def req(origen, destino):
    return {"id": f"{origen}>{destino}", "origen": origen, "destino": destino, "tipo": "REQUIERE"}


def panaderia(nodos_extra=(), aristas_extra=()):
    """Pan: Empacar -> Tajar -> Hornear -> Fermentar -> Amasar -> Harina (igual que ciclos.test.ts)."""
    return Grafo(
        nodos=[
            nodo("PAN", "producto"), nodo("GALLETA", "producto"),
            nodo("AMASAR", "proceso"), nodo("FERMENTAR", "proceso"), nodo("HORNEAR", "proceso"),
            nodo("TAJAR", "proceso"), nodo("EMPACAR", "proceso"),
            nodo("HARINA", "insumo"),
            *nodos_extra,
        ],
        aristas=[
            req("PAN", "EMPACAR"), req("EMPACAR", "TAJAR"), req("TAJAR", "HORNEAR"),
            req("HORNEAR", "FERMENTAR"), req("FERMENTAR", "AMASAR"), req("AMASAR", "HARINA"),
            req("GALLETA", "HARINA"),
            *aristas_extra,
        ],
    )


class TestAlgoritmos(unittest.TestCase):
    def test_kahn_por_etapas(self):
        requisitos = {1: [], 2: [1], 3: [1], 4: [2, 3]}

        self.assertEqual(ordenar_por_etapas([1, 2, 3, 4], requisitos), [[1], [2, 3], [4]])

    def test_tarjan_sin_ciclos(self):
        self.assertEqual(buscar_ciclos([1, 2, 3], {1: [2], 2: [3], 3: []}), [])

    def test_tarjan_reporta_el_ciclo_mas_corto(self):
        # 1 -> 2 -> 3 -> 1 y además 1 -> 3: el ciclo más corto por 1 es 1 -> 3 -> 1.
        requisitos = {1: [2, 3], 2: [3], 3: [1]}

        self.assertEqual(buscar_ciclos([1, 2, 3], requisitos), [[1, 3]])


class TestOrdenProduccion(unittest.TestCase):
    def test_caso_aciclico_da_orden_valido(self):
        r = consultar_orden_produccion(panaderia())

        self.assertEqual(r.caso, "orden_valido")
        self.assertEqual(r.ciclos, [])
        self.assertEqual(r.etapas, [["AMASAR"], ["FERMENTAR"], ["HORNEAR"], ["TAJAR"], ["EMPACAR"]])
        self.assertEqual(len(r.planes), 1)
        self.assertEqual(r.planes[0].producto.id, "PAN")
        self.assertEqual(
            [id for etapa in r.planes[0].etapas for id in etapa],
            ["AMASAR", "FERMENTAR", "HORNEAR", "TAJAR", "EMPACAR"],
        )
        self.assertEqual([p.id for p in r.sin_procesos], ["GALLETA"])

    def test_procesos_independientes_quedan_en_la_misma_etapa(self):
        g = panaderia([nodo("ETIQUETAR", "proceso")], [req("EMPACAR", "ETIQUETAR")])

        self.assertEqual(consultar_orden_produccion(g).etapas[0], ["AMASAR", "ETIQUETAR"])

    def test_el_orden_respeta_cada_dependencia(self):
        r = consultar_orden_produccion(MOCK_GRAFO)
        posicion = {id: i for i, etapa in enumerate(r.etapas) for id in etapa}

        for a in MOCK_GRAFO.aristas:
            if a.origen in posicion and a.destino in posicion:
                self.assertLess(posicion[a.destino], posicion[a.origen], f"{a.origen} requiere {a.destino}")

    def test_caso_ciclico_reporta_el_ciclo_y_no_presenta_orden_falso(self):
        g = panaderia(aristas_extra=[req("AMASAR", "HORNEAR")])  # Hornear -> Fermentar -> Amasar -> Hornear

        r = consultar_orden_produccion(g)

        self.assertEqual(r.caso, "ciclo")
        self.assertEqual([c.ids for c in r.ciclos], [["AMASAR", "HORNEAR", "FERMENTAR"]])
        self.assertEqual(
            r.ciclos[0].descripcion,
            "AMASAR necesita HORNEAR, HORNEAR necesita FERMENTAR, FERMENTAR necesita AMASAR: "
            "ninguno puede empezar primero.",
        )
        self.assertEqual(r.en_ciclo, ["AMASAR", "FERMENTAR", "HORNEAR"])
        self.assertIsNone(r.etapas)
        self.assertIsNone(r.planes[0].etapas)
        self.assertEqual(r.planes[0].bloqueado_por, [0])
        self.assertIn("PAN", r.mensaje)

    def test_un_proceso_que_se_requiere_a_si_mismo_es_un_ciclo(self):
        r = consultar_orden_produccion(panaderia(aristas_extra=[req("TAJAR", "TAJAR")]))

        self.assertEqual([c.ids for c in r.ciclos], [["TAJAR"]])
        self.assertIn("a sí mismo", r.ciclos[0].descripcion)

    def test_un_ciclo_solo_bloquea_a_los_productos_que_lo_usan(self):
        g = panaderia(
            [nodo("PONQUE", "producto"), nodo("GLASEAR", "proceso"), nodo("DECORAR", "proceso")],
            [req("PONQUE", "GLASEAR"), req("GLASEAR", "DECORAR"), req("DECORAR", "GLASEAR")],
        )

        r = consultar_orden_produccion(g)
        plan = {p.producto.id: p for p in r.planes}

        self.assertEqual(len(r.ciclos), 1)
        self.assertIsNone(plan["PONQUE"].etapas)
        self.assertEqual(
            [id for etapa in plan["PAN"].etapas for id in etapa],
            ["AMASAR", "FERMENTAR", "HORNEAR", "TAJAR", "EMPACAR"],
        )

    def test_sin_procesos(self):
        g = Grafo(nodos=[nodo("PAN", "producto"), nodo("HARINA", "insumo")], aristas=[req("PAN", "HARINA")])

        r = consultar_orden_produccion(g)

        self.assertEqual(r.caso, "sin_procesos")
        self.assertEqual(r.etapas, [])
        self.assertEqual([p.id for p in r.sin_procesos], ["PAN"])


class TestAceptacionEndpoint(GrafoAisladoTestCase):
    """Aceptación F3 sobre los datos de la demo: orden válido y, tras cargar una dependencia, ciclo."""

    def test_datos_de_la_demo_tienen_orden_valido(self):
        r = obtener_orden_produccion()

        self.assertEqual(r.caso, "orden_valido")
        self.assertEqual(r.etapas, [["PRC-AMASAR"], ["PRC-FERMENTAR"], ["PRC-HORNEAR"], ["PRC-TAJAR"], ["PRC-EMPACAR"]])

    def test_cargar_una_dependencia_contradictoria_genera_alerta(self):
        # "Para amasar necesito hornear" contradice "hornear requiere fermentar, fermentar requiere amasar".
        crear_dependencia(DependenciaCreate(origen="PRC-AMASAR", destino="PRC-HORNEAR"))

        r = obtener_orden_produccion()

        self.assertEqual(r.caso, "ciclo")
        self.assertEqual([c.ids for c in r.ciclos], [["PRC-AMASAR", "PRC-HORNEAR", "PRC-FERMENTAR"]])
        self.assertIsNone(r.etapas)
        pan = next(p for p in r.planes if p.producto.id == "PRD-PAN")
        self.assertIsNone(pan.etapas)


if __name__ == "__main__":
    unittest.main()
