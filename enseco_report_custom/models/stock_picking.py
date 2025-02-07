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
        for rec in self.filtered(lambda p: p.sale_id and p.state not in ['done', 'cancel']):
            rec.declared_value = 0
            for move_id in rec.move_ids_without_package:
                factor_inv = move_id.sale_line_id.product_uom.factor_inv if move_id.sale_line_id.product_uom.factor_inv else 1
                quantity_real = move_id.quantity / factor_inv
                price_unit_real = move_id.sale_line_id.price_subtotal / (move_id.sale_line_id.product_uom_qty if (move_id.sale_line_id.product_uom_qty > 1) else 1)
                quantity_detail = str(quantity_real) + ' U. de ' + str(move_id.sale_line_id.product_uom.name)
                move_id.quantity_detail = quantity_detail
                rec.declared_value += price_unit_real * quantity_real
