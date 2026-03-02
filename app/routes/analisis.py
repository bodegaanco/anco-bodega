from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import Producto, Cuadrilla, Rendicion, RendicionItem, Salida
from app import db
from sqlalchemy import func
from datetime import datetime, date, timedelta
import json

analisis_bp = Blueprint('analisis', __name__, url_prefix='/analisis')

@analisis_bp.route('/')
@login_required
def index():
    hoy         = date.today()
    desde_str   = request.args.get('desde', (hoy - timedelta(days=30)).strftime('%Y-%m-%d'))
    hasta_str   = request.args.get('hasta', hoy.strftime('%Y-%m-%d'))
    producto_id = request.args.get('producto_id', '')

    desde_dt = datetime.strptime(desde_str, '%Y-%m-%d')
    hasta_dt = datetime.strptime(hasta_str, '%Y-%m-%d').replace(hour=23, minute=59)

    top_productos = db.session.query(
        Producto.descripcion, Producto.unidad,
        func.sum(RendicionItem.cantidad_usada).label('total')
    ).join(RendicionItem).join(Rendicion)\
     .filter(Rendicion.creado_en.between(desde_dt, hasta_dt))\
     .group_by(Producto.id)\
     .order_by(func.sum(RendicionItem.cantidad_usada).desc()).limit(10).all()

    consumo_cuadrilla = db.session.query(
        Cuadrilla.nombre,
        func.sum(RendicionItem.cantidad_usada).label('total')
    ).join(Rendicion, Rendicion.cuadrilla_id == Cuadrilla.id)\
     .join(RendicionItem, RendicionItem.rendicion_id == Rendicion.id)\
     .filter(Rendicion.creado_en.between(desde_dt, hasta_dt))\
     .group_by(Cuadrilla.id)\
     .order_by(func.sum(RendicionItem.cantidad_usada).desc()).all()

    meses_labels, meses_data = [], []
    meses_nombres = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    for i in range(5, -1, -1):
        ref = date(hoy.year, hoy.month, 1) - timedelta(days=i*30)
        ini = date(ref.year, ref.month, 1)
        fin = date(ref.year, ref.month+1, 1) - timedelta(days=1) if ref.month < 12 else date(ref.year+1,1,1) - timedelta(days=1)
        total = db.session.query(func.sum(RendicionItem.cantidad_usada))\
            .join(Rendicion).filter(func.date(Rendicion.creado_en).between(ini, fin)).scalar() or 0
        meses_labels.append(f"{meses_nombres[ini.month]} {ini.year}")
        meses_data.append(int(total))

    detalle_producto, producto_sel = [], None
    if producto_id:
        producto_sel = Producto.query.get(producto_id)
        detalle_producto = db.session.query(
            Cuadrilla.nombre,
            func.sum(RendicionItem.cantidad_usada).label('total'),
            func.count(Rendicion.id).label('num_ot')
        ).join(Rendicion, Rendicion.cuadrilla_id == Cuadrilla.id)\
         .join(RendicionItem, RendicionItem.rendicion_id == Rendicion.id)\
         .filter(RendicionItem.producto_id == producto_id,
                 Rendicion.creado_en.between(desde_dt, hasta_dt))\
         .group_by(Cuadrilla.id)\
         .order_by(func.sum(RendicionItem.cantidad_usada).desc()).all()

    total_items   = db.session.query(func.sum(RendicionItem.cantidad_usada))\
        .join(Rendicion).filter(Rendicion.creado_en.between(desde_dt, hasta_dt)).scalar() or 0
    total_ots     = Rendicion.query.filter(Rendicion.creado_en.between(desde_dt, hasta_dt)).count()
    total_salidas = Salida.query.filter(Salida.creado_en.between(desde_dt, hasta_dt)).count()

    return render_template('analisis.html',
        desde_str=desde_str, hasta_str=hasta_str,
        top_productos=top_productos,
        consumo_cuadrilla=consumo_cuadrilla,
        meses_labels=json.dumps(meses_labels),
        meses_data=json.dumps(meses_data),
        detalle_producto=detalle_producto,
        producto_sel=producto_sel,
        producto_id=producto_id,
        productos_lista=Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all(),
        total_items=int(total_items), total_ots=total_ots, total_salidas=total_salidas,
        dias_periodo=(hasta_dt.date() - desde_dt.date()).days,
    )