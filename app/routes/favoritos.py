from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Producto, ProductoFavorito
from app import db

favoritos_bp = Blueprint('favoritos', __name__, url_prefix='/favoritos')

@favoritos_bp.route('/')
@login_required
def index():
    favoritos  = ProductoFavorito.query.join(Producto).order_by(Producto.descripcion).all()
    productos  = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    fav_ids    = {f.producto_id for f in favoritos}
    return render_template('favoritos.html', favoritos=favoritos, productos=productos, fav_ids=fav_ids)

@favoritos_bp.route('/agregar/<int:producto_id>', methods=['POST'])
@login_required
def agregar(producto_id):
    if not ProductoFavorito.query.filter_by(producto_id=producto_id).first():
        db.session.add(ProductoFavorito(producto_id=producto_id))
        db.session.commit()
    return redirect(url_for('favoritos.index'))

@favoritos_bp.route('/quitar/<int:producto_id>', methods=['POST'])
@login_required
def quitar(producto_id):
    fav = ProductoFavorito.query.filter_by(producto_id=producto_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return redirect(url_for('favoritos.index'))

@favoritos_bp.route('/api')
@login_required
def api():
    """Retorna lista de favoritos como JSON para usar en salidas/OT"""
    favs = ProductoFavorito.query.join(Producto).order_by(Producto.descripcion).all()
    return jsonify([{
        'id':          f.producto.id,
        'descripcion': f.producto.descripcion,
        'codigo':      f.producto.codigo,
        'unidad':      f.producto.unidad,
        'stock':       f.producto.stock_bodega,
    } for f in favs])
