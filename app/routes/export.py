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
    ws.title = 'Comparativo Mensual'

    meses_es = ['', 'Enero','Febrero','Marzo','Abril','Mayo','Junio',
                'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    ws.merge_cells('A1:F1')
    ws['A1'] = f'ANCO — Consumo por Cuadrilla — {meses_es[mes]} {año}'
    ws['A1'].font      = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 28

    # ── Hoja 1: Resumen por cuadrilla ──
    headers = ['Cuadrilla', 'N° Salidas', 'N° OT Rendidas', 'Productos distintos usados']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')

    cuadrillas = Cuadrilla.query.filter_by(activa=True).all()
    for row_n, c_obj in enumerate(cuadrillas, 3):
        salidas_mes = Salida.query.filter(
            Salida.cuadrilla_id == c_obj.id,
            db.func.extract('year',  Salida.creado_en) == año,
            db.func.extract('month', Salida.creado_en) == mes
        ).count()
        ots_mes = Rendicion.query.filter(
            Rendicion.cuadrilla_id == c_obj.id,
            db.func.extract('year',  Rendicion.creado_en) == año,
            db.func.extract('month', Rendicion.creado_en) == mes
        ).count()
        prods_distintos = db.session.query(func.count(func.distinct(RendicionItem.producto_id)))\
            .join(Rendicion)\
            .filter(
                Rendicion.cuadrilla_id == c_obj.id,
                db.func.extract('year',  Rendicion.creado_en) == año,
                db.func.extract('month', Rendicion.creado_en) == mes
            ).scalar() or 0

        for col_n, val in enumerate([c_obj.nombre, salidas_mes, ots_mes, prods_distintos], 1):
            cell = ws.cell(row=row_n, column=col_n, value=val)
            cell.border = borde_fino()
            if row_n % 2 == 0:
                cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)

    auto_ancho(ws)

    # ── Hoja 2: Detalle por cuadrilla ──
    ws2 = wb.create_sheet('Detalle Consumo')
    ws2.merge_cells('A1:F1')
    ws2['A1'] = f'Detalle de consumo por OT — {meses_es[mes]} {año}'
    ws2['A1'].font      = Font(bold=True, size=12, color='FFFFFF')
    ws2['A1'].fill      = PatternFill('solid', fgColor=AZUL_OSCURO)
    ws2['A1'].alignment = Alignment(horizontal='center')

    headers2 = ['Cuadrilla', 'N° OT', 'Fecha', 'Producto', 'Cantidad', 'Unidad']
    for i, h in enumerate(headers2, 1):
        c = ws2.cell(row=2, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center')

    rendiciones = Rendicion.query.filter(
        db.func.extract('year',  Rendicion.creado_en) == año,
        db.func.extract('month', Rendicion.creado_en) == mes
    ).order_by(Rendicion.cuadrilla_id, Rendicion.creado_en).all()

    row_n = 3
    for r in rendiciones:
        for item in r.items:
            for col_n, val in enumerate([
                r.cuadrilla.nombre, r.numero_ot,
                r.creado_en.strftime('%d/%m/%Y'),
                item.producto.descripcion,
                item.cantidad_usada,
                item.producto.unidad
            ], 1):
                cell = ws2.cell(row=row_n, column=col_n, value=val)
                cell.border = borde_fino()
                if row_n % 2 == 0:
                    cell.fill = PatternFill('solid', fgColor=GRIS_CLARO)
            row_n += 1

    auto_ancho(ws2)

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
