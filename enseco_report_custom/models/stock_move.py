from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    quantity_detail = fields.Char(
        string="Detalle de cantidad", compute="_compute_quantity_detail", store=True
    )

    @api.depends("sale_line_id.product_uom", "quantity")
    def _compute_quantity_detail(self):
        for move in self:
            factor = getattr(move.sale_line_id.product_uom_id, 'factor', 1.0)
            if factor == 0:
                _logger.warning(f"Factor de conversión es 0 para UoM {uom.id}, usando 1.0")
                factor = 1.0
            quantity_real = move.quantity / factor
            move.quantity_detail = (
                str(quantity_real) + " U. de " + str(move.sale_line_id.product_uom_id.name)
            )
