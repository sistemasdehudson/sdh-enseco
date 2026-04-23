from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends(
        'automatic_declare_value',
        'move_ids.state',
        'move_ids.quantity',
    )
    
    def _compute_declared_value(self):
        super()._compute_declared_value()
        for rec in self:
            rec.declared_value = 0
            for move_id in rec.move_ids:
                factor = move_id.sale_line_id.product_uom_id.factor if move_id.sale_line_id.product_uom_id.factor else 1
                quantity_real = move_id.quantity / factor
                price_unit_real = move_id.sale_line_id.price_subtotal / (move_id.sale_line_id.product_uom_qty if (move_id.sale_line_id.product_uom_qty > 1) else 1)
                quantity_detail = str(quantity_real) + ' U. de ' + str(move_id.sale_line_id.product_uom_id.name)
                move_id.quantity_detail = quantity_detail
                rec.declared_value += price_unit_real * quantity_real
