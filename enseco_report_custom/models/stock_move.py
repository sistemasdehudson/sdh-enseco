from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    quantity_detail = fields.Char(
        string="Detalle de cantidad", compute="_compute_quantity_detail", store=True
    )

    @api.depends("sale_line_id.product_uom", "quantity")
    def _compute_quantity_detail(self):
        for move in self:
            factor_inv = (
                move.sale_line_id.product_uom.factor_inv
                if move.sale_line_id.product_uom.factor_inv
                else 1
            )
            quantity_real = move.quantity / factor_inv
            move.quantity_detail = (
                str(quantity_real) + " U. de " + str(move.sale_line_id.product_uom.name)
            )
