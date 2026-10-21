from odoo import api, fields, models

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

    def _reparto_orden_entrega_texto(self):
        """Orden de entrega con la vuelta del lote: "1RO - PRIMERA VUELTA".

        Devuelve solo "1RO" o solo "PRIMERA VUELTA" si falta el otro dato, y
        cadena vacía si no hay ninguno. Lo usan la hoja de ruta, la etiqueta
        de transferencia y las operaciones de recolección.
        """
        self.ensure_one()
        orden = ""
        if self.reparto_orden_parada:
            etiquetas = dict(self._fields["reparto_orden_parada"]._description_selection(self.env))
            orden = etiquetas.get(self.reparto_orden_parada, "")
        vuelta = self.batch_id._reparto_vuelta_texto()
        return " - ".join(texto for texto in (orden, vuelta) if texto)

    def action_reparto_abrir_remito(self):
        """Abre el formulario del remito (botón de la lista de remitos del lote)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": self.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }

    @api.model_create_multi
    def create(self, vals_list):
        remitos = super().create(vals_list)
        remitos.filtered("batch_id")._reparto_tomar_fecha_lote()
        return remitos

    def write(self, vals):
        res = super().write(vals)
        if "batch_id" in vals:
            self._reparto_tomar_fecha_lote()
        return res

    def _reparto_tomar_fecha_lote(self):
        """Un remito que entra a un lote toma la fecha de los demás remitos.

        Se usa la fecha más tardía de los otros remitos pendientes del lote,
        porque Odoo recalcula la fecha del lote como la más temprana de sus
        remitos apenas entra uno nuevo. Si no hay otros, la del lote.
        Escribe solo scheduled_date (sin batch_id), así que no vuelve a entrar.
        """
        for remito in self:
            lote = remito.batch_id
            if not lote or remito.state in ("done", "cancel"):
                continue
            otros = lote.picking_ids.filtered(
                lambda p: p.id != remito.id
                and p.state not in ("done", "cancel")
                and p.scheduled_date
            )
            fecha = max(otros.mapped("scheduled_date")) if otros else lote.scheduled_date
            if fecha and remito.scheduled_date != fecha:
                remito.write({"scheduled_date": fecha})
