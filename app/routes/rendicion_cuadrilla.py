from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Cuadrilla, Producto, StockCuadrilla, Salida, SalidaItem
from app import db
from datetime import datetime

rendicion_cuadrilla_bp = Blueprint('rendicion_cuadrilla', __name__, url_prefix='/rendicion-cuadrilla')

@rendicion_cuadrilla_bp.route('/')
@login_required
def index():
    cuadrillas = Cuadrilla.query.filter_by(activa=True).all()
    # Mostrar rendiciones (salidas con tipo='rendicion_cuadrilla')
    rendiciones = Salida.query.filter_by(tipo='rendicion_cuadrilla')\
        .order_by(Salida.creado_en.desc()).all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return render_template('rendicion_cuadrilla.html',
        cuadrillas=cuadrillas, rendiciones=rendiciones, productos_select=productos,
        now=datetime.now())

@rendicion_cuadrilla_bp.route('/nueva', methods=['POST'])
@login_required
def nueva():
    cuadrilla_id  = request.form.get('cuadrilla_id')
    notas         = request.form.get('notas', '')
    fecha_str     = request.form.get('fecha_entrega', '')
    hora_str      = request.form.get('hora_entrega', '00:00')
    producto_ids  = request.form.getlist('producto_id[]')
    cantidades    = request.form.getlist('cantidad[]')

    if not cuadrilla_id:
        flash('Debes seleccionar una cuadrilla', 'error')
        return redirect(url_for('rendicion_cuadrilla.index'))

    try:
        fecha_dt = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M") if fecha_str else datetime.utcnow()
    except:
        fecha_dt = datetime.utcnow()

    # Usar Salida con tipo especial para no confundir con entregas normales
    salida = Salida(cuadrilla_id=cuadrilla_id, notas=notas,
                    usuario_id=current_user.id, creado_en=fecha_dt,
                    tipo='rendicion_cuadrilla')
    db.session.add(salida)
    db.session.flush()

    for pid, cant in zip(producto_ids, cantidades):
        if not pid or cant == '':
            continue
        cantidad = float(cant)
        if cantidad <= 0:
            continue

        # Descontar del stock cuadrilla
        sc = StockCuadrilla.query.filter_by(
            cuadrilla_id=cuadrilla_id, producto_id=pid).first()
        if sc:
            sc.cantidad = max(0, sc.cantidad - cantidad)

        item = SalidaItem(salida_id=salida.id, producto_id=pid, cantidad=cantidad)
        db.session.add(item)

    db.session.commit()
    flash('✅ Rendición registrada y stock de cuadrilla actualizado', 'success')
    return redirect(url_for('rendicion_cuadrilla.index'))
