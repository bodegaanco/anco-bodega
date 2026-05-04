from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Salida, SalidaItem, Rendicion, RendicionItem, Cuadrilla, Producto, StockCuadrilla, Entrada
from app import db

movimientos_bp = Blueprint('movimientos', __name__, url_prefix='/movimientos')

# ── SALIDAS ──────────────────────────────────────────────────────────────────
@movimientos_bp.route('/salidas')
@login_required
def salidas():
    cuadrilla_id = request.args.get('cuadrilla_id', '')
    fecha        = request.args.get('fecha', '')
    q = Salida.query
    if cuadrilla_id:
        q = q.filter_by(cuadrilla_id=cuadrilla_id)
    salidas_list    = q.order_by(Salida.creado_en.desc()).all()
    cuadrillas      = Cuadrilla.query.filter_by(activa=True).all()
    productos_select= Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return render_template('salidas.html', salidas=salidas_list, cuadrillas=cuadrillas, productos_select=productos_select)

@movimientos_bp.route('/salidas/nueva', methods=['POST'])
@login_required
def nueva_salida():
    cuadrilla_id  = request.form.get('cuadrilla_id')
    notas         = request.form.get('notas', '')
    producto_ids  = request.form.getlist('producto_id[]')
    cantidades    = request.form.getlist('cantidad[]')

    if not cuadrilla_id:
        flash('Debes seleccionar una cuadrilla', 'error')
        return redirect(url_for('movimientos.salidas'))

    salida = Salida(cuadrilla_id=cuadrilla_id, notas=notas, usuario_id=current_user.id)
    db.session.add(salida)
    db.session.flush()

    for pid, cant in zip(producto_ids, cantidades):
        if pid and cant and int(cant) > 0:
            producto = Producto.query.get(pid)
            if not producto:
                continue
            cantidad = int(cant)

            # Descontar de bodega
            producto.stock_bodega = max(0, producto.stock_bodega - cantidad)

            # Agregar al stock de la cuadrilla
            sc = StockCuadrilla.query.filter_by(
                cuadrilla_id=cuadrilla_id, producto_id=pid).first()
            if sc:
                sc.cantidad += cantidad
            else:
                sc = StockCuadrilla(cuadrilla_id=cuadrilla_id, producto_id=pid, cantidad=cantidad)
                db.session.add(sc)

            item = SalidaItem(salida_id=salida.id, producto_id=pid, cantidad=cantidad)
            db.session.add(item)

    db.session.commit()
    flash('✅ Salida registrada correctamente', 'success')
    return redirect(url_for('movimientos.salidas'))

# ── RENDICIONES ──────────────────────────────────────────────────────────────
@movimientos_bp.route('/rendiciones')
@login_required
def rendiciones():
    cuadrilla_id = request.args.get('cuadrilla_id', '')
    q = Rendicion.query
    if cuadrilla_id:
        q = q.filter_by(cuadrilla_id=cuadrilla_id)
    rendiciones_list  = q.order_by(Rendicion.creado_en.desc()).all()
    cuadrillas        = Cuadrilla.query.filter_by(activa=True).all()
    productos_select  = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return render_template('rendiciones.html', rendiciones=rendiciones_list, cuadrillas=cuadrillas, productos_select=productos_select)

@movimientos_bp.route('/rendiciones/nueva', methods=['POST'])
@login_required
def nueva_rendicion():
    cuadrilla_id  = request.form.get('cuadrilla_id')
    numero_ot     = request.form.get('numero_ot', '').strip().upper()
    producto_ids  = request.form.getlist('producto_id[]')
    cantidades    = request.form.getlist('cantidad[]')
    forzar        = request.form.get('forzar', '0')

    if not cuadrilla_id or not numero_ot:
        flash('Debes completar todos los campos', 'error')
        return redirect(url_for('movimientos.rendiciones'))

    # ── Detectar OT duplicada ────────────────────────────────────────────────
    ot_existente = Rendicion.query.filter_by(numero_ot=numero_ot).first()
    if ot_existente and forzar != '1':
        flash(
            f'⚠️ DUPLICADO: La OT <strong>{numero_ot}</strong> ya fue registrada '
            f'el {ot_existente.creado_en.strftime("%d/%m/%Y")} '
            f'por cuadrilla <strong>{ot_existente.cuadrilla.nombre}</strong>. '
            f'Si igual quieres registrarla, confirma abajo.',
            'duplicado'
        )
        return redirect(url_for('movimientos.rendiciones',
            ot_duplicada=numero_ot,
            cuadrilla_id=cuadrilla_id,
            forzar='1'
        ))

    rendicion = Rendicion(
        cuadrilla_id=cuadrilla_id,
        numero_ot=numero_ot,
        usuario_id=current_user.id
    )
    db.session.add(rendicion)
    db.session.flush()

    for pid, cant in zip(producto_ids, cantidades):
        if pid and cant and int(cant) > 0:
            cantidad = int(cant)
            # Descontar del stock de la cuadrilla
            sc = StockCuadrilla.query.filter_by(
                cuadrilla_id=cuadrilla_id, producto_id=pid).first()
            if sc:
                sc.cantidad = max(0, sc.cantidad - cantidad)

            item = RendicionItem(
                rendicion_id=rendicion.id,
                producto_id=pid,
                cantidad_usada=cantidad
            )
            db.session.add(item)

    db.session.commit()
    flash(f'✅ OT {numero_ot} registrada correctamente', 'success')
    return redirect(url_for('movimientos.rendiciones'))

# ── HISTORIAL ─────────────────────────────────────────────────────────────────
@movimientos_bp.route('/historial')
@login_required
def historial():
    cuadrilla_id = request.args.get('cuadrilla_id', '')
    cuadrillas   = Cuadrilla.query.filter_by(activa=True).all()
    salidas      = []
    cuadrilla    = None
    if cuadrilla_id:
        cuadrilla = Cuadrilla.query.get(cuadrilla_id)
        salidas   = Salida.query.filter_by(cuadrilla_id=cuadrilla_id)\
                        .order_by(Salida.creado_en.desc()).all()
    else:
        salidas = Salida.query.order_by(Salida.creado_en.desc()).limit(50).all()
    return render_template('historial.html',
        salidas=salidas, cuadrillas=cuadrillas, cuadrilla=cuadrilla)


@movimientos_bp.route('/salidas/anular/<int:id>', methods=['POST'])
@login_required
def anular_salida(id):
    salida = Salida.query.get_or_404(id)
    motivo = request.form.get('motivo', 'Sin motivo')

    if salida.anulada:
        flash('Esta salida ya fue anulada', 'error')
        return redirect(url_for('movimientos.salidas'))

    # Revertir stock — devolver a bodega y quitar de cuadrilla
    for item in salida.items:
        producto = Producto.query.get(item.producto_id)
        if producto:
            producto.stock_bodega += item.cantidad

        sc = StockCuadrilla.query.filter_by(
            cuadrilla_id=salida.cuadrilla_id,
            producto_id=item.producto_id
        ).first()
        if sc:
            sc.cantidad = max(0, sc.cantidad - item.cantidad)

    salida.anulada          = True
    salida.motivo_anulacion = motivo
    db.session.commit()
    flash(f'✅ Salida anulada correctamente. Stock revertido.', 'success')
    return redirect(url_for('movimientos.salidas'))
    
# ── Movimientos anular ─────────────────────────────────────────────────────────────────

@movimientos_bp.route('/rendiciones/anular/<int:id>', methods=['POST'])
@login_required
def anular_rendicion(id):
    rendicion = Rendicion.query.get_or_404(id)
    motivo    = request.form.get('motivo', 'Sin motivo')

    if rendicion.anulada:
        flash('Esta rendición ya fue anulada', 'error')
        return redirect(url_for('movimientos.rendiciones'))

    # Revertir stock — devolver materiales a la cuadrilla
    for item in rendicion.items:
        sc = StockCuadrilla.query.filter_by(
            cuadrilla_id=rendicion.cuadrilla_id,
            producto_id=item.producto_id
        ).first()
        if sc:
            sc.cantidad += item.cantidad_usada
        else:
            sc = StockCuadrilla(
                cuadrilla_id=rendicion.cuadrilla_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad_usada
            )
            db.session.add(sc)

    rendicion.anulada          = True
    rendicion.motivo_anulacion = motivo
    db.session.commit()
    flash(f'✅ Rendición OT {rendicion.numero_ot} anulada. Stock revertido.', 'success')
    return redirect(url_for('movimientos.rendiciones'))


# ── Revisar OT ─────────────────────────────────────────────────────────────────

@movimientos_bp.route('/rendiciones/revisar/<int:id>', methods=['POST'])
@login_required
def revisar_rendicion(id):
    rendicion = Rendicion.query.get_or_404(id)
    resultado = request.form.get('resultado')  # 'ok' o 'diferencia'
    if not rendicion.anulada:
        rendicion.estado       = resultado
        rendicion.revisada_por = current_user.nombre
        db.session.commit()
        if resultado == 'ok':
            flash(f'✅ OT {rendicion.numero_ot} confirmada correcta', 'success')
        else:
            flash(f'⚠️ OT {rendicion.numero_ot} marcada con diferencias — puedes editarla', 'warning')
    return redirect(url_for('movimientos.rendiciones'))


@movimientos_bp.route('/rendiciones/editar/<int:id>', methods=['POST'])
@login_required
def editar_rendicion(id):
    rendicion = Rendicion.query.get_or_404(id)
    if rendicion.anulada:
        flash('No se puede editar una OT anulada', 'error')
        return redirect(url_for('movimientos.rendiciones'))

    # Primero revertir stock actual de esta rendicion
    for item in rendicion.items:
        sc = StockCuadrilla.query.filter_by(
            cuadrilla_id=rendicion.cuadrilla_id,
            producto_id=item.producto_id
        ).first()
        if sc:
            sc.cantidad += item.cantidad_usada
        db.session.delete(item)

    # Guardar nuevos items
    productos_ids = request.form.getlist('producto_id[]')
    cantidades    = request.form.getlist('cantidad[]')
    for pid, cant in zip(productos_ids, cantidades):
        if not pid or not cant:
            continue
        cant = int(cant)
        item = RendicionItem(
            rendicion_id=rendicion.id,
            producto_id=int(pid),
            cantidad_usada=cant
        )
        db.session.add(item)
        # Descontar del stock cuadrilla con los nuevos valores
        sc = StockCuadrilla.query.filter_by(
            cuadrilla_id=rendicion.cuadrilla_id,
            producto_id=int(pid)
        ).first()
        if sc:
            sc.cantidad = max(0, sc.cantidad - cant)

    rendicion.estado = 'pendiente'  # vuelve a pendiente para re-revisar
    db.session.commit()
    flash(f'✅ OT {rendicion.numero_ot} actualizada — vuelve a estado pendiente para re-revisar', 'success')
    return redirect(url_for('movimientos.rendiciones'))

