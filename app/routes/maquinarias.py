from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Maquinaria, PrestamoMaquinaria, Cuadrilla
from app import db
from datetime import datetime

maquinarias_bp = Blueprint('maquinarias', __name__, url_prefix='/maquinarias')

@maquinarias_bp.route('/')
@login_required
def index():
    maquinarias = Maquinaria.query.filter_by(activa=True).order_by(Maquinaria.nombre).all()
    cuadrillas  = Cuadrilla.query.filter_by(activa=True).all()
    # Préstamos activos (no devueltos)
    activos = PrestamoMaquinaria.query.filter_by(devuelta=False)\
                .order_by(PrestamoMaquinaria.fecha_entrega.desc()).all()
    # Historial completo
    historial = PrestamoMaquinaria.query.filter_by(devuelta=True)\
                .order_by(PrestamoMaquinaria.fecha_devol.desc()).limit(30).all()
    return render_template('maquinarias.html',
        maquinarias=maquinarias, cuadrillas=cuadrillas,
        activos=activos, historial=historial,
        now=datetime.utcnow())

@maquinarias_bp.route('/nueva', methods=['POST'])
@login_required
def nueva():
    nombre      = request.form.get('nombre')
    codigo      = request.form.get('codigo', '')
    descripcion = request.form.get('descripcion', '')
    if nombre:
        m = Maquinaria(nombre=nombre, codigo=codigo, descripcion=descripcion)
        db.session.add(m)
        db.session.commit()
        flash(f'✅ Maquinaria "{nombre}" registrada', 'success')
    return redirect(url_for('maquinarias.index'))

@maquinarias_bp.route('/prestar', methods=['POST'])
@login_required
def prestar():
    maquinaria_id = request.form.get('maquinaria_id')
    cuadrilla_id  = request.form.get('cuadrilla_id')
    notas         = request.form.get('notas', '')

    maquinaria = Maquinaria.query.get_or_404(maquinaria_id)

    # Verificar que no esté ya prestada
    if maquinaria.en_uso():
        flash(f'⚠️ {maquinaria.nombre} ya está en uso por otra cuadrilla', 'error')
        return redirect(url_for('maquinarias.index'))

    prestamo = PrestamoMaquinaria(
        maquinaria_id = maquinaria_id,
        cuadrilla_id  = cuadrilla_id,
        notas         = notas,
        usuario_id    = current_user.id
    )
    db.session.add(prestamo)
    db.session.commit()
    flash(f'✅ {maquinaria.nombre} entregada correctamente', 'success')
    return redirect(url_for('maquinarias.index'))

@maquinarias_bp.route('/devolver/<int:prestamo_id>', methods=['POST'])
@login_required
def devolver(prestamo_id):
    prestamo = PrestamoMaquinaria.query.get_or_404(prestamo_id)
    prestamo.devuelta   = True
    prestamo.fecha_devol = datetime.utcnow()
    db.session.commit()
    flash(f'✅ {prestamo.maquinaria.nombre} marcada como devuelta', 'success')
    return redirect(url_for('maquinarias.index'))

@maquinarias_bp.route('/eliminar/<int:prestamo_id>', methods=['POST'])
@login_required
def eliminar_prestamo(prestamo_id):
    prestamo = PrestamoMaquinaria.query.get_or_404(prestamo_id)
    nombre   = prestamo.maquinaria.nombre
    db.session.delete(prestamo)
    db.session.commit()
    flash(f'🗑️ Préstamo de {nombre} eliminado', 'success')
    return redirect(url_for('maquinarias.index'))

@maquinarias_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
@login_required
def cambiar_estado(id):
    m      = Maquinaria.query.get_or_404(id)
    estado = request.form.get('estado')
    estados_validos = ['disponible', 'mantencion', 'fuera_servicio']
    if estado in estados_validos:
        m.estado = estado
        db.session.commit()
        nombres = {'disponible':'Disponible','mantencion':'En Mantención','fuera_servicio':'Fuera de Servicio'}
        flash(f'✅ {m.nombre} marcada como {nombres[estado]}', 'success')
    return redirect(url_for('maquinarias.index'))

@maquinarias_bp.route('/desactivar/<int:id>', methods=['POST'])
@login_required
def desactivar(id):
    m = Maquinaria.query.get_or_404(id)
    m.activa = False
    db.session.commit()
    flash(f'Maquinaria {m.nombre} desactivada', 'success')
    return redirect(url_for('maquinarias.index'))
