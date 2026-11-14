from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class SaleOrderVatWizard(models.TransientModel):
    _name = "sale.order.vat.wizard"
    _description = "Cambiar IVA de todas las líneas del presupuesto"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="order_id.company_id")
    tax_id = fields.Many2one(
        "account.tax",
        string="IVA",
        required=True,
        domain="[('type_tax_use', '=', 'sale'), ('tax_group_id.l10n_ar_vat_afip_code', '!=', False),"
        " ('company_id', 'parent_of', company_id)]",
    )

    def action_apply(self):
        self.ensure_one()
        order = self.order_id
        if order.state not in ("draft", "sent"):
            raise UserError(self.env._("Solo se puede cambiar el IVA en presupuestos (borrador o enviados)."))
        lines = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
        for line in lines:
            # Se reemplaza solo el IVA; percepciones u otros impuestos de la línea se mantienen.
            other_taxes = line.tax_ids.filtered(lambda t: not t.tax_group_id.l10n_ar_vat_afip_code)
            line.tax_ids = [Command.set((other_taxes | self.tax_id).ids)]
        order.message_post(
            body=self.env._(
                "IVA de todas las líneas cambiado a %(tax)s (%(count)s líneas).",
                tax=self.tax_id.display_name,
                count=len(lines),
            )
        )
        return {"type": "ir.actions.act_window_close"}
