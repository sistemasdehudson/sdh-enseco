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
                line_id = move_id.sale_line_id
                price_unit_real = line_id.price_total / (line_id.product_uom_qty if (line_id.product_uom_qty > 1) else 1)
                rec.declared_value += price_unit_real * move_id.quantity
