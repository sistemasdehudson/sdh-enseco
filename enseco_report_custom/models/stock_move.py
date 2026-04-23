from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = "stock.move"

    quantity_detail = fields.Char(
        string="Detalle de cantidad", compute="_compute_quantity_detail", store=True
    )

    @api.depends("sale_line_id.product_uom_id", "quantity")
    def _compute_quantity_detail(self):
        for move in self:
            factor = (
                move.sale_line_id.product_uom_id.factor
                if move.sale_line_id.product_uom_id.factor
                else 1
            )
            if factor == 0:
                _logger.warning(
                    "El factor de la unidad de medida es cero para el producto %s. Se asignará un factor de 1 para evitar errores de división.",
                    move.sale_line_id.product_id.name,
                )
                factor = 1  
            quantity_real = move.quantity / factor
            move.quantity_detail = (
                str(quantity_real) + " U. de " + str(move.sale_line_id.product_uom_id.name)
            )
