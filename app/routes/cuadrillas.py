from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Cuadrilla, StockCuadrilla, Producto
from app import db

cuadrillas_bp = Blueprint('cuadrillas', __name__, url_prefix='/cuadrillas')

@cuadrillas_bp.route('/')
@login_required
def index():
    cuadrillas = Cuadrilla.query.order_by(Cuadrilla.activa.desc(), Cuadrilla.nombre).all()
    return render_template('cuadrillas.html', cuadrillas=cuadrillas)

@cuadrillas_bp.route('/nueva', methods=['POST'])
@login_required
def nueva():
    nombre = request.form.get('nombre')
    notas  = request.form.get('notas', '')
    if nombre:
        c = Cuadrilla(nombre=nombre, notas=notas)
        db.session.add(c)
        db.session.commit()
        flash(f'✅ Cuadrilla {nombre} agregada', 'success')
    return redirect(url_for('cuadrillas.index'))

@cuadrillas_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
def toggle(id):
    c = Cuadrilla.query.get_or_404(id)
    c.activa = not c.activa
    db.session.commit()
    estado = 'activada' if c.activa else 'desactivada'
    flash(f'✅ Cuadrilla {c.nombre} {estado}', 'success')
    return redirect(url_for('cuadrillas.index'))

@cuadrillas_bp.route('/<int:id>')
@login_required
def detalle(id):
    cuadrilla = Cuadrilla.query.get_or_404(id)
    stock     = StockCuadrilla.query.filter_by(cuadrilla_id=id).all()
    return render_template('cuadrilla_detalle.html', cuadrilla=cuadrilla, stock=stock)

@cuadrillas_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    from app.models import StockCuadrilla, Salida, Rendicion
    c = Cuadrilla.query.get_or_404(id)
    tiene_salidas     = Salida.query.filter_by(cuadrilla_id=id).first()
    tiene_rendiciones = Rendicion.query.filter_by(cuadrilla_id=id).first()
    if tiene_salidas or tiene_rendiciones:
        flash(f'⚠️ No se puede eliminar "{c.nombre}" porque tiene movimientos registrados. Puedes desactivarla en su lugar.', 'error')
        return redirect(url_for('cuadrillas.index'))
    StockCuadrilla.query.filter_by(cuadrilla_id=id).delete()
    db.session.delete(c)
    db.session.commit()
    flash(f'🗑️ Cuadrilla "{c.nombre}" eliminada', 'success')
    return redirect(url_for('cuadrillas.index'))
