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
        db.func.date(Salida.creado_en) == hoy,
        Salida.tipo == 'salida'
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
    ultimas_salidas  = Salida.query.filter(Salida.tipo == 'salida').order_by(Salida.creado_en.desc()).limit(5).all()

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


@main_bp.route('/run-migrate-float')
@login_required
def run_migrate_float():
    from sqlalchemy import text
    from app import db
    resultados = []
    queries = [
        ("productos.stock_bodega", "ALTER TABLE productos ALTER COLUMN stock_bodega TYPE FLOAT USING stock_bodega::float"),
        ("stock_cuadrilla.cantidad", "ALTER TABLE stock_cuadrilla ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float"),
        ("salida_items.cantidad", "ALTER TABLE salida_items ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float"),
        ("rendicion_items.cantidad_usada", "ALTER TABLE rendicion_items ALTER COLUMN cantidad_usada TYPE FLOAT USING cantidad_usada::float"),
        ("inventario_items.cantidad_real", "ALTER TABLE inventario_items ALTER COLUMN cantidad_real TYPE FLOAT USING cantidad_real::float"),
        ("inventario_items.diferencia", "ALTER TABLE inventario_items ALTER COLUMN diferencia TYPE FLOAT USING diferencia::float"),
        ("inventario_items.stock_sistema", "ALTER TABLE inventario_items ALTER COLUMN stock_sistema TYPE FLOAT USING stock_sistema::float"),
        ("inventario_items.stock_real", "ALTER TABLE inventario_items ALTER COLUMN stock_real TYPE FLOAT USING stock_real::float"),
        ("salidas.tipo", "ALTER TABLE salidas ADD COLUMN IF NOT EXISTS tipo VARCHAR(30) DEFAULT 'salida'"),
        ("rendiciones.notas_revision", "ALTER TABLE rendiciones ADD COLUMN IF NOT EXISTS notas_revision VARCHAR(500)"),
        ("comparacion_ot_items", """CREATE TABLE IF NOT EXISTS comparacion_ot_items (
            id SERIAL PRIMARY KEY,
            rendicion_id INTEGER NOT NULL REFERENCES rendiciones(id),
            producto_id INTEGER NOT NULL REFERENCES productos(id),
            cantidad_anco FLOAT NOT NULL,
            cantidad_otro FLOAT DEFAULT 0,
            diferencia FLOAT DEFAULT 0
        )"""),
    ]
    for nombre, sql in queries:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            resultados.append(f"✅ {nombre}")
        except Exception as e:
            db.session.rollback()
            resultados.append(f"⚠️ {nombre}: {str(e)[:80]}")

    return "<h2>Migración Float</h2><pre>" + "\n".join(resultados) + "</pre><br><a href='/'>Volver al sistema</a>"

@main_bp.route('/setup-inicial-2026')
def setup_inicial():
    """Ruta temporal SIN login para crear tablas y usuarios en BD nueva"""
    from app.models import Usuario
    from werkzeug.security import generate_password_hash

    resultado = []
    try:
        db.create_all()
        resultado.append("✅ Tablas creadas correctamente")
    except Exception as e:
        resultado.append(f"⚠️ Error creando tablas: {e}")
        return "<pre>" + "\n".join(resultado) + "</pre>"

    usuarios_nuevos = [
        ('Bodeguero',         'bodega.anco@gmail.com',              'anco2025',  'bodeguero'),
        ('Francisco Muñoz',   'franciscomunozg2002@gmail.com',      'anco2025',  'administrador'),
        ('Supervisor 1',      'supervisor1.anco@gmail.com',         'anco2025',  'supervisor'),
        ('Supervisor 2',      'supervisor2.anco@gmail.com',         'anco2025',  'supervisor'),
        ('Supervisor 3',      'supervisor3.anco@gmail.com',         'anco2025',  'supervisor'),
        ('Administrador',     'admin.anco@gmail.com',               'anco2025',  'administrador'),
    ]
    for nombre, email, pw, rol in usuarios_nuevos:
        try:
            if not Usuario.query.filter_by(email=email).first():
                db.session.add(Usuario(
                    nombre=nombre, email=email,
                    password=generate_password_hash(pw), rol=rol
                ))
                db.session.commit()
                resultado.append(f"✅ Creado: {email} / {pw} ({rol})")
            else:
                resultado.append(f"ℹ️ Ya existe: {email}")
        except Exception as e:
            db.session.rollback()
            resultado.append(f"⚠️ Error con {email}: {e}")

    return "<h2>Setup Inicial</h2><pre>" + "\n".join(resultado) + "</pre><br><a href='/'>Ir al login</a>"


@main_bp.route('/cargar-productos-2026')
def cargar_productos_inicial():
    """Ruta temporal SIN login para cargar catalogo de 138 productos"""
    from app.models import Producto

    productos_data = [
        ('34000712', 'ABRAZADERA ASB-CEM DN75MM', 'C/U'),
        ('30000070', 'GOLILLA VAINA P/MEDIDOR 13MM', 'C/U'),
        ('30000072', 'TUERCA ENTRADA 15MM', 'C/U'),
        ('30000077', 'TUERCA SALIDA ROSCA 7/8 13MM', 'C/U'),
        ('30000080', 'VAINA HILADA MEDIDOR 13MM', 'C/U'),
        ('34000404', 'UNION UNIV DN 200MM', 'C/U'),
        ('34000494', 'CODO REDUC BRONCE SS 38x32MM', 'C/U'),
        ('34000678', 'CAÑERIA PVC COLECTOR T2 DN180MM', 'M'),
        ('34000717', 'ABRAZADERA REPAR 119-130 L300MM', 'C/U'),
        ('34000726', 'ABRAZADERA REPAR 88-98 L300MM', 'C/U'),
        ('34000728', 'ABRAZADERA REPAR 95-105 L300MM', 'C/U'),
        ('34000742', 'ADAPTADOR PVC 110X100MM', 'C/U'),
        ('34000743', 'ADAPTADOR PVC 125X125MM', 'C/U'),
        ('34000744', 'ADAPTADOR PVC 140X125MM', 'C/U'),
        ('34000745', 'ADAPTADOR PVC 160X150MM', 'C/U'),
        ('34000746', 'ADAPTADOR PVC 200X200MM', 'C/U'),
        ('34000751', 'ADAPTADOR PVC 75X75MM', 'C/U'),
        ('34000752', 'ADAPTADOR PVC 90X75MM', 'C/U'),
        ('34000788', 'COLLAR TOMA CARGA METALICO 3/4', 'C/U'),
        ('34000789', 'CAÑERIA COBRE TIPO L DN13MM', 'M'),
        ('34000790', 'CAÑERIA COBRE TIPO L DN19MM', 'M'),
        ('34000791', 'CAÑERIA COBRE TIPO L DN25MM', 'M'),
        ('34000792', 'CAÑERIA COBRE TIPO L DN32MM', 'M'),
        ('34000793', 'CAÑERIA COBRE TIPO L DN38MM', 'M'),
        ('34000794', 'CAÑERIA COBRE TIPO L DN50MM', 'M'),
        ('34000799', 'CAÑERIA HDPE PE100 PN10 DN32MM', 'M'),
        ('34000803', 'CAÑERIA HDPE PE100 PN10 DN25MM', 'M'),
        ('34000806', 'CAÑERIA PVC CLASE10 DN110MM', 'M'),
        ('34000807', 'CAÑERIA PVC CLASE10 DN125MM', 'M'),
        ('34000808', 'CAÑERIA PVC CLASE10 DN140MM', 'M'),
        ('34000809', 'CAÑERIA PVC CLASE10 DN160MM', 'M'),
        ('34000811', 'CAÑERIA PVC CLASE10 DN200MM', 'M'),
        ('34000820', 'CAÑERIA PVC CLASE10 DN63MM', 'M'),
        ('34000821', 'CAÑERIA PVC CLASE10 DN75MM', 'M'),
        ('34000822', 'CAÑERIA PVC CLASE10 DN90MM', 'M'),
        ('34000825', 'CINCHA INOX DN100 110-130MM', 'C/U'),
        ('34000826', 'CINCHA INOX DN125 130-150MM', 'C/U'),
        ('34000827', 'CINCHA INOX DN150 160-180MM', 'C/U'),
        ('34000834', 'CINCHA INOX DN60 70-90MM', 'C/U'),
        ('34000835', 'CINCHA INOX DN80 90-110MM', 'C/U'),
        ('34000837', 'CODO 90 HDPE 32X1PULG', 'C/U'),
        ('34000840', 'CODO REDUC BRONCE SS 19x13MM', 'C/U'),
        ('34000844', 'CODO BRONCE HE-S DN13MM', 'C/U'),
        ('34000845', 'CODO BRONCE HE-S DN19MM', 'C/U'),
        ('34000846', 'CODO BRONCE HE-S DN25MM', 'C/U'),
        ('34000848', 'CODO BRONCE HE-S DN38MM', 'C/U'),
        ('34000850', 'CODO BRONCE HI-HE DN13MM', 'C/U'),
        ('34000851', 'CODO BRONCE HI-HE DN19MM', 'C/U'),
        ('34000852', 'CODO BRONCE HI-HE DN25MM', 'C/U'),
        ('34000854', 'CODO BRONCE HI-HE DN38MM', 'C/U'),
        ('34000862', 'CODO BRONCE HI-S DN13MM', 'C/U'),
        ('34000863', 'CODO BRONCE HI-S DN19MM', 'C/U'),
        ('34000864', 'CODO BRONCE HI-S DN25MM', 'C/U'),
        ('34000865', 'CODO BRONCE HI-S DN32MM', 'C/U'),
        ('34000866', 'CODO BRONCE HI-S DN38MM', 'C/U'),
        ('34000868', 'CODO BRONCE SS DN13MM', 'C/U'),
        ('34000869', 'CODO BRONCE SS DN19MM', 'C/U'),
        ('34000870', 'CODO BRONCE SS DN25MM', 'C/U'),
        ('34000871', 'CODO BRONCE SS DN32MM', 'C/U'),
        ('34000872', 'CODO BRONCE SS DN38MM', 'C/U'),
        ('34000873', 'CODO BRONCE SS DN50MM', 'C/U'),
        ('34000918', 'COPLA BRONCE SS DN13MM', 'C/U'),
        ('34000919', 'COPLA BRONCE SS DN19MM', 'C/U'),
        ('34000920', 'COPLA BRONCE SS DN25MM', 'C/U'),
        ('34000921', 'COPLA BRONCE SS DN32MM', 'C/U'),
        ('34000922', 'COPLA BRONCE SS DN38MM', 'C/U'),
        ('34000923', 'COPLA BRONCE SS DN50MM', 'C/U'),
        ('34000929', 'COPLA PVC REPAR ANGER 110MM', 'C/U'),
        ('34000930', 'COPLA PVC REPAR ANGER 125MM', 'C/U'),
        ('34000931', 'COPLA PVC REPAR ANGER 140MM', 'C/U'),
        ('34000932', 'COPLA PVC REPAR ANGER 160MM', 'C/U'),
        ('34000933', 'COPLA PVC REPAR ANGER 200MM', 'C/U'),
        ('34000937', 'COPLA PVC REPAR ANGER 63MM', 'C/U'),
        ('34000938', 'COPLA PVC REPAR ANGER 75MM', 'C/U'),
        ('34000939', 'COPLA PVC REPAR ANGER 90MM', 'C/U'),
        ('34000940', 'COPLA REDUC BRONCE 19X13MM', 'C/U'),
        ('34000941', 'COPLA REDUC BRONCE 25X19MM', 'C/U'),
        ('34000944', 'COPLA REDUC BRONCE 38X25MM', 'C/U'),
        ('34000947', 'COPLA TRANS HDPE-CU 25MMX3/4', 'C/U'),
        ('34000948', 'COPLA TRANS HDPE-CU 32MMX1', 'C/U'),
        ('34000969', 'CURVA PVC ANGER-ESP 1/4X110MM', 'C/U'),
        ('34000975', 'CURVA PVC ANGER-ESP 1/8X110MM', 'C/U'),
        ('34001013', 'GUARDA LLAVE FE FDO P/VALVULA', 'C/U'),
        ('34001019', 'LLAVE COLLAR BRONCE HE-HE 19MM', 'C/U'),
        ('34001020', 'LLAVE COLLAR BRONCE HE-HE 25MM', 'C/U'),
        ('34001022', 'LLAVE COLLAR BRONCE HE-HE 38MM', 'C/U'),
        ('34001024', 'LLAVE PASO BOLA BRONCE HI-HI 13MM', 'C/U'),
        ('34001025', 'LLAVE PASO BOLA BRONCE HI-HI 19MM', 'C/U'),
        ('34001026', 'LLAVE PASO BOLA BRONCE HI-HI 25MM', 'C/U'),
        ('34001031', 'LLAVE PASO BRONCE SS DN13MM', 'C/U'),
        ('34001032', 'LLAVE PASO BRONCE SS DN19MM', 'C/U'),
        ('34001056', 'REDUCCION PVC 110X90MM', 'C/U'),
        ('34001124', 'TAPON PVC ANGER 110MM', 'C/U'),
        ('34001125', 'TAPON PVC ANGER 125MM', 'C/U'),
        ('34001129', 'TAPON PVC ANGER 90MM', 'C/U'),
        ('34001131', 'TEE BRONCE SSS 13X13MM', 'C/U'),
        ('34001133', 'TEE BRONCE SSS 19X19MM', 'C/U'),
        ('34001165', 'TERMINAL BRONCE HE-S 13MM', 'C/U'),
        ('34001166', 'TERMINAL BRONCE HE-S 19MM', 'C/U'),
        ('34001167', 'TERMINAL BRONCE HE-S 25MM', 'C/U'),
        ('34001168', 'TERMINAL BRONCE HE-S 32MM', 'C/U'),
        ('34001169', 'TERMINAL BRONCE HE-S 38MM', 'C/U'),
        ('34001170', 'TERMINAL BRONCE HE-S 50MM', 'C/U'),
        ('34001172', 'TERMINAL BRONCE HI-S 13MM', 'C/U'),
        ('34001173', 'TERMINAL BRONCE HI-S 19MM', 'C/U'),
        ('34001174', 'TERMINAL BRONCE HI-S 25MM', 'C/U'),
        ('34001175', 'TERMINAL BRONCE HI-S 32MM', 'C/U'),
        ('34001176', 'TERMINAL BRONCE HI-S 38MM', 'C/U'),
        ('34001177', 'TERMINAL BRONCE HI-S 50MM', 'C/U'),
        ('34001190', 'TERMINAL HDPE-CU 25X3/4', 'C/U'),
        ('34001195', 'TERMINAL PVC CEM-HE 20X1/2', 'C/U'),
        ('34001196', 'TERMINAL PVC CEM-HE 25X3/4', 'C/U'),
        ('34001200', 'TERMINAL PVC CEM-HI 20X1/2', 'C/U'),
        ('34001201', 'TERMINAL PVC CEM-HI 25X3/4', 'C/U'),
        ('34001202', 'TERMINAL PVC CEM-HI 32X1', 'C/U'),
        ('34001221', 'UNION AMER BRONCE SS 13MM', 'C/U'),
        ('34001222', 'UNION AMER BRONCE SS 19MM', 'C/U'),
        ('34001223', 'UNION AMER BRONCE SS 25MM', 'C/U'),
        ('34001224', 'UNION AMER BRONCE SS 32MM', 'C/U'),
        ('34001225', 'UNION AMER BRONCE SS 38MM', 'C/U'),
        ('34001226', 'UNION AMER BRONCE SS 50MM', 'C/U'),
        ('34001251', 'UNION UNIV DN125MM 132-154MM', 'C/U'),
        ('34001253', 'UNION UNIV DN150MM 159-182MM', 'C/U'),
        ('34001258', 'UNION UNIV DN75MM 84-108MM', 'C/U'),
        ('34001259', 'UNION UNIV DN100MM 108-130MM', 'C/U'),
        ('34001274', 'ANILLO FE FDO TAPA CAM 70X10CM', 'C/U'),
        ('34001279', 'CAÑERIA PVC COLECTOR II DN200MM', 'M'),
        ('34001286', 'CAÑERIA PVC SANITARIO DN110MM', 'M'),
        ('34001291', 'MARCO CUADRADO REFORZADO 60X60CM', 'C/U'),
        ('34001294', 'REJILLA CIRC TAPA CAM 69X10CM', 'C/U'),
        ('34001295', 'TAPA CAM CUADRADA REFORZADA 60X60', 'C/U'),
        ('34001300', 'VALVULA ANTIRETORNO DN110MM', 'C/U'),
        ('34001541', 'CAÑERIA HDPE PE80 PN6 DN50MM', 'M'),
        ('34001684', 'COLLAR TOMA CARGA NYLON 3/4', 'C/U'),
        ('34001690', 'COLLAR TOMA CARGA NYLON 1PULG', 'C/U'),
        ('34001694', 'LLAVE PASO BOLA ALU DN32MM', 'C/U'),
        ('34001695', 'LLAVE PASO BOLA ALU DN38MM', 'C/U'),
        ('34001696', 'LLAVE PASO BOLA ALU DN50MM', 'C/U'),
    ]

    creados, existentes = 0, 0
    for codigo, descripcion, unidad in productos_data:
        try:
            if not Producto.query.filter_by(codigo=codigo).first():
                db.session.add(Producto(
                    codigo=codigo,
                    descripcion=descripcion,
                    unidad=unidad,
                    stock_bodega=0,
                    stock_min=0,
                    activo=True
                ))
                creados += 1
            else:
                existentes += 1
        except Exception as e:
            pass

    db.session.commit()
    return f"<h2>Carga de Productos</h2><pre>✅ {creados} productos creados\nℹ️ {existentes} ya existían\n📦 Total en catálogo: {Producto.query.count()}</pre><br><a href='/'>Ir al sistema</a>"
