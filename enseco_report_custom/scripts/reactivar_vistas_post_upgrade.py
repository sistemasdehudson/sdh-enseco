"""
Script de reactivación de vistas post-upgrade 17→19.
Ejecutar UNA SOLA VEZ después del upgrade, con la DB estable y validada.

Mecanismo:
1. Detecta dinámicamente qué módulos AR/Adhoc están instalados.
2. Busca todas las vistas desactivadas en esos módulos.
3. Valida cada vista (activa → _get_combined_arch() → restaura).
4. Reactiva solo las que pasaron validación.
5. Documenta vistas fallidas como deuda técnica.
6. Imprime reporte final con el estado de cada vista.

Requiere reinicio manual de Odoo después de la ejecución.

Uso en Odoo.sh:
    odoo-bin shell
    >>> exec(open('/home/odoo/src/user/enseco_report_custom/scripts/reactivar_vistas_post_upgrade.py').read())
    
Después del script:
    odoosh-restart
"""

import logging
import os
import sys
import traceback
from datetime import datetime

_logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# FORZAR FLUSH INMEDIATO DE SALIDA
# ═══════════════════════════════════════════════════════════════════

class FlushLogger:
    """Wrapper que hace flush después de cada write para ver output en tiempo real."""
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def flush(self):
        self.stream.flush()

sys.stdout = FlushLogger(sys.stdout)
sys.stderr = FlushLogger(sys.stderr)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

# Módulos AR/Adhoc a considerar (se cruza con los instalados en DB)
MODULOS_AR_ADHOC = [
    'l10n_ar', 'l10n_ar_ux', 'l10n_ar_sale', 'l10n_ar_stock',
    'l10n_ar_stock_ux', 'l10n_ar_edi', 'l10n_ar_edi_ux',
    'l10n_ar_account_reports', 'l10n_ar_purchase', 'l10n_ar_pos',
    'l10n_latam_invoice_document',
    'sale_ux', 'sale_stock_ux', 'stock_ux', 'account_ux', 'purchase_stock_ux',
    'enseco_report_custom',
]

# Si True, aborta si alguna vista falla validación
STRICT_MODE = False

# Si True, intenta reiniciar Odoo automáticamente al final
AUTO_RESTART = False

# ═══════════════════════════════════════════════════════════════════
# ESTRUCTURA DE DATOS PARA REPORTE FINAL
# ═══════════════════════════════════════════════════════════════════

class VistaTracker:
    """Guarda el estado de cada vista durante todo el proceso."""
    def __init__(self, xmlid, view_id, inherit_id):
        self.xmlid = xmlid
        self.view_id = view_id
        self.inherit_id = inherit_id
        self.estado_inicial = None
        self.estado_inicial_str = "?"
        self.validacion_ok = None
        self.validacion_msg = ""
        self.reactivacion_ok = None
        self.reactivacion_msg = ""
        self.estado_final = None
        self.estado_final_str = "?"

tracker = {}

# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════

def log(msg):
    """Log con timestamp y flush inmediato."""
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

def obtener_modulos_instalados():
    """Devuelve set de módulos AR/Adhoc que están installed en esta DB."""
    instalados = set()
    for modulo in MODULOS_AR_ADHOC:
        m = env['ir.module.module'].search([
            ('name', '=', modulo),
            ('state', '=', 'installed')
        ], limit=1)
        if m:
            instalados.add(modulo)
    return instalados

def obtener_vistas_desactivadas(modulos_instalados):
    """Busca vistas desactivadas e inicializa el tracker."""
    if not modulos_instalados:
        return []

    placeholders = ','.join(['%s'] * len(modulos_instalados))

    query = f"""
        SELECT 
            imd.module || '.' || imd.name AS xmlid,
            v.id,
            imd.module,
            imd.name,
            v.inherit_id
        FROM ir_ui_view v
        JOIN ir_model_data imd ON imd.res_id = v.id AND imd.model = 'ir.ui.view'
        WHERE v.active = false
          AND imd.module IN ({placeholders})
        ORDER BY imd.module, imd.name
    """

    env.cr.execute(query, tuple(modulos_instalados))
    resultados = env.cr.fetchall()

    # Inicializar tracker
    for xmlid, vid, mod, name, inherit_id in resultados:
        view = env['ir.ui.view'].browse(vid)
        t = VistaTracker(xmlid, vid, inherit_id)
        t.estado_inicial = view.active
        t.estado_inicial_str = "ACTIVA" if view.active else "DESACTIVADA"
        tracker[xmlid] = t

    return resultados

def validar_vista(view_id, xmlid):
    """
    Intenta activar → _get_combined_arch() → restaurar.
    Retorna (ok: bool, error_message: str).
    """
    view = env['ir.ui.view'].browse(view_id)
    if not view.exists():
        msg = "No existe en DB"
        if xmlid in tracker:
            tracker[xmlid].validacion_ok = False
            tracker[xmlid].validacion_msg = msg
        return False, msg

    try:
        view.write({'active': True})

        try:
            _ = view._get_combined_arch()
        except Exception as e:
            msg = str(e).split('\n')[0][:200]
            try:
                view.write({'active': False})
            except Exception:
                pass
            if xmlid in tracker:
                tracker[xmlid].validacion_ok = False
                tracker[xmlid].validacion_msg = f"Error XML: {msg}"
            return False, f"Error XML: {msg}"

        view.write({'active': False})

        if xmlid in tracker:
            tracker[xmlid].validacion_ok = True
            tracker[xmlid].validacion_msg = "OK"
        return True, "OK"

    except Exception as e:
        msg = str(e).split('\n')[0][:200]
        try:
            view.write({'active': False})
        except Exception:
            pass
        if xmlid in tracker:
            tracker[xmlid].validacion_ok = False
            tracker[xmlid].validacion_msg = f"Error activación: {msg}"
        return False, f"Error activación: {msg}"

def reactivar_vista(view_id, xmlid):
    """Reactivar una vista que ya pasó validación."""
    view = env['ir.ui.view'].browse(view_id)
    if not view.exists():
        msg = "No existe en DB"
        if xmlid in tracker:
            tracker[xmlid].reactivacion_ok = False
            tracker[xmlid].reactivacion_msg = msg
            tracker[xmlid].estado_final_str = "?"
        return False, msg

    if view.active:
        msg = "Ya estaba activa (no-op)"
        if xmlid in tracker:
            tracker[xmlid].reactivacion_ok = True
            tracker[xmlid].reactivacion_msg = msg
            tracker[xmlid].estado_final = True
            tracker[xmlid].estado_final_str = "ACTIVA"
        return True, msg

    try:
        view.write({'active': True})
        msg = "Reactivada OK"
        if xmlid in tracker:
            tracker[xmlid].reactivacion_ok = True
            tracker[xmlid].reactivacion_msg = msg
            tracker[xmlid].estado_final = True
            tracker[xmlid].estado_final_str = "ACTIVA"
        return True, msg
    except Exception as e:
        msg = str(e).split('\n')[0][:200]
        if xmlid in tracker:
            tracker[xmlid].reactivacion_ok = False
            tracker[xmlid].reactivacion_msg = msg
            tracker[xmlid].estado_final = False
            tracker[xmlid].estado_final_str = "DESACTIVADA"
        return False, msg

def reiniciar_odoo():
    """Intenta reiniciar Odoo.sh."""
    try:
        result = os.system('odooosh-restart 2>/dev/null')
        if result == 0:
            log("✓ Reinicio de Odoo.sh ejecutado")
            return True
    except Exception:
        pass

    try:
        open('/tmp/odoo-restart', 'w').close()
        log("✓ Archivo de reinicio creado en /tmp/odoo-restart")
        return True
    except Exception:
        pass

    log("⚠ No se pudo reiniciar automáticamente")
    log("  Ejecutá manualmente: odoosh-restart")
    return False

# ═══════════════════════════════════════════════════════════════════
# REPORTE FINAL
# ═══════════════════════════════════════════════════════════════════

def imprimir_reporte_final(modulos_count):
    """Tabla detallada con el estado de cada vista procesada."""

    log("")
    log("=" * 90)
    log("REPORTE FINAL — ESTADO DE CADA VISTA PROCESADA")
    log("=" * 90)
    log("")

    header = f"{'XMLID':<55} {'INICIAL':<12} {'VALID':<8} {'REACT':<8} {'FINAL':<12} {'DETALLE'}"
    log(header)
    log("-" * len(header))

    for xmlid in sorted(tracker.keys()):
        t = tracker[xmlid]

        inicial = t.estado_inicial_str

        if t.validacion_ok is True:
            valid = "✅ OK"
        elif t.validacion_ok is False:
            valid = "❌ FALLA"
        else:
            valid = "—"

        if t.reactivacion_ok is True:
            if 'ya estaba' in t.reactivacion_msg.lower() or 'no-op' in t.reactivacion_msg.lower():
                react = "ℹ️ YA"
            else:
                react = "✅ OK"
        elif t.reactivacion_ok is False:
            react = "❌ ERR"
        else:
            react = "—"

        final = t.estado_final_str

        if t.validacion_ok is False:
            detalle = t.validacion_msg[:65]
        elif t.reactivacion_ok is False:
            detalle = t.reactivacion_msg[:65]
        elif t.reactivacion_ok is True:
            if 'ya estaba' in t.reactivacion_msg.lower():
                detalle = "Sin cambios"
            else:
                detalle = "Reactivada correctamente"
        else:
            detalle = "No procesada"

        log(f"{xmlid:<55} {inicial:<12} {valid:<8} {react:<8} {final:<12} {detalle}")

    log("-" * 90)
    log("")

    total = len(tracker)
    reactivadas_ok = sum(1 for t in tracker.values()
                        if t.reactivacion_ok is True
                        and 'ya estaba' not in t.reactivacion_msg.lower()
                        and 'no-op' not in t.reactivacion_msg.lower())
    ya_activas_count = sum(1 for t in tracker.values()
                          if t.reactivacion_ok is True
                          and ('ya estaba' in t.reactivacion_msg.lower()
                               or 'no-op' in t.reactivacion_msg.lower()))
    fallaron_valid = sum(1 for t in tracker.values() if t.validacion_ok is False)
    fallaron_react = sum(1 for t in tracker.values() if t.reactivacion_ok is False)
    sin_cambios = sum(1 for t in tracker.values()
                     if t.estado_inicial_str == t.estado_final_str
                     and t.estado_inicial_str != "?")
    cambiaron = sum(1 for t in tracker.values()
                   if t.estado_inicial_str != t.estado_final_str
                   and t.estado_inicial_str != "?" and t.estado_final_str != "?")

    log(f"  Total de vistas procesadas:              {total}")
    log(f"  Vistas que cambiaron de estado:          {cambiaron}")
    log(f"    De DESACTIVADA → ACTIVA:               {reactivadas_ok}")
    log(f"  Vistas sin cambios:                      {sin_cambios}")
    log(f"    Ya estaban ACTIVAS (no-op):             {ya_activas_count}")
    log(f"    Quedaron DESACTIVADAS por fallo:        {fallaron_valid}")
    log(f"    Error en reactivación:                 {fallaron_react}")
    log("")

    # Vistas que FALLARON
    if fallaron_valid > 0:
        log("-" * 90)
        log("⚠️  VISTAS QUE FALLARON VALIDACIÓN (DEUDA TÉCNICA)")
        log("-" * 90)
        for xmlid in sorted(tracker.keys()):
            t = tracker[xmlid]
            if t.validacion_ok is False:
                log(f"  ❌ {xmlid}")
                log(f"     ID: {t.view_id}")
                log(f"     Error: {t.validacion_msg}")
                log("")
        log(f"  Estas {fallaron_valid} vistas NO fueron reactivadas.")
        log(f"  Requieren intervención manual (corregir xpath o actualizar módulo).")
        log(f"  Reporte guardado en: /tmp/vistas_fallidas_post_upgrade.txt")
        log("")

    # Vistas REACTIVADAS
    if reactivadas_ok > 0:
        log("-" * 90)
        log("✅ VISTAS REACTIVADAS CORRECTAMENTE")
        log("-" * 90)
        for xmlid in sorted(tracker.keys()):
            t = tracker[xmlid]
            if t.reactivacion_ok is True and 'ya estaba' not in t.reactivacion_msg.lower() and 'no-op' not in t.reactivacion_msg.lower():
                log(f"  ✅ {xmlid} (id={t.view_id})")
                log(f"     {t.estado_inicial_str} → {t.estado_final_str}")
        log("")

    # Vistas que YA estaban activas
    if ya_activas_count > 0:
        log("-" * 90)
        log("ℹ️  VISTAS QUE YA ESTABAN ACTIVAS (SIN CAMBIOS)")
        log("-" * 90)
        for xmlid in sorted(tracker.keys()):
            t = tracker[xmlid]
            if t.reactivacion_ok is True and ('ya estaba' in t.reactivacion_msg.lower() or 'no-op' in t.reactivacion_msg.lower()):
                log(f"  ℹ️  {xmlid} (id={t.view_id})")
        log("")

    log("-" * 90)
    log(f"  Módulos AR/Adhoc instalados en esta DB: {modulos_count}")
    log(f"  Vistas desactivadas detectadas:         {total}")
    log("")
    log("=" * 90)
    log("")

# ═══════════════════════════════════════════════════════════════════
# PROCESO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def main():
    log("=" * 70)
    log("SCRIPT DE REACTIVACIÓN DE VISTAS POST-UPGRADE 17→19")
    log("=" * 70)
    log(f"DB: {env.cr.dbname}")
    log(f"STRICT_MODE: {STRICT_MODE}")
    log(f"AUTO_RESTART: {AUTO_RESTART}")

    # ── FASE 1: Detección de módulos ──────────────────────────
    log("\n" + "─" * 50)
    log("FASE 1: Detección de módulos AR/Adhoc instalados")
    log("─" * 50)

    modulos_instalados = obtener_modulos_instalados()
    log(f"  Módulos instalados: {len(modulos_instalados)}")
    for m in sorted(modulos_instalados):
        log(f"    ✓ {m}")

    faltantes = set(MODULOS_AR_ADHOC) - modulos_instalados
    if faltantes:
        log(f"  Módulos NO instalados (se omiten): {len(faltantes)}")
        for m in sorted(faltantes):
            log(f"    ✗ {m}")

    # ── FASE 2: Búsqueda de vistas desactivadas ───────────────
    log("\n" + "─" * 50)
    log("FASE 2: Búsqueda de vistas desactivadas")
    log("─" * 50)

    vistas = obtener_vistas_desactivadas(modulos_instalados)
    log(f"  Vistas desactivadas encontradas: {len(vistas)}")

    if not vistas:
        log("  ✓ No hay vistas para reactivar.")
        log("\n" + "=" * 70)
        log("FIN — Sin cambios")
        log("=" * 70)
        return 0

    for xmlid, vid, mod, name, inherit_id in vistas:
        log(f"    {xmlid} (id={vid}, inherit={inherit_id})")

    # ── FASE 3: Validación reversible ─────────────────────────
    log("\n" + "─" * 50)
    log("FASE 3: Validación de vistas (activa → test → restaura)")
    log("─" * 50)

    ok_list = []
    fail_list = []

    for xmlid, vid, mod, name, inherit_id in vistas:
        log(f"  Validando: {xmlid} (id={vid})...")
        ok, msg = validar_vista(vid, xmlid)
        if ok:
            log(f"    ✅ {msg}")
            ok_list.append((xmlid, vid))
        else:
            log(f"    ❌ {msg}")
            fail_list.append((xmlid, vid, msg))

    log(f"\n  RESULTADO VALIDACIÓN:")
    log(f"    ✓ OK: {len(ok_list)} vistas")
    log(f"    ✗ FALLAN: {len(fail_list)} vistas")

    # ── Control STRICT_MODE ───────────────────────────────────
    if fail_list and STRICT_MODE:
        log("\n" + "=" * 70)
        log("ABORTANDO POR STRICT_MODE=True")
        log("=" * 70)
        log("Las siguientes vistas fallaron validación:")
        for xmlid, vid, msg in fail_list:
            log(f"  ❌ {xmlid}: {msg}")
        log("\nCorregí los xpath antes de reintentar.")
        log("Cambiá STRICT_MODE=False para reactivar las OK y documentar estas.")

        with open('/tmp/vistas_fallidas_strict.txt', 'w') as f:
            f.write(f"Vistas que fallaron validación — {datetime.now()}\n")
            f.write("=" * 70 + "\n")
            for xmlid, vid, msg in fail_list:
                f.write(f"\n{xmlid} (id={vid})\n")
                f.write(f"  Error: {msg}\n")
        log("  Reporte guardado en: /tmp/vistas_fallidas_strict.txt")

        # Imprimir reporte parcial antes de abortar
        imprimir_reporte_final(len(modulos_instalados))
        return 1

    # ── FASE 4: Reactivación ──────────────────────────────────
    log("\n" + "─" * 50)
    log("FASE 4: Reactivación de vistas validadas")
    log("─" * 50)

    reactivadas = 0
    ya_activas = 0
    errores = 0

    if not ok_list:
        log("  No hay vistas OK para reactivar.")
    else:
        for xmlid, vid in ok_list:
            log(f"  Reactivando: {xmlid} (id={vid})...")
            ok, msg = reactivar_vista(vid, xmlid)
            if ok:
                if 'ya estaba' in msg.lower() or 'no-op' in msg.lower():
                    log(f"    ℹ️  {msg}")
                    ya_activas += 1
                else:
                    log(f"    ✅ {msg}")
                    reactivadas += 1
            else:
                log(f"    ❌ {msg}")
                errores += 1

        log(f"\n  RESULTADO REACTIVACIÓN:")
        log(f"    Reactivadas: {reactivadas}")
        log(f"    Ya estaban activas: {ya_activas}")
        log(f"    Errores: {errores}")

    # ── FASE 5: Reporte de vistas fallidas (deuda técnica) ────
    if fail_list:
        log("\n" + "─" * 50)
        log("FASE 5: Deuda técnica — vistas que fallaron validación")
        log("─" * 50)
        log("  Las siguientes vistas NO fueron reactivadas. Requieren intervención.")
        log("")

        for xmlid, vid, msg in fail_list:
            log(f"  ❌ {xmlid} (id={vid})")
            log(f"     {msg}")

        with open('/tmp/vistas_fallidas_post_upgrade.txt', 'w') as f:
            f.write(f"Vistas con fallos de validación — {datetime.now()}\n")
            f.write(f"DB: {env.cr.dbname}\n")
            f.write("=" * 70 + "\n\n")
            for xmlid, vid, msg in fail_list:
                f.write(f"### {xmlid} (id={vid})\n")
                f.write(f"Error: {msg}\n\n")

        log(f"\n  Reporte guardado en: /tmp/vistas_fallidas_post_upgrade.txt")

    # ── FASE 6: Reinicio ──────────────────────────────────────
    if AUTO_RESTART and ok_list:
        log("\n" + "─" * 50)
        log("FASE 6: Reinicio de Odoo")
        log("─" * 50)
        log("  Haciendo commit de los cambios...")
        env.cr.commit()
        log("  ✓ Commit OK")
        log("")
        if reiniciar_odoo():
            log("  ✓ Reinicio ejecutado. Las vistas ya están activas.")
        else:
            log("  ⚠ Ejecutá manualmente: odoosh-restart")

    # ── FASE 7: Reporte final ─────────────────────────────────
    log("\n" + "─" * 50)
    log("FASE 7: Reporte final consolidado")
    log("─" * 50)

    imprimir_reporte_final(len(modulos_instalados))

    return 0

# ═══════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════

try:
    exit_code = main()
except Exception as e:
    log(f"\n{'=' * 70}")
    log(f"ERROR FATAL NO ESPERADO")
    log(f"{'=' * 70}")
    log(f"  {type(e).__name__}: {e}")
    log(f"")
    traceback.print_exc()
    log(f"\n{'=' * 70}")
    exit_code = 1

if exit_code != 0:
    log(f"\n⚠️  El script terminó con errores (código {exit_code}).")
    log("Revisá el output más arriba para ver los detalles.")
else:
    log("\n✓ Script completado exitosamente.")
    log("")
    log("Recordá reiniciar Odoo manualmente:")
    log("  odoosh-restart")
