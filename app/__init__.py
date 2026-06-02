from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

print("🔵 INIT.PY CARGADO")

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    print("🔵 create_app() INICIANDO")

    app = Flask(__name__)
    print("✅ Flask creado")

    @app.template_filter('num')
    def num_filter(value):
        if value is None:
            return '0'

        try:
            f = float(value)

            if f.is_integer():
                return str(int(f))

            return f'{f:.4f}'.rstrip('0').rstrip('.')

        except Exception:
            return str(value)

    print("✅ Filtro num registrado")

    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'anco-bodega-secret-2025'
    )

    db_url = os.environ.get(
        'DATABASE_URL',
        'sqlite:///anco_bodega.db'
    )

    print("🔵 DATABASE_URL encontrada:", bool(db_url))

    if db_url.startswith('postgres://'):
        db_url = db_url.replace(
            'postgres://',
            'postgresql://',
            1
        )

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    print("✅ Configuración cargada")

    db.init_app(app)
    print("✅ SQLAlchemy iniciado")

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'

    print("✅ LoginManager iniciado")

    print("🔵 Importando blueprints...")

    from app.routes.auth import auth_bp
    print("✅ auth_bp")

    from app.routes.main import main_bp
    print("✅ main_bp")

    from app.routes.stock import stock_bp
    print("✅ stock_bp")

    from app.routes.cuadrillas import cuadrillas_bp
    print("✅ cuadrillas_bp")

    from app.routes.movimientos import movimientos_bp
    print("✅ movimientos_bp")

    from app.routes.inventario import inventario_bp
    print("✅ inventario_bp")

    from app.routes.reportes import reportes_bp
    print("✅ reportes_bp")

    from app.routes.maquinarias import maquinarias_bp
    print("✅ maquinarias_bp")

    from app.routes.export import export_bp
    print("✅ export_bp")

    from app.routes.analisis import analisis_bp
    print("✅ analisis_bp")

    from app.routes.favoritos import favoritos_bp
    print("✅ favoritos_bp")

    print("🔵 Registrando blueprints...")

    app.register_blueprint(auth_bp)
    print("✅ auth registrado")

    app.register_blueprint(main_bp)
    print("✅ main registrado")

    app.register_blueprint(stock_bp)
    print("✅ stock registrado")

    app.register_blueprint(cuadrillas_bp)
    print("✅ cuadrillas registrado")

    app.register_blueprint(movimientos_bp)
    print("✅ movimientos registrado")

    app.register_blueprint(inventario_bp)
    print("✅ inventario registrado")

    app.register_blueprint(reportes_bp)
    print("✅ reportes registrado")

    app.register_blueprint(maquinarias_bp)
    print("✅ maquinarias registrado")

    app.register_blueprint(export_bp)
    print("✅ export registrado")

    app.register_blueprint(analisis_bp)
    print("✅ analisis registrado")

    app.register_blueprint(favoritos_bp)
    print("✅ favoritos registrado")

    print("🟢 APP LISTA")

    return app


@login_manager.user_loader
def load_user(user_id):
    print(f"🔵 load_user({user_id})")

    from app.models import Usuario

    try:
        user = Usuario.query.get(int(user_id))

        if user:
            print(f"✅ Usuario encontrado: {user.email}")
        else:
            print("❌ Usuario no encontrado")

        return user

    except Exception as e:
        print("🔥 ERROR load_user:", str(e))
        return None