from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Inventario, InventarioItem, Cuadrilla, Producto, StockCuadrilla
from app import db
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/')
@login_required
def index():
    # Filtros
    cuadrilla_id = request.args.get('cuadrilla_id', '')
    tipo_filtro  = request.args.get('tipo', '')

    q = Inventario.query
    if cuadrilla_id:
        q = q.filter_by(cuadrilla_id=cuadrilla_id)
    if tipo_filtro:
        q = q.filter_by(tipo=tipo_filtro)

    inventarios = q.order_by(Inventario.creado_en.desc()).all()
    cuadrillas  = Cuadrilla.query.filter_by(activa=True).all()
    productos   = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()

    return render_template('inventario.html',
        inventarios=inventarios, cuadrillas=cuadrillas,
        productos=productos, now=datetime.now(),
        cuadrilla_filtro=cuadrilla_id, tipo_filtro=tipo_filtro)


@inventario_bp.route('/detalle/<int:inv_id>')
@login_required
def detalle(inv_id):
    inv = Inventario.query.get_or_404(inv_id)
    return jsonify({
        'id':        inv.id,
        'tipo':      inv.tipo,
        'fecha':     inv.creado_en.strftime('%d/%m/%Y %H:%M'),
        'cuadrilla': inv.cuadrilla.nombre if inv.cuadrilla else 'Bodega',
        'usuario':   inv.usuario.nombre if inv.usuario else '—',
        'items': [{
            'nombre':       item.producto.descripcion,
            'codigo':       item.producto.codigo,
            'unidad':       item.producto.unidad,
            'sistema':      item.stock_sistema,
            'real':         item.stock_real,
            'diferencia':   item.diferencia,
        } for item in inv.items]
    })


@inventario_bp.route('/stock_cuadrilla/<int:cuadrilla_id>')
@login_required
def stock_cuadrilla(cuadrilla_id):
    stocks = StockCuadrilla.query.filter_by(cuadrilla_id=cuadrilla_id).all()
    data = []
    for sc in stocks:
        if sc.cantidad > 0:
            data.append({
                'producto_id': sc.producto_id,
                'nombre':      sc.producto.descripcion,
                'codigo':      sc.producto.codigo,
                'unidad':      sc.producto.unidad,
                'cantidad':    sc.cantidad,
            })
    return jsonify(data)


@inventario_bp.route('/nuevo', methods=['POST'])
@login_required
def nuevo():
    tipo         = request.form.get('tipo')
    cuadrilla_id = request.form.get('cuadrilla_id') or None
    fecha_inv    = request.form.get('fecha_inventario', '')
    producto_ids = request.form.getlist('producto_id[]')
    cantidades   = request.form.getlist('cantidad_real[]')

    # Fecha manual
    if fecha_inv:
        try:
            fecha_dt = datetime.strptime(fecha_inv, '%Y-%m-%d')
        except:
            fecha_dt = datetime.utcnow()
    else:
        fecha_dt = datetime.utcnow()

    inv = Inventario(tipo=tipo, cuadrilla_id=cuadrilla_id,
                     usuario_id=current_user.id, creado_en=fecha_dt)
    db.session.add(inv)
    db.session.flush()

    for pid, cant_real in zip(producto_ids, cantidades):
        if not pid or cant_real == '':
            continue
        producto  = Producto.query.get(pid)
        cant_real = float(cant_real)

        if tipo == 'bodega':
            stock_sistema         = producto.stock_bodega
            diferencia            = cant_real - stock_sistema
            producto.stock_bodega = cant_real
        else:
            sc = StockCuadrilla.query.filter_by(
                cuadrilla_id=cuadrilla_id, producto_id=pid).first()
            stock_sistema = sc.cantidad if sc else 0
            diferencia    = cant_real - stock_sistema
            if sc:
                sc.cantidad = cant_real
            else:
                sc = StockCuadrilla(cuadrilla_id=cuadrilla_id,
                                    producto_id=pid, cantidad=cant_real)
                db.session.add(sc)

        item = InventarioItem(
            inventario_id=inv.id,
            producto_id=pid,
            stock_sistema=stock_sistema,
            stock_real=cant_real,
            diferencia=diferencia
        )
        db.session.add(item)

    db.session.commit()
    flash('✅ Inventario registrado y stock actualizado', 'success')
    return redirect(url_for('inventario.index'))


@inventario_bp.route('/cargar_excel', methods=['POST'])
@login_required
def cargar_excel():
    import openpyxl
    from io import BytesIO

    archivo      = request.files.get('archivo_excel')
    tipo         = request.form.get('tipo', 'bodega')
    cuadrilla_id = request.form.get('cuadrilla_id') or None
    fecha_inv    = request.form.get('fecha_inventario', '')

    if not archivo or archivo.filename == '':
        flash('Debes seleccionar un archivo Excel', 'error')
        return redirect(url_for('inventario.index'))

    try:
        wb = openpyxl.load_workbook(BytesIO(archivo.read()))
        ws = wb.active
    except Exception as e:
        flash(f'Error al leer el Excel: {str(e)}', 'error')
        return redirect(url_for('inventario.index'))

    filas = []
    for row in ws.iter_rows(values_only=True):
        if not row[1] or not row[2]:
            continue
        try:
            codigo   = str(int(row[1])).strip()
            cantidad = float(row[2])
            filas.append((codigo, cantidad))
        except:
            continue

    if not filas:
        flash('No se encontraron datos válidos en el Excel', 'error')
        return redirect(url_for('inventario.index'))

    if fecha_inv:
        try:
            fecha_dt = datetime.strptime(fecha_inv, '%Y-%m-%d')
        except:
            fecha_dt = datetime.utcnow()
    else:
        fecha_dt = datetime.utcnow()

    inv = Inventario(tipo=tipo, cuadrilla_id=cuadrilla_id,
                     usuario_id=current_user.id, creado_en=fecha_dt)
    db.session.add(inv)
    db.session.flush()

    ajustados = 0
    no_encontrados = []

    for codigo, cant_real in filas:
        producto = Producto.query.filter_by(codigo=codigo, activo=True).first()
        if not producto:
            no_encontrados.append(codigo)
            continue

        if tipo == 'bodega':
            stock_sistema         = producto.stock_bodega
            diferencia            = cant_real - stock_sistema
            producto.stock_bodega = cant_real
        else:
            sc = StockCuadrilla.query.filter_by(
                cuadrilla_id=cuadrilla_id, producto_id=producto.id).first()
            stock_sistema = sc.cantidad if sc else 0
            diferencia    = cant_real - stock_sistema
            if sc:
                sc.cantidad = cant_real
            else:
                sc = StockCuadrilla(cuadrilla_id=cuadrilla_id,
                                    producto_id=producto.id, cantidad=cant_real)
                db.session.add(sc)

        item = InventarioItem(
            inventario_id=inv.id,
            producto_id=producto.id,
            stock_sistema=stock_sistema,
            stock_real=cant_real,
            diferencia=diferencia
        )
        db.session.add(item)
        ajustados += 1

    db.session.commit()
    msg = f'✅ {ajustados} producto(s) ajustados desde Excel'
    if no_encontrados:
        msg += f' — {len(no_encontrados)} código(s) no encontrados: {", ".join(no_encontrados[:5])}'
    flash(msg, 'success')
    return redirect(url_for('inventario.index'))
