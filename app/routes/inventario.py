from flask import Blueprint, render_template, request, redirect, url_for, flash
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
        producto   = Producto.query.get(pid)
        cant_real  = int(cant_real)

        if tipo == 'bodega':
            stock_sistema        = producto.stock_bodega
            diferencia           = cant_real - stock_sistema
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
    flash('✅ Inventario aplicado y stock ajustado', 'success')
    return redirect(url_for('inventario.index'))
