from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import Producto, Cuadrilla, Rendicion, RendicionItem, Salida, SalidaItem, StockCuadrilla, ComparacionOTItem
from app import db
from sqlalchemy import func
from datetime import datetime, date, timedelta
import json

analisis_bp = Blueprint('analisis', __name__, url_prefix='/analisis')

@analisis_bp.route('/')
@login_required
def index():
    hoy       = date.today()
    desde_str = request.args.get('desde', (hoy - timedelta(days=30)).strftime('%Y-%m-%d'))
    hasta_str = request.args.get('hasta', hoy.strftime('%Y-%m-%d'))
    producto_id = request.args.get('producto_id', '')

    desde_dt = datetime.strptime(desde_str, '%Y-%m-%d')
    hasta_dt = datetime.strptime(hasta_str, '%Y-%m-%d').replace(hour=23, minute=59)

    meses_nombres = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

    # ── KPIs ──────────────────────────────────────────────────────
    total_salidas  = Salida.query.filter(
        Salida.creado_en.between(desde_dt, hasta_dt),
        Salida.anulada == False,
        Salida.tipo == 'salida'
    ).count()
    total_ots      = Rendicion.query.filter(Rendicion.creado_en.between(desde_dt, hasta_dt), Rendicion.anulada == False).count()
    total_entregado = db.session.query(func.sum(SalidaItem.cantidad))\
        .join(Salida).filter(Salida.creado_en.between(desde_dt, hasta_dt), Salida.anulada == False, Salida.tipo == 'salida').scalar() or 0
    total_utilizado = db.session.query(func.sum(RendicionItem.cantidad_usada))\
        .join(Rendicion).filter(Rendicion.creado_en.between(desde_dt, hasta_dt), Rendicion.anulada == False).scalar() or 0

    # ── 1. TOP 10 PRODUCTOS MÁS ENTREGADOS (Salidas) ─────────────
    top_entregados = db.session.query(
        Producto.descripcion, Producto.unidad,
        func.sum(SalidaItem.cantidad).label('total')
    ).join(SalidaItem).join(Salida)\
     .filter(Salida.creado_en.between(desde_dt, hasta_dt), Salida.anulada == False, Salida.tipo == 'salida')\
     .group_by(Producto.id)\
     .order_by(func.sum(SalidaItem.cantidad).desc()).limit(10).all()

    # ── 2. TOP 10 PRODUCTOS MÁS USADOS (OT Rendiciones) ──────────
    top_usados = db.session.query(
        Producto.descripcion, Producto.unidad,
        func.sum(RendicionItem.cantidad_usada).label('total')
    ).join(RendicionItem).join(Rendicion)\
     .filter(Rendicion.creado_en.between(desde_dt, hasta_dt), Rendicion.anulada == False)\
     .group_by(Producto.id)\
     .order_by(func.sum(RendicionItem.cantidad_usada).desc()).limit(10).all()

    # ── 3. CONSUMO POR CUADRILLA (Salidas) ───────────────────────
    consumo_cuadrilla = db.session.query(
        Cuadrilla.nombre,
        func.sum(SalidaItem.cantidad).label('entregado'),
        func.count(func.distinct(Salida.id)).label('num_salidas')
    ).join(Salida, Salida.cuadrilla_id == Cuadrilla.id)\
     .join(SalidaItem, SalidaItem.salida_id == Salida.id)\
     .filter(Salida.creado_en.between(desde_dt, hasta_dt), Salida.anulada == False, Salida.tipo == 'salida')\
     .group_by(Cuadrilla.id)\
     .order_by(func.sum(SalidaItem.cantidad).desc()).all()

    # ── 4. EFICIENCIA DE RENDICIÓN por cuadrilla ─────────────────
    cuadrillas_all = Cuadrilla.query.filter_by(activa=True).all()
    eficiencia = []
    for c in cuadrillas_all:
        n_salidas = Salida.query.filter(
            Salida.cuadrilla_id == c.id,
            Salida.creado_en.between(desde_dt, hasta_dt),
            Salida.anulada == False, Salida.tipo == 'salida'
        ).count()
        n_rendidas = db.session.query(func.count(func.distinct(Rendicion.id)))\
            .filter(Rendicion.cuadrilla_id == c.id,
                    Rendicion.creado_en.between(desde_dt, hasta_dt),
                    Rendicion.anulada == False).scalar() or 0
        if n_salidas > 0:
            pct = round(min(n_rendidas / n_salidas * 100, 100), 1)
            eficiencia.append({'nombre': c.nombre, 'salidas': n_salidas, 'rendidas': n_rendidas, 'pct': pct})

    eficiencia.sort(key=lambda x: x['pct'])

    # ── 5. EVOLUCIÓN MENSUAL (Salidas) ────────────────────────────
    meses_labels, meses_entregado, meses_usado = [], [], []
    for i in range(5, -1, -1):
        ref = date(hoy.year, hoy.month, 1) - timedelta(days=i*30)
        ini = date(ref.year, ref.month, 1)
        fin = date(ref.year, ref.month+1, 1) - timedelta(days=1) if ref.month < 12 else date(ref.year+1,1,1) - timedelta(days=1)
        ent = db.session.query(func.sum(SalidaItem.cantidad))\
            .join(Salida).filter(func.date(Salida.creado_en).between(ini, fin), Salida.anulada == False, Salida.tipo == 'salida').scalar() or 0
        uso = db.session.query(func.sum(RendicionItem.cantidad_usada))\
            .join(Rendicion).filter(func.date(Rendicion.creado_en).between(ini, fin), Rendicion.anulada == False).scalar() or 0
        meses_labels.append(f"{meses_nombres[ini.month]} {ini.year}")
        meses_entregado.append(round(float(ent), 2))
        meses_usado.append(round(float(uso), 2))

    # ── 6. DIFERENCIAS OT (pérdidas por cuadrilla) ───────────────
    dif_ot = db.session.query(
        Cuadrilla.nombre,
        func.sum(ComparacionOTItem.diferencia).label('dif_total'),
        func.count(ComparacionOTItem.id).label('n_items')
    ).join(Rendicion, Rendicion.id == ComparacionOTItem.rendicion_id)\
     .join(Cuadrilla, Cuadrilla.id == Rendicion.cuadrilla_id)\
     .filter(Rendicion.creado_en.between(desde_dt, hasta_dt))\
     .group_by(Cuadrilla.id)\
     .order_by(func.sum(ComparacionOTItem.diferencia)).all()

    # ── 7. ESTADO CUADRILLAS (stock teórico actual) ───────────────
    estado_cuadrillas = []
    for c in cuadrillas_all:
        stocks = StockCuadrilla.query.filter_by(cuadrilla_id=c.id).all()
        total_stock = sum(s.cantidad for s in stocks if s.cantidad > 0)
        n_productos = len([s for s in stocks if s.cantidad > 0])
        ultima_salida = Salida.query.filter_by(cuadrilla_id=c.id, anulada=False)\
            .order_by(Salida.creado_en.desc()).first()
        ultima_ot = Rendicion.query.filter_by(cuadrilla_id=c.id, anulada=False)\
            .order_by(Rendicion.creado_en.desc()).first()
        ots_con_dif = Rendicion.query.filter_by(cuadrilla_id=c.id, estado='diferencia', anulada=False).count()
        estado_cuadrillas.append({
            'nombre': c.nombre,
            'total_stock': round(total_stock, 2),
            'n_productos': n_productos,
            'ultima_salida': ultima_salida.creado_en.strftime('%d/%m/%Y') if ultima_salida else '—',
            'ultima_ot': ultima_ot.creado_en.strftime('%d/%m/%Y') if ultima_ot else '—',
            'ots_con_dif': ots_con_dif,
        })

    # ── DETALLE PRODUCTO ──────────────────────────────────────────
    detalle_producto, producto_sel = [], None
    if producto_id:
        producto_sel = Producto.query.get(producto_id)
        detalle_producto = db.session.query(
            Cuadrilla.nombre,
            func.sum(SalidaItem.cantidad).label('entregado'),
            func.count(func.distinct(Salida.id)).label('num_salidas')
        ).join(Salida, Salida.cuadrilla_id == Cuadrilla.id)\
         .join(SalidaItem, SalidaItem.salida_id == Salida.id)\
         .filter(SalidaItem.producto_id == producto_id,
                 Salida.creado_en.between(desde_dt, hasta_dt),
                 Salida.anulada == False)\
         .group_by(Cuadrilla.id)\
         .order_by(func.sum(SalidaItem.cantidad).desc()).all()

    from app.models import Inventario
    inventarios_lista = Inventario.query.order_by(Inventario.creado_en.desc()).limit(50).all()

    return render_template('analisis.html',
        desde_str=desde_str, hasta_str=hasta_str,
        total_salidas=total_salidas, total_ots=total_ots,
        total_entregado=round(float(total_entregado), 2),
        total_utilizado=round(float(total_utilizado), 2),
        top_entregados=top_entregados,
        top_usados=top_usados,
        consumo_cuadrilla=consumo_cuadrilla,
        eficiencia=eficiencia,
        meses_labels=json.dumps(meses_labels),
        meses_entregado=json.dumps(meses_entregado),
        meses_usado=json.dumps(meses_usado),
        dif_ot=dif_ot,
        estado_cuadrillas=estado_cuadrillas,
        detalle_producto=detalle_producto,
        producto_sel=producto_sel,
        producto_id=producto_id,
        productos_lista=Producto.query.filter_by(activo=True).order_by(Producto.descripcion).all(),
        dias_periodo=(hasta_dt.date() - desde_dt.date()).days,
        cuadrillas_lista=cuadrillas_all,
        inventarios_lista=inventarios_lista,
    )
