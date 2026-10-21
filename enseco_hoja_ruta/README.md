# ENSECO - Hoja de ruta de reparto (`enseco_hoja_ruta`)

Reemplaza la hoja de ruta que ENSECO armaba a mano en una planilla. Pasa a código
las personalizaciones hechas con Studio en staging (documento técnico
"Traspaso a producción" v1.0).

## Qué hace

- **Pedido de venta**: pestaña *Reparto* con teléfono de contacto en obra,
  dirección de entrega, observaciones para logística, ¿recibe con lluvia? y
  confirmación de reparto (por defecto *Confirmado* en pedidos nuevos).
- **Remito**: pestaña *Reparto* con los datos del pedido (editar en el remito
  escribe en el pedido) y los de logística: orden de entrega, zona de reparto y
  lado de descarga.
- **Lote**: vuelta, grupo *Viaje* (km y horas de salida y regreso, km recorridos
  y duración) y lista de remitos editable, ordenada por orden de entrega, con
  botón para abrir el remito.
- **Fechas**: al cambiar la fecha programada del lote, sus remitos pendientes la
  toman; un remito que entra a un lote toma la fecha de los demás.
- **Reportes**: *Hoja de ruta ENSECO* (lote, A4 horizontal, una hoja por lote) y
  ajustes en el Recibo de entrega (ENSECO), la Etiqueta de Transferencia y las
  Operaciones de recolección.
- **Viajes (km y horas)**: Inventario › Reportes, con lista, tabla dinámica y
  gráfico.

Al instalar, activa la *Gestión de despacho* en los tipos de operación de salida
y quita del menú Imprimir de los remitos el reporte Aeroo "Hoja de ruta", que da
error en 19.0.

## Dependencias

`sale_stock`, `stock_delivery`, `stock_picking_batch`, `stock_fleet` (y por él
`fleet`), `stock_ux`, `l10n_ar_stock_ux`, `l10n_ar_stock_delivery` y
`enseco_report_custom`.

## Configuración posterior

Los datos de flota no se cargan con el módulo. En Flota hay que crear:

- Las categorías de vehículo con su **capacidad de peso** (por ejemplo,
  "Camión hasta 3.500 kg" con 3500 y "Camión hasta 8.000 kg" con 8000).
- Los vehículos propios, cada uno con su categoría.

Sin categoría con capacidad, el lote y la hoja de ruta muestran el peso total sin
porcentaje de ocupación.
