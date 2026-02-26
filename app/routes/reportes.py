from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Producto, Cuadrilla, Salida, Entrada, Rendicion
from app import db
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/')
@login_required
def index():
    compras = Producto.query.filter(
        Producto.activo == True,
        Producto.stock_bodega <= Producto.stock_min
    ).order_by(Producto.stock_bodega).all()

    from app.models import RendicionItem
    from sqlalchemy import func
    top_productos = db.session.query(
        Producto.descripcion,
        func.sum(RendicionItem.cantidad_usada).label('total')
    ).join(RendicionItem).group_by(Producto.id)\
     .order_by(func.sum(RendicionItem.cantidad_usada).desc()).limit(10).all()

    now = datetime.now()
    return render_template('reportes.html',
        compras           = compras,
        top_productos     = top_productos,
        total_entradas    = Entrada.query.count(),
        total_salidas     = Salida.query.count(),
        total_rendiciones = Rendicion.query.count(),
        mes_actual        = now.month,
        año_actual        = now.year,
    )
