from odoo import SUPERUSER_ID, api

from odoo.addons.enseco_hoja_ruta.hooks import _reparto_precision_peso


def migrate(cr, version):
    """Bases que ya tenían el módulo: el post_init_hook no vuelve a correr al actualizar."""
    _reparto_precision_peso(api.Environment(cr, SUPERUSER_ID, {}))
