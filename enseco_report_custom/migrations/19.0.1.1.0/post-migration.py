"""
Post-migrate de enseco_report_custom 19.0.1.1.0.

Reactiva las vistas del módulo desactivadas por el upgrade oficial 17→19.
Reemplaza al script manual scripts/reactivar_vistas_post_upgrade.py.

Validado en builds 31400715 (post-fix manual) y 31401666 (sin fix manual).
Las 2 vistas afectadas en build limpio:
  - enseco_report_custom.report_delivery_document
  - enseco_report_custom.view_picking_form_inherit
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "enseco_report_custom post-migrate 19.0.1.1.0: "
        "reactivación de vistas desactivadas por el upgrade oficial"
    )

    cr.execute("""
        SELECT v.id, imd.name AS xml_name
        FROM ir_ui_view v
        JOIN ir_model_data imd
            ON imd.res_id = v.id
            AND imd.model = 'ir.ui.view'
            AND imd.module = 'enseco_report_custom'
        WHERE v.active = FALSE
        ORDER BY imd.name
    """)
    rows = cr.fetchall()

    if not rows:
        _logger.info("  ✓ No hay vistas desactivadas. Nada que hacer.")
        return

    _logger.info("  Detectadas %d vistas desactivadas para reactivar:", len(rows))
    for view_id, xml_name in rows:
        _logger.info("    - enseco_report_custom.%s (id=%d)", xml_name, view_id)

    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    reactivadas = 0
    fallidas = []

    for view_id, xml_name in rows:
        xmlid = "enseco_report_custom.%s" % xml_name
        view = env['ir.ui.view'].browse(view_id)

        if not view.exists():
            _logger.warning("    ⚠ %s: no existe en DB, skip", xmlid)
            continue

        try:
            view.write({'active': True})
            try:
                view._get_combined_arch()
            except Exception as e:
                view.write({'active': False})
                error_msg = str(e).split('\n')[0][:200]
                fallidas.append((xmlid, view_id, error_msg))
                _logger.warning(
                    "    ⚠ %s (id=%d): validación falló, queda desactivada. Error: %s",
                    xmlid, view_id, error_msg
                )
                continue

            reactivadas += 1
            _logger.info("    ✓ %s (id=%d): reactivada", xmlid, view_id)

        except Exception as e:
            error_msg = str(e).split('\n')[0][:200]
            fallidas.append((xmlid, view_id, "Error en write: %s" % error_msg))
            _logger.error(
                "    ✗ %s (id=%d): error en activación: %s",
                xmlid, view_id, error_msg
            )
            try:
                cr.execute(
                    "UPDATE ir_ui_view SET active = FALSE WHERE id = %s",
                    (view_id,)
                )
            except Exception:
                pass

    _logger.info("")
    _logger.info("  Resumen:")
    _logger.info("    ✓ Reactivadas: %d", reactivadas)
    _logger.info("    ✗ Fallidas (deuda técnica): %d", len(fallidas))

    if fallidas:
        _logger.warning(
            "  Las siguientes vistas no pudieron reactivarse "
            "y requieren atención manual:"
        )
        for xmlid, view_id, error_msg in fallidas:
            _logger.warning("    - %s (id=%d): %s", xmlid, view_id, error_msg)
