from flask import Blueprint, send_file, request
from flask_login import login_required
from app.models import Producto, Cuadrilla, Salida, SalidaItem, Rendicion, RendicionItem, PrestamoMaquinaria
from app import db
from sqlalchemy import func
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

export_bp = Blueprint('export', __name__, url_prefix='/export')

# Colores ANCO
AZUL       = '3E88D6'
AZUL_OSCURO= '0d1f35'
GRIS_CLARO = 'f0f4f8'
ROJO       = 'e63946'
VERDE      = '2a9d8f'
NARANJO    = 'f4a261'

def estilo_header(ws, fila, cols, color=AZUL_OSCURO):
    for col in range(1, cols + 1):
        cell = ws.cell(row=fila, column=col)
        cell.font      = Font(bold=True, color='FFFFFF', size=10)
        cell.fill      = PatternFill('solid', fgColor=color)
        cell.alignment = Alignment(horizontal='center', vertical='center')

def borde_fino():
    lado = Side(style='thin', color='DDDDDD')
    return Border(left=lado, right=lado, top=lado, bottom=lado)

def auto_ancho(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)


# ── STOCK BODEGA ────────────────────────────────────────────────────────────
@export_bp.route('/stock')
@login_required
def stock():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Stock Bodega'

    # Título
    ws.merge_cells('A1:H1')
    ws['A1'] = f'ANCO BODEGA — Stock al {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A1'].font      = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 28

    # Headers
    headers = ['Código', 'Descripción', 'Categoría', 'Unidad', 'Stock Actual', 'Stock Mínimo', 'Estado', 'Diferencia']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.font      = Font(bold=True, color='FFFFFF', size=10)
        c.fill      = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')
    ws.row_dimensions[2].height = 20

    productos = Producto.query.filter_by(activo=True).order_by(Producto.categoria, Producto.descripcion).all()
    for row_n, p in enumerate(productos, 3):
        alerta = p.alerta()
        estado = '⚠️ CRÍTICO' if alerta == 'critico' else ('⚡ BAJO' if alerta == 'bajo' else '✅ Normal')
        dif    = p.stock_bodega - p.stock_min
        row_data = [p.codigo, p.descripcion, p.categoria, p.unidad, p.stock_bodega, p.stock_min, estado, dif]
        for col_n, val in enumerate(row_data, 1):
            c = ws.cell(row=row_n, column=col_n, value=val)
            c.border    = borde_fino()
            c.alignment = Alignment(vertical='center')
            if alerta == 'critico':
                c.fill = PatternFill('solid', fgColor='FFEAEA')
            elif alerta == 'bajo':
                c.fill = PatternFill('solid', fgColor='FFF4E5')
            elif row_n % 2 == 0:
                c.fill = PatternFill('solid', fgColor=GRIS_CLARO)

    auto_ancho(ws)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'ANCO_Stock_{datetime.now().strftime("%Y%m%d")}.xlsx')


# ── LISTA DE COMPRAS ────────────────────────────────────────────────────────
@export_bp.route('/compras')
@login_required
def compras():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Lista de Compras'

    ws.merge_cells('A1:F1')
    ws['A1'] = f'ANCO — Lista de Compras al {datetime.now().strftime("%d/%m/%Y")}'
    ws['A1'].font      = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 28

    headers = ['Código', 'Descripción', 'Categoría', 'Unidad', 'Stock Actual', 'Cantidad a Reponer']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=ROJO)
        c.alignment = Alignment(horizontal='center')

    productos = Producto.query.filter(
        Producto.activo == True,
        Producto.stock_bodega <= Producto.stock_min
    ).order_by(Producto.stock_bodega).all()

    for row_n, p in enumerate(productos, 3):
        falta = p.stock_min - p.stock_bodega
        row_data = [p.codigo, p.descripcion, p.categoria, p.unidad, p.stock_bodega, max(falta, 1)]
        for col_n, val in enumerate(row_data, 1):
            c = ws.cell(row=row_n, column=col_n, value=val)
            c.border = borde_fino()
            if row_n % 2 == 0:
                c.fill = PatternFill('solid', fgColor='FFF4E5')

    auto_ancho(ws)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'ANCO_Compras_{datetime.now().strftime("%Y%m%d")}.xlsx')


# ── COMPARATIVO MENSUAL ──────────────────────────────────────────────────────
@export_bp.route('/comparativo')
@login_required
def comparativo():
    año  = request.args.get('año',  datetime.now().year, type=int)
    mes  = request.args.get('mes',  datetime.now().month, type=int)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Resumen por Cuadrilla'

    meses_es = ['', 'Enero','Febrero','Marzo','Abril','Mayo','Junio',
                'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    # ── Hoja 1: Resumen Entregado vs Utilizado ──
    ws.merge_cells('A1:G1')
    ws['A1'] = f'ANCO — Entregado vs Utilizado por Cuadrilla — {meses_es[mes]} {año}'
    ws['A1'].font      = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 28

    headers = ['Cuadrilla', 'N° Entregas', 'Prods. Entregados',
               'Total Entregado', 'Prods. Utilizados', 'Total Utilizado', 'Diferencia']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center', wrap_text=True)
    ws.row_dimensions[2].height = 32

    cuadrillas = Cuadrilla.query.filter_by(activa=True).all()
    for row_n, c_obj in enumerate(cuadrillas, 3):
        salidas_mes = Salida.query.filter(
            Salida.cuadrilla_id == c_obj.id,
            Salida.anulada == False,
            db.func.extract('year',  Salida.creado_en) == año,
            db.func.extract('month', Salida.creado_en) == mes
        ).all()
        items_sal       = [i for s in salidas_mes for i in s.items]
        total_entregado = sum(i.cantidad for i in items_sal)
        prods_entregados = len(set(i.producto_id for i in items_sal))

        from app.models import RendicionSalida, RendicionSalidaItem
        rend_items = db.session.query(RendicionSalidaItem)            .join(RendicionSalida)            .filter(
                RendicionSalida.cuadrilla_id == c_obj.id,
                db.func.extract('year',  RendicionSalida.creado_en) == año,
                db.func.extract('month', RendicionSalida.creado_en) == mes
            ).all()
        total_utilizado  = sum(i.cantidad_rendida for i in rend_items)
        prods_utilizados = len(set(i.producto_id for i in rend_items))
        diferencia       = total_entregado - total_utilizado

        for col_n, val in enumerate([c_obj.nombre, len(salidas_mes), prods_entregados,
                                      total_entregado, prods_utilizados, total_utilizado, diferencia], 1):
            cell = ws.cell(row=row_n, column=col_n, value=val)
            cell.border = borde_fino()
            if row_n % 2 == 0:
                cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)
            if col_n == 7:
                cell.font = Font(bold=True, color='E63946' if isinstance(val, (int,float)) and val > 0 else '2A9D8F')

    auto_ancho(ws)

    # ── Hoja 2: Detalle Entregas (Salidas) ──
    ws2 = wb.create_sheet('Detalle Entregas')
    ws2.merge_cells('A1:G1')
    ws2['A1'] = f'Detalle de Entregas — {meses_es[mes]} {año}'
    ws2['A1'].font      = Font(bold=True, size=12, color='FFFFFF')
    ws2['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws2['A1'].alignment = Alignment(horizontal='center')

    for i, h in enumerate(['Cuadrilla','Fecha','Producto','Código','Cant. Entregada','Unidad','Notas'], 1):
        c = ws2.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')

    salidas_todas = Salida.query.filter(
        Salida.anulada == False,
        db.func.extract('year',  Salida.creado_en) == año,
        db.func.extract('month', Salida.creado_en) == mes
    ).order_by(Salida.cuadrilla_id, Salida.creado_en).all()

    row_n = 3
    for s in salidas_todas:
        for item in s.items:
            for col_n, val in enumerate([s.cuadrilla.nombre, s.creado_en.strftime('%d/%m/%Y %H:%M'),
                item.producto.descripcion, item.producto.codigo, item.cantidad,
                item.producto.unidad, s.notas or ''], 1):
                cell = ws2.cell(row=row_n, column=col_n, value=val)
                cell.border = borde_fino()
                if row_n % 2 == 0: cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)
            row_n += 1
    auto_ancho(ws2)

    # ── Hoja 3: Detalle Utilizado (Rendiciones por Salida) ──
    ws3 = wb.create_sheet('Detalle Utilizado')
    ws3.merge_cells('A1:F1')
    ws3['A1'] = f'Detalle de Material Utilizado — {meses_es[mes]} {año}'
    ws3['A1'].font      = Font(bold=True, size=12, color='FFFFFF')
    ws3['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws3['A1'].alignment = Alignment(horizontal='center')

    for i, h in enumerate(['Cuadrilla','Fecha Rendición','Producto','Código','Cant. Utilizada','Unidad'], 1):
        c = ws3.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')

    from app.models import RendicionSalida, RendicionSalidaItem
    rend_todas = db.session.query(RendicionSalida, RendicionSalidaItem)        .join(RendicionSalidaItem)        .filter(
            db.func.extract('year',  RendicionSalida.creado_en) == año,
            db.func.extract('month', RendicionSalida.creado_en) == mes
        ).order_by(RendicionSalida.cuadrilla_id, RendicionSalida.creado_en).all()

    row_n = 3
    for rend, item in rend_todas:
        for col_n, val in enumerate([rend.cuadrilla.nombre, rend.creado_en.strftime('%d/%m/%Y'),
            item.producto.descripcion, item.producto.codigo,
            item.cantidad_rendida, item.producto.unidad], 1):
            cell = ws3.cell(row=row_n, column=col_n, value=val)
            cell.border = borde_fino()
            if row_n % 2 == 0: cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)
        row_n += 1
    auto_ancho(ws3)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'ANCO_Comparativo_{meses_es[mes]}_{año}.xlsx')

# ── HISTORIAL SALIDAS ────────────────────────────────────────────────────────
@export_bp.route('/salidas')
@login_required
def salidas():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Historial Salidas'

    ws.merge_cells('A1:F1')
    ws['A1'] = f'ANCO — Historial de Salidas al {datetime.now().strftime("%d/%m/%Y")}'
    ws['A1'].font      = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws['A1'].alignment = Alignment(horizontal='center')

    headers = ['Fecha/Hora', 'Cuadrilla', 'Producto', 'Cantidad', 'Unidad', 'Notas']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')

    salidas_list = Salida.query.order_by(Salida.creado_en.desc()).all()
    row_n = 3
    for s in salidas_list:
        for item in s.items:
            for col_n, val in enumerate([
                s.creado_en.strftime('%d/%m/%Y %H:%M'),
                s.cuadrilla.nombre,
                item.producto.descripcion,
                item.cantidad,
                item.producto.unidad,
                s.notas or ''
            ], 1):
                cell = ws.cell(row=row_n, column=col_n, value=val)
                cell.border = borde_fino()
                if row_n % 2 == 0:
                    cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)
            row_n += 1

    auto_ancho(ws)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'ANCO_Salidas_{datetime.now().strftime("%Y%m%d")}.xlsx')
