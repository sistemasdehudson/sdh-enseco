import re

from odoo.tests import TransactionCase, tagged

from odoo.addons.enseco_hoja_ruta.hooks import _reparto_precision_peso


@tagged("post_install", "-at_install", "enseco_hoja_ruta")
class TestRepartoPeso(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.precision = cls.env.ref("product.decimal_stock_weight")
        cls.partner = cls.env["res.partner"].create({"name": "Obra Prueba Peso"})
        tipo = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.env.company.id)], limit=1)
        cls.remito = cls.env["stock.picking"].create({
            "partner_id": cls.partner.id,
            "picking_type_id": tipo.id,
            "location_id": tipo.default_location_src_id.id,
            "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
        })

    def test_precision_sube_a_4(self):
        self.precision.digits = 2
        _reparto_precision_peso(self.env)
        self.assertEqual(self.precision.digits, 4)

    def test_precision_no_baja(self):
        self.precision.digits = 5
        _reparto_precision_peso(self.env)
        self.assertEqual(self.precision.digits, 5)

    def _texto_reporte(self, xmlid):
        html = self.env["ir.actions.report"]._render_qweb_html(xmlid, self.remito.ids)[0].decode()
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))

    def test_peso_con_2_decimales(self):
        self.precision.digits = 4
        self.remito.shipping_weight = 413.55
        for xmlid in (
            "enseco_report_custom.action_report_delivery_enseco",
            "stock.action_report_picking",
            "stock.action_report_delivery",
        ):
            texto = self._texto_reporte(xmlid)
            self.assertRegex(texto, r"413[.,]55 kg", xmlid)
            self.assertNotRegex(texto, r"413[.,]5500", xmlid)
