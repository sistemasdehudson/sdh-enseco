import babel.dates
import pytz

from odoo import api, fields, models
from odoo.tools.misc import babel_locale_parse

REPARTO_TZ_DEFAULT = "America/Argentina/Buenos_Aires"

REPARTO_VUELTA = [
    ("1", "Primera vuelta"),
    ("2", "Segunda vuelta"),
    ("3", "Tercera vuelta"),
]


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    reparto_vuelta = fields.Selection(
        selection=REPARTO_VUELTA,
        string="Vuelta",
    )
    reparto_km_salida = fields.Integer(
        string="KM de salida",
    )
    reparto_km_regreso = fields.Integer(
        string="KM de regreso",
    )
    reparto_hora_salida = fields.Datetime(
        string="Hora de salida",
    )
    reparto_hora_regreso = fields.Datetime(
        string="Hora de regreso",
    )
    reparto_km_recorridos = fields.Integer(
        string="KM recorridos",
        compute="_compute_reparto_km_recorridos",
        store=True,
    )
    reparto_horas_viaje = fields.Float(
        string="Duración del viaje",
        compute="_compute_reparto_horas_viaje",
        store=True,
    )

    @api.depends("reparto_km_salida", "reparto_km_regreso")
    def _compute_reparto_km_recorridos(self):
        for lote in self:
            if lote.reparto_km_salida and lote.reparto_km_regreso:
                lote.reparto_km_recorridos = lote.reparto_km_regreso - lote.reparto_km_salida
            else:
                lote.reparto_km_recorridos = 0

    @api.depends("reparto_hora_salida", "reparto_hora_regreso")
    def _compute_reparto_horas_viaje(self):
        for lote in self:
            if lote.reparto_hora_salida and lote.reparto_hora_regreso:
                duracion = lote.reparto_hora_regreso - lote.reparto_hora_salida
                lote.reparto_horas_viaje = duracion.total_seconds() / 3600.0
            else:
                lote.reparto_horas_viaje = 0.0

    def write(self, vals):
        """Al cambiar la fecha programada del lote, sus remitos pendientes la toman.

        Escribe scheduled_date en los remitos sin batch_id, así que no dispara
        la lógica del remito que entra al lote.
        """
        res = super().write(vals)
        if "scheduled_date" in vals:
            for lote in self.filtered("scheduled_date"):
                remitos = lote.picking_ids.filtered(
                    lambda p: p.state not in ("done", "cancel")
                    and p.scheduled_date != lote.scheduled_date
                )
                if remitos:
                    remitos.write({"scheduled_date": lote.scheduled_date})
        return res

    # Helpers de texto, fecha y hora para los reportes

    def _reparto_vuelta_texto(self):
        """Vuelta en mayúsculas ("PRIMERA VUELTA"); vacío si no hay lote o vuelta."""
        if len(self) != 1 or not self.reparto_vuelta:
            return ""
        etiquetas = dict(self._fields["reparto_vuelta"]._description_selection(self.env))
        return etiquetas.get(self.reparto_vuelta, "").upper()

    def _reparto_tz(self):
        """Zona horaria del usuario o, si no tiene, la de Buenos Aires."""
        try:
            return pytz.timezone(self.env.user.tz or REPARTO_TZ_DEFAULT)
        except pytz.UnknownTimeZoneError:
            return pytz.timezone(REPARTO_TZ_DEFAULT)

    def _reparto_fecha_local(self, valor):
        """Convierte un datetime UTC de la base a la zona horaria del usuario."""
        return pytz.utc.localize(valor).astimezone(self._reparto_tz())

    def _reparto_titulo_fecha(self):
        """Fecha programada para el título de la hoja de ruta: "MARTES 15/09/2026"."""
        self.ensure_one()
        if not self.scheduled_date:
            return ""
        fecha = self._reparto_fecha_local(self.scheduled_date).date()
        locale = babel_locale_parse(self.env.lang or self.env.user.lang or "es_AR")
        return babel.dates.format_date(fecha, "EEEE dd/MM/yyyy", locale=locale).upper()

    def _reparto_hora(self, campo):
        """Hora (HH:mm) de un campo datetime del lote en la zona del usuario."""
        self.ensure_one()
        valor = self[campo]
        if not valor:
            return ""
        return self._reparto_fecha_local(valor).strftime("%H:%M")
