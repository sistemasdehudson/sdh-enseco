"""
Post-migrate de enseco_report_custom 19.0.1.2.1.

Recalcula stock.move.quantity_detail con la regla nueva (la misma del Recibo ENSECO):
- se vacía si no hay línea de venta o si la UdM de venta es la misma del movimiento;
- se recalcula por ORM (formato es_AR) cuando la UdM de venta es distinta.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE stock_move m
           SET quantity_detail = NULL
          FROM stock_move m2
          LEFT JOIN sale_order_line sol ON sol.id = m2.sale_line_id
         WHERE m.id = m2.id
           AND m.quantity_detail IS NOT NULL
           AND (sol.id IS NULL OR sol.product_uom_id IS NULL OR sol.product_uom_id = m2.product_uom)
    """)
    vaciados = cr.rowcount
    cr.execute("""
        SELECT m.id
          FROM stock_move m
          JOIN sale_order_line sol ON sol.id = m.sale_line_id
         WHERE sol.product_uom_id IS NOT NULL
           AND sol.product_uom_id <> m.product_uom
    """)
    ids = [r[0] for r in cr.fetchall()]
    env = api.Environment(cr, SUPERUSER_ID, {})
    moves = env["stock.move"].browse(ids)
    moves._compute_quantity_detail()
    moves.flush_recordset(["quantity_detail"])
    _logger.info(
        "enseco_report_custom 19.0.1.2.1: quantity_detail vaciado en %s movimientos y recalculado en %s",
        vaciados, len(ids),
    )
