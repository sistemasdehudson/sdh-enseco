from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends_context("enseco_vat_discriminated")
    def _compute_vat_discriminated(self):
        # Reporte "Cotización con IVA discriminado": con este contexto el IVA se
        # discrimina para cualquier cliente (l10n_ar_sale solo lo hace para RI).
        # Sin el contexto, el resto de los reportes se comporta como siempre.
        super()._compute_vat_discriminated()
        if self.env.context.get("enseco_vat_discriminated"):
            for rec in self.filtered("company_id.l10n_ar_company_requires_vat"):
                rec.vat_discriminated = True

    @api.depends_context("enseco_vat_discriminated")
    def _compute_tax_totals(self):
        return super()._compute_tax_totals()

    def action_open_vat_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cambiar IVA de todas las líneas"),
            "res_model": "sale.order.vat.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }

    def _get_name_sale_report(self, report_xml_id):
        self.ensure_one()
        if self.company_id.country_id.code == 'AR':
            return 'enseco_report_custom.report_saleorder_document'
        return report_xml_id


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Los precios del reporte dependen de vat_discriminated: se recalculan según el contexto.
    @api.depends_context("enseco_vat_discriminated")
    def _compute_report_price_reduce(self):
        return super()._compute_report_price_reduce()

    @api.depends_context("enseco_vat_discriminated")
    def _compute_report_prices_and_taxes(self):
        return super()._compute_report_prices_and_taxes()
