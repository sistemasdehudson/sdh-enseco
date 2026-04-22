{
    "name": "Enseco - Ocultar Impuestos en Reportes de Venta",
    "summary": "Oculta impuestos en el detalle y totales del reporte de pedidos de venta ",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "website": "",
    "author": "Enseco",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        #"l10n_ar_sale",
        #"l10n_ar_stock",
        "sale",
        "stock",
    ],
    "data": [
        "views/sale_report_templates.xml",
        "data/sale_order_report.xml",
        #"views/report_deliveryslip.xml",
        #"views/stock_picking_views.xml",
    ],
}
