from app import create_app, db
from app.models import Usuario, Producto
from werkzeug.security import generate_password_hash

app = create_app()

# Crear tablas al iniciar (sin seed pesado)
with app.app_context():
    try:
        db.create_all()
        print('✅ Tablas verificadas')
    except Exception as e:
        print(f'⚠️ Error BD: {e}')

if __name__ == '__main__':
    app.run(debug=True)
