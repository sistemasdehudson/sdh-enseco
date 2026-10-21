import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Configuración al instalar. Idempotente: no falla si falta algo."""
    _reparto_activar_gestion_despacho(env)
    _reparto_quitar_aeroo_hoja_de_ruta(env)


def _reparto_activar_gestion_despacho(env):
    """Activa Gestión de despacho en los tipos de salida activos de todas las compañías.

    stock_fleet ya lo hace en su hook para los tipos del almacén; esto cubre
    tipos de salida que no sean out_type_id de un almacén. Sin la gestión de
    despacho, el lote oculta vehículo, capacidad y vuelta.
    """
    tipos = env["stock.picking.type"].search([
        ("code", "=", "outgoing"),
        ("dispatch_management", "=", False),
    ])
    if tipos:
        tipos.write({"dispatch_management": True})
        _logger.info(
            "enseco_hoja_ruta: gestión de despacho activada en %s tipo(s) de salida: %s",
            len(tipos), ", ".join(tipos.mapped("display_name")),
        )
    else:
        _logger.info("enseco_hoja_ruta: todos los tipos de salida ya tenían gestión de despacho")


def _reparto_quitar_aeroo_hoja_de_ruta(env):
    """Quita del menú Imprimir de los remitos el reporte Aeroo "Hoja de ruta".

    No tiene plantilla en 19.0 y da error; lo reemplaza la Hoja de ruta ENSECO
    del lote. Solo se desvincula del menú (binding_model_id), no se borra.
    """
    Report = env["ir.actions.report"]
    reportes = Report.browse()
    for xmlid in ("stock_ux.picking_waybill", "picking_waybill.picking_waybill"):
        reporte = env.ref(xmlid, raise_if_not_found=False)
        if reporte and reporte._name == "ir.actions.report":
            _logger.info("enseco_hoja_ruta: encontrado %s (id %s)", xmlid, reporte.id)
            reportes |= reporte
    # Por si el registro quedó sin xmlid (huérfano de versiones anteriores)
    reportes |= Report.search([
        ("model", "=", "stock.picking"),
        ("report_name", "=", "picking_waybill"),
    ]).filtered(lambda r: r.report_type == "aeroo")
    vinculados = reportes.filtered("binding_model_id")
    if vinculados:
        vinculados.unlink_action()
        _logger.info(
            "enseco_hoja_ruta: quitado del menú Imprimir: %s",
            ", ".join("%s (id %s)" % (r.name, r.id) for r in vinculados),
        )
    elif reportes:
        _logger.info("enseco_hoja_ruta: el reporte Aeroo Hoja de ruta ya estaba fuera del menú")
    else:
        _logger.info("enseco_hoja_ruta: no se encontró el reporte Aeroo Hoja de ruta")
