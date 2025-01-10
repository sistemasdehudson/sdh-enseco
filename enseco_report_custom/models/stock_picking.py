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
            rec.declared_value = rec.sale_id.amount_total
