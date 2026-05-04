from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configuración
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'anco-bodega-secret-2025')

    # Railway usa 'postgres://' pero SQLAlchemy necesita 'postgresql://'
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///anco_bodega.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'

    # Registrar blueprints
    from app.routes.analisis    import analisis_bp
    from app.routes.favoritos   import favoritos_bp
    from app.routes.auth        import auth_bp
    from app.routes.main        import main_bp
    from app.routes.stock       import stock_bp
    from app.routes.cuadrillas  import cuadrillas_bp
    from app.routes.movimientos import movimientos_bp
    from app.routes.inventario  import inventario_bp
    from app.routes.reportes    import reportes_bp
    from app.routes.maquinarias import maquinarias_bp
    from app.routes.export      import export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(cuadrillas_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(maquinarias_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(analisis_bp)
    app.register_blueprint(favoritos_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario
    return Usuario.query.get(int(user_id))
