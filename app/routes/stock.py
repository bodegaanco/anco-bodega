from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Producto, Entrada
from app import db

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/')
@login_required
def index():
    categoria = request.args.get('categoria', '')
    estado    = request.args.get('estado', '')
    buscar    = request.args.get('buscar', '')

    q = Producto.query.filter_by(activo=True)
    if categoria:
        q = q.filter_by(categoria=categoria)
    if buscar:
        q = q.filter(Producto.descripcion.ilike(f'%{buscar}%'))
    if estado == 'alerta':
        q = q.filter(Producto.stock_bodega <= Producto.stock_min)

    productos   = q.order_by(Producto.categoria, Producto.descripcion).all()
    categorias  = db.session.query(Producto.categoria).distinct().all()
    return render_template('stock.html', productos=productos, categorias=categorias)

@stock_bp.route('/entrada', methods=['GET','POST'])
@login_required
def entrada():
    if request.method == 'POST':
        productos_ids  = request.form.getlist('producto_id[]')
        cantidades     = request.form.getlist('cantidad[]')
        for pid, cant in zip(productos_ids, cantidades):
            if pid and cant and int(cant) > 0:
                producto = Producto.query.get(pid)
                if producto:
                    antes = producto.stock_bodega
                    producto.stock_bodega += int(cant)
                    entrada = Entrada(
                        producto_id   = producto.id,
                        cantidad      = int(cant),
                        stock_antes   = antes,
                        stock_despues = producto.stock_bodega
                    )
                    db.session.add(entrada)
        db.session.commit()
        flash('✅ Entrada registrada correctamente', 'success')
        return redirect(url_for('stock.index'))
    productos = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return render_template('entrada.html', productos=productos)

@stock_bp.route('/ajuste/<int:id>', methods=['POST'])
@login_required
def ajuste(id):
    producto    = Producto.query.get_or_404(id)
    nuevo_stock = int(request.form.get('nuevo_stock', 0))
    producto.stock_bodega = nuevo_stock
    db.session.commit()
    flash(f'✅ Stock de {producto.descripcion} ajustado a {nuevo_stock}', 'success')
    return redirect(url_for('stock.index'))

@stock_bp.route('/api/productos')
@login_required
def api_productos():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all()
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo,
        'descripcion': p.descripcion,
        'unidad': p.unidad,
        'stock_bodega': p.stock_bodega
    } for p in productos])


# ── EDITAR PRODUCTO (descripcion, categoria, unidad, stock_min) ──────────────
@stock_bp.route('/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    producto             = Producto.query.get_or_404(id)
    producto.descripcion = request.form.get('descripcion', producto.descripcion).strip()
    producto.categoria   = request.form.get('categoria', producto.categoria).strip()
    producto.unidad      = request.form.get('unidad', producto.unidad).strip()
    s = request.form.get('stock_min', '0').strip()
    producto.stock_min   = int(s) if s.isdigit() else 0
    db.session.commit()
    flash('✅ Producto actualizado correctamente', 'success')
    return redirect(url_for('stock.index'))


@stock_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
def toggle(id):
    p        = Producto.query.get_or_404(id)
    p.activo = not p.activo
    db.session.commit()
    flash(f'✅ Producto {"activado" if p.activo else "desactivado"}', 'success')
    return redirect(url_for('stock.index'))
