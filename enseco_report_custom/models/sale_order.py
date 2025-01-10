from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_name_sale_report(self, report_xml_id):
        self.ensure_one()
        if self.company_id.country_id.code == 'AR':
            return 'enseco_report_custom.report_saleorder_document'
        return report_xml_id
