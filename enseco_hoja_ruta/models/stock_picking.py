from odoo import fields, models

REPARTO_ORDEN_PARADA = [
    ("01", "1RO"),
    ("02", "2DO"),
    ("03", "3RO"),
    ("04", "4TO"),
    ("05", "5TO"),
    ("06", "6TO"),
    ("07", "7MO"),
    ("08", "8VO"),
    ("09", "9NO"),
    ("10", "10MO"),
    ("11", "11VO"),
    ("12", "12VO"),
]

REPARTO_ZONA = [
    ("oeste", "Zona Oeste"),
    ("caba", "Zona CABA"),
    ("norte", "Zona Norte"),
    ("sur", "Zona Sur"),
]

REPARTO_LADO_DESCARGA = [
    ("conductor", "Conductor"),
    ("acompanante", "Acompañante"),
    ("indistinto", "Indistinto"),
]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Datos del pedido: se guardan en el pedido de venta; editar en el remito
    # escribe en el pedido y todos sus remitos comparten el dato.
    reparto_telefono_obra = fields.Char(
        related="sale_id.reparto_telefono_obra",
        readonly=False,
    )
    reparto_direccion_entrega = fields.Text(
        related="sale_id.reparto_direccion_entrega",
        readonly=False,
    )
    reparto_obs_logistica = fields.Text(
        related="sale_id.reparto_obs_logistica",
        readonly=False,
    )
    reparto_recibe_lluvia = fields.Selection(
        related="sale_id.reparto_recibe_lluvia",
        readonly=False,
    )
    reparto_confirmacion = fields.Selection(
        related="sale_id.reparto_confirmacion",
        readonly=False,
    )

    # Datos de logística, propios del remito.
    reparto_orden_parada = fields.Selection(
        selection=REPARTO_ORDEN_PARADA,
        string="Orden de entrega",
    )
    reparto_zona = fields.Selection(
        selection=REPARTO_ZONA,
        string="Zona de reparto",
    )
    reparto_lado_descarga = fields.Selection(
        selection=REPARTO_LADO_DESCARGA,
        string="Lado de descarga",
    )
