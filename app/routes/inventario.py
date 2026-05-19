from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Inventario, InventarioItem, Cuadrilla, Producto, StockCuadrilla
from app import db

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/')
@login_required
def index():
    inventarios = Inventario.query.order_by(Inventario.creado_en.desc()).all()
    cuadrillas  = Cuadrilla.query.filter_by(activa=True).all()
    productos   = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return render_template('inventario.html',
        inventarios=inventarios, cuadrillas=cuadrillas, productos=productos)

@inventario_bp.route('/stock_cuadrilla/<int:cuadrilla_id>')
@login_required
def stock_cuadrilla(cuadrilla_id):
    """API: retorna stock teorico de una cuadrilla para precargar inventario"""
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
    tipo         = request.form.get('tipo')  # bodega | cuadrilla
    cuadrilla_id = request.form.get('cuadrilla_id') or None
    producto_ids = request.form.getlist('producto_id[]')
    cantidades   = request.form.getlist('cantidad_real[]')

    inv = Inventario(tipo=tipo, cuadrilla_id=cuadrilla_id, usuario_id=current_user.id)
    db.session.add(inv)
    db.session.flush()

    for pid, cant_real in zip(producto_ids, cantidades):
        if not pid or cant_real == '':
            continue
        producto  = Producto.query.get(pid)
        cant_real = float(cant_real)

        if tipo == 'bodega':
            # Solo toca stock bodega — NO toca cuadrillas
            stock_sistema         = producto.stock_bodega
            diferencia            = cant_real - stock_sistema
            producto.stock_bodega = cant_real
        else:
            # Solo toca stock cuadrilla — NO toca bodega
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
    flash('✅ Inventario aplicado y stock ajustado', 'success')
    return redirect(url_for('inventario.index'))


@inventario_bp.route('/cargar_excel', methods=['POST'])
@login_required
def cargar_excel():
    import openpyxl
    from io import BytesIO

    archivo = request.files.get('archivo_excel')
    tipo    = request.form.get('tipo', 'bodega')
    cuadrilla_id = request.form.get('cuadrilla_id') or None

    if not archivo or archivo.filename == '':
        flash('Debes seleccionar un archivo Excel', 'error')
        return redirect(url_for('inventario.index'))

    try:
        wb = openpyxl.load_workbook(BytesIO(archivo.read()))
        ws = wb.active
    except Exception as e:
        flash(f'Error al leer el Excel: {str(e)}', 'error')
        return redirect(url_for('inventario.index'))

    # Leer filas — formato: col A = nombre, col B = código, col C = cantidad
    filas = []
    for row in ws.iter_rows(values_only=True):
        if not row[1] or not row[2]:
            continue
        try:
            codigo  = str(int(row[1])).strip()
            cantidad = float(row[2])
            filas.append((codigo, cantidad))
        except:
            continue

    if not filas:
        flash('No se encontraron datos válidos en el Excel', 'error')
        return redirect(url_for('inventario.index'))

    # Crear inventario
    inv = Inventario(tipo=tipo, cuadrilla_id=cuadrilla_id, usuario_id=current_user.id)
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
