print("RUN.PY CARGADO")

from app import create_app, db

print("1 - import create_app OK")

app = create_app()

print("2 - despues create_app")

# Exponer para gunicorn
application = app

print("3 - application creada")

try:
    with app.app_context():

        print("4 - entrando app_context")

        from app.models import (
            Usuario,
            Producto,
            Cuadrilla,
            Entrada,
            Salida
        )

        print("5 - models importados")

        # prueba de conexión
        total_productos = Producto.query.count()

        print(f"6 - conexion DB OK")
        print(f"7 - productos encontrados: {total_productos}")

except Exception as e:
    print("ERROR EN APP_CONTEXT:")
    print(str(e))

print("8 - fin run.py")


def seed():
    print("SEED INICIANDO")

    with app.app_context():

        print("SEED -> create_all")
        db.create_all()

        print("SEED -> verificando usuarios")

        if not Usuario.query.filter_by(email='bodega.anco@gmail.com').first():
            print("creando usuario bodeguero")

        if not Usuario.query.filter_by(email='franciscomunozg2002@gmail.com').first():
            print("creando usuario supervisor")

        print("SEED FINALIZADO")


if __name__ == "__main__":
    print("9 - modo local")

    try:
        seed()
    except Exception as e:
        print("ERROR SEED:")
        print(str(e))

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )