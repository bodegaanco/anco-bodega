from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Producto, Cuadrilla, StockCuadrilla, Salida, Entrada
from app import db
from datetime import datetime, date

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # KPIs
    total_productos  = Producto.query.filter_by(activo=True).count()
    criticos         = Producto.query.filter(
                           Producto.activo == True,
                           Producto.stock_bodega <= Producto.stock_min
                       ).count()
    cuadrillas_activas = Cuadrilla.query.filter_by(activa=True).count()

    # Salidas de hoy
    hoy = date.today()
    salidas_hoy = Salida.query.filter(
        db.func.date(Salida.creado_en) == hoy
    ).count()

    # Alertas de stock (bodega + cuadrillas)
    alertas_bodega = Producto.query.filter(
        Producto.activo == True,
        Producto.stock_bodega <= Producto.stock_min
    ).order_by(Producto.stock_bodega).limit(10).all()

    alertas_cuadrilla = StockCuadrilla.query.filter(
        StockCuadrilla.cantidad <= StockCuadrilla.stock_min
    ).limit(5).all()

    # Cuadrillas con resumen
    cuadrillas = Cuadrilla.query.filter_by(activa=True).all()

    # Últimos movimientos (entradas + salidas mezclados)
    ultimas_entradas = Entrada.query.order_by(Entrada.creado_en.desc()).limit(5).all()
    ultimas_salidas  = Salida.query.order_by(Salida.creado_en.desc()).limit(5).all()

    return render_template('dashboard.html',
        total_productos    = total_productos,
        criticos           = criticos,
        cuadrillas_activas = cuadrillas_activas,
        salidas_hoy        = salidas_hoy,
        alertas_bodega     = alertas_bodega,
        alertas_cuadrilla  = alertas_cuadrilla,
        cuadrillas         = cuadrillas,
        ultimas_entradas   = ultimas_entradas,
        ultimas_salidas    = ultimas_salidas,
    )
