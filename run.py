from app import create_app, db

app = create_app()

# Crear tablas si no existen — seguro para correr siempre,
# create_all() no borra tablas existentes, solo crea las que faltan
with app.app_context():
    try:
        db.create_all()
        print('✅ Tablas verificadas/creadas correctamente')
    except Exception as e:
        print(f'⚠️ Error creando tablas: {e}')

if __name__ == '__main__':
    app.run(debug=True)
