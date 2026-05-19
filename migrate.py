"""
Ejecutar UNA SOLA VEZ para migrar columnas Integer a Float
Correr con: python migrate.py
"""
import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE productos ALTER COLUMN stock_bodega TYPE FLOAT USING stock_bodega::float;"))
        print("✅ productos.stock_bodega")
    except Exception as e:
        print(f"⚠️  productos.stock_bodega: {e}")
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE stock_cuadrilla ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float;"))
        print("✅ stock_cuadrilla.cantidad")
    except Exception as e:
        print(f"⚠️  stock_cuadrilla.cantidad: {e}")
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE salida_items ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float;"))
        print("✅ salida_items.cantidad")
    except Exception as e:
        print(f"⚠️  salida_items.cantidad: {e}")
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE rendicion_items ALTER COLUMN cantidad_usada TYPE FLOAT USING cantidad_usada::float;"))
        print("✅ rendicion_items.cantidad_usada")
    except Exception as e:
        print(f"⚠️  rendicion_items.cantidad_usada: {e}")
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE inventario_items ALTER COLUMN cantidad_real TYPE FLOAT USING cantidad_real::float;"))
        db.session.execute(text("ALTER TABLE inventario_items ALTER COLUMN diferencia TYPE FLOAT USING diferencia::float;"))
        db.session.execute(text("ALTER TABLE inventario_items ALTER COLUMN stock_sistema TYPE FLOAT USING stock_sistema::float;"))
        db.session.execute(text("ALTER TABLE inventario_items ALTER COLUMN stock_real TYPE FLOAT USING stock_real::float;"))
        print("✅ inventario_items columnas")
    except Exception as e:
        print(f"⚠️  inventario_items: {e}")
        db.session.rollback()

    db.session.commit()
    print("\n🚀 Migración completada!")
