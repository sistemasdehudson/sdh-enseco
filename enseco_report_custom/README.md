# Enseco - Ocultar Impuestos en Reportes de Venta

## Descripción

Este módulo permite ocultar los impuestos en el reporte de pedidos de venta (`report_saleorder_document`).  

## Funcionalidad

El módulo agrega dos nuevos reportes:

### 1. Cotización sin IVA

- ✅ Oculta la columna "IVA" en el detalle de artículos
- ✅ Muestra precios con impuestos incluidos en precio unitario y subtotal
- ✅ Oculta el desglose de impuestos en la sección de totales
- ✅ Oculta la fila de subtotal, mostrando solo el total final

### 2. Cotización sin Precios ni IVA

- ✅ Oculta la columna "IVA" en el detalle de artículos
- ✅ Oculta las columnas de "Precio Unitario" y "Subtotal"
- ✅ Oculta el desglose de impuestos en la sección de totales
- ✅ Oculta la fila de subtotal
- ✅ Muestra solo el total final en el resumen

## Instalación

1. Copiar el módulo en el directorio de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "Enseco - Ocultar Impuestos" e instalar

## Uso

1. Ir a **Ventas → Pedidos**
2. Abrir o crear un pedido de venta
3. Hacer clic en **Imprimir**
4. Seleccionar una de las opciones:
   - **"Cotización sin IVA"** - Oculta impuestos, muestra precios con IVA incluido
   - **"Cotización sin Precios ni IVA"** - Oculta precios e impuestos, solo muestra el total final

El reporte estándar seguirá mostrando los impuestos y precios normalmente.

## Dependencias

- `l10n_ar_sale` - Localización Argentina para Ventas
- `sale` - Módulo de Ventas de Odoo

## Versión

- **Versión del módulo**: 19.0.1.0.0
- **Compatible con**: Odoo 19.0

## Autor

Enseco

## Licencia

LGPL-3
