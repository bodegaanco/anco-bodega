from app import create_app, db
from app.models import Usuario, Producto
from werkzeug.security import generate_password_hash

app = create_app()

def seed():
    """Carga datos iniciales solo si la BD está vacía"""
    with app.app_context():
        db.create_all()

        if Usuario.query.count() > 0:
            print('✅ Base de datos ya inicializada')
            return

        # Usuarios
        db.session.add(Usuario(
            nombre='Bodeguero',
            email='bodega.anco@gmail.com',
            password=generate_password_hash('anco2025'),
            rol='bodeguero'
        ))
        db.session.add(Usuario(
            nombre='Francisco Muñoz',
            email='franciscomunozg2002@gmail.com',
            password=generate_password_hash('anco2025'),
            rol='supervisor'
        ))
        db.session.commit()
        print('🚀 Base de datos lista!')

if __name__ == '__main__':
    seed()
    app.run(debug=True)

# Para Railway — solo crear tablas, NO seed
with app.app_context():
    db.create_all()
