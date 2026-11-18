from odoo import fields, models

from .stock_picking import (
    REPARTO_CAMPOS_LOGISTICA,
    REPARTO_LADO_DESCARGA,
    REPARTO_ORDEN_PARADA,
    REPARTO_ZONA,
)

REPARTO_RECIBE_LLUVIA = [
    ("si", "Sí"),
    ("no", "No"),
    ("consultar", "Consultar"),
]

REPARTO_CONFIRMACION = [
    ("confirmado", "Confirmado"),
    ("sin_confirmar", "Sin confirmar"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    reparto_telefono_obra = fields.Char(
        string="Teléfono de contacto en obra",
    )
    reparto_direccion_entrega = fields.Text(
        string="Dirección de entrega",
    )
    reparto_obs_logistica = fields.Text(
        string="Observaciones para logística",
    )
    reparto_recibe_lluvia = fields.Selection(
        selection=REPARTO_RECIBE_LLUVIA,
        string="¿Recibe con lluvia?",
    )
    reparto_confirmacion = fields.Selection(
        selection=REPARTO_CONFIRMACION,
        string="Confirmación de reparto",
    )

    # De logística: también en el remito (bajan a los remitos abiertos)
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

    def write(self, vals):
        res = super().write(vals)
        logistica = {campo: vals[campo] for campo in REPARTO_CAMPOS_LOGISTICA if campo in vals}
        if logistica:
            # Lo que cambia el comercial baja a los remitos abiertos del pedido
            self.picking_ids.filtered(lambda p: p.state not in ("done", "cancel")).write(logistica)
        return res
