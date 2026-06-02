-- Ejecutar en Railway -> PostgreSQL -> Query
ALTER TABLE productos ALTER COLUMN stock_bodega TYPE FLOAT USING stock_bodega::float;
ALTER TABLE stock_cuadrillas ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float;
ALTER TABLE salida_items ALTER COLUMN cantidad TYPE FLOAT USING cantidad::float;
ALTER TABLE rendicion_items ALTER COLUMN cantidad_usada TYPE FLOAT USING cantidad_usada::float;
ALTER TABLE inventario_items ALTER COLUMN cantidad_real TYPE FLOAT USING cantidad_real::float;
ALTER TABLE inventario_items ALTER COLUMN diferencia TYPE FLOAT USING diferencia::float;
