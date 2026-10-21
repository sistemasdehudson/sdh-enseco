from odoo import fields, models

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
