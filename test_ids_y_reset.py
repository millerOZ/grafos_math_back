import os
import unittest
from unittest import mock

from fastapi import HTTPException
from pydantic import ValidationError

from data import MOCK_GRAFO
from impacto import consultar_impacto
from main import (
    crear_insumo,
    crear_producto,
    crear_proveedor,
    obtener_impacto,
    reiniciar_demo,
)
from models import InsumoCreate, ProcesoCreate, ProductoCreate, ProveedorCreate
from test_dependencias import GrafoAisladoTestCase


IDS_MALOS = ["", "   ", "PRV NUEVO", " PRV-NUEVO", "prv-nuevo", "PRV-x", "PRV-", "PRVNUEVO", "PRV-NUEVO!"]

# Los cuatro modelos de creación, con un id válido para cada uno y el resto de campos.
MODELOS = [
    (ProveedorCreate, "PRV-NUEVO", {}),
    (ProcesoCreate, "PRC-NUEVO", {}),
    (InsumoCreate, "INS-NUEVO", {"proveedor_id": "PRV-QUIM"}),
    (ProductoCreate, "PRD-NUEVO", {"insumo_ids": ["INS-HARINA"]}),
]


class TestIdAlCrear(GrafoAisladoTestCase):
    def assert_invalido(self, modelo, **datos):
        with self.assertRaises(ValidationError) as ctx:
            modelo(**datos)
        return ctx.exception.errors()[0]["msg"]

    def test_mismo_criterio_en_los_cuatro_modelos(self):
        # Antes ProveedorCreate, InsumoCreate y ProductoCreate aceptaban "" y "PRV-x".
        for modelo, _, extra in MODELOS:
            for id_malo in IDS_MALOS:
                with self.subTest(modelo=modelo.__name__, id=id_malo):
                    self.assert_invalido(modelo, id=id_malo, nombre="X", **extra)

    def test_mismo_motivo_que_impacto(self):
        for id_malo in IDS_MALOS:
            with self.subTest(id=id_malo):
                msg = self.assert_invalido(ProveedorCreate, id=id_malo, nombre="X")
                self.assertEqual(msg, consultar_impacto(MOCK_GRAFO, id_malo).mensaje)

    def test_prefijo_debe_coincidir_con_la_capa(self):
        self.assertIn("PRV-", self.assert_invalido(ProveedorCreate, id="INS-NUEVO", nombre="X"))
        self.assert_invalido(ProcesoCreate, id="PRV-NUEVO", nombre="X")
        self.assert_invalido(InsumoCreate, id="PRD-NUEVO", nombre="X", proveedor_id="PRV-QUIM")
        self.assert_invalido(ProductoCreate, id="PRC-NUEVO", nombre="X", insumo_ids=["INS-HARINA"])

    def test_nombre_obligatorio_en_los_cuatro_modelos(self):
        for modelo, id_ok, extra in MODELOS:
            for nombre in ["", "   "]:
                with self.subTest(modelo=modelo.__name__, nombre=nombre):
                    self.assert_invalido(modelo, id=id_ok, nombre=nombre, **extra)

    def test_ids_de_referencia_tambien_se_validan(self):
        self.assert_invalido(InsumoCreate, id="INS-NUEVO", nombre="X", proveedor_id="prv-quim")
        self.assert_invalido(InsumoCreate, id="INS-NUEVO", nombre="X", proveedor_id="")
        self.assert_invalido(ProductoCreate, id="PRD-NUEVO", nombre="X", insumo_ids=["INS-HARINA", "INS HARINA"])

    def test_ids_validos_se_aceptan(self):
        for modelo, id_ok, extra in MODELOS:
            with self.subTest(modelo=modelo.__name__):
                self.assertEqual(modelo(id=id_ok, nombre="X", **extra).id, id_ok)

    def test_todo_lo_creado_se_puede_consultar_en_impacto(self):
        crear_proveedor(ProveedorCreate(id="PRV-MOLINO", nombre="Molino"))
        crear_insumo(InsumoCreate(id="INS-AVENA", nombre="Avena", proveedor_id="PRV-MOLINO"))
        crear_producto(ProductoCreate(id="PRD-GALLETA-AVENA", nombre="Galleta de avena", insumo_ids=["INS-AVENA"]))
        self.assertEqual(obtener_impacto("PRV-MOLINO").caso, "afecta_cadena")


class TestDemoReset(GrafoAisladoTestCase):
    def assert_403(self, token):
        with self.assertRaises(HTTPException) as ctx:
            reiniciar_demo(x_demo_token=token)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_deshabilitado_si_no_hay_clave_configurada(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assert_403("cualquiera")
            self.assert_403(None)

    def test_rechaza_clave_ausente_o_incorrecta(self):
        with mock.patch.dict(os.environ, {"DEMO_RESET_TOKEN": "secreta"}):
            self.assert_403(None)
            self.assert_403("")
            self.assert_403("otra")
            self.assert_403("contraseña")  # texto no ASCII: no debe romper la comparación

    def test_con_clave_correcta_reinicia(self):
        inicial = MOCK_GRAFO.model_dump()
        crear_proveedor(ProveedorCreate(id="PRV-MOLINO", nombre="Molino"))
        with mock.patch.dict(os.environ, {"DEMO_RESET_TOKEN": "secreta"}):
            grafo = reiniciar_demo(x_demo_token="secreta")
        self.assertEqual(grafo.model_dump(), inicial)

    def test_clave_incorrecta_no_toca_el_grafo(self):
        crear_proveedor(ProveedorCreate(id="PRV-MOLINO", nombre="Molino"))
        antes = MOCK_GRAFO.model_dump()
        with mock.patch.dict(os.environ, {"DEMO_RESET_TOKEN": "secreta"}):
            self.assert_403("otra")
        self.assertEqual(MOCK_GRAFO.model_dump(), antes)


if __name__ == "__main__":
    unittest.main()
