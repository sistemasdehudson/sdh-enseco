from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    quantity_detail = fields.Char(
        string="Detalle de cantidad", compute="_compute_quantity_detail", store=True
    )

    @api.depends("sale_line_id.product_uom_id", "product_uom", "quantity")
    def _compute_quantity_detail(self):
        # Misma regla que el Recibo de entrega (ENSECO), plantilla quantity_detail_enseco:
        # solo si la UdM de venta difiere de la del movimiento, con formato es_AR
        # ("10 U. de 6,00 MTS"). Es un campo almacenado, así que el formato es fijo en es_AR.
        lang = self.env["res.lang"]._lang_get("es_AR") or self.env["res.lang"]._lang_get(self.env.lang)
        for move in self:
            sale_uom = move.sale_line_id.product_uom_id.with_context(lang=lang.code)
            if not sale_uom or sale_uom == move.product_uom:
                move.quantity_detail = False
                continue
            qty = move.quantity / (sale_uom.factor or 1)
            qty_txt = lang.format("%.4f", qty, grouping=True).rstrip("0").rstrip(lang.decimal_point)
            move.quantity_detail = "%s U. de %s" % (qty_txt, sale_uom.name)
