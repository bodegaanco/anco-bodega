from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# ─── USUARIOS ───────────────────────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    rol        = db.Column(db.String(20), default='bodeguero')  # bodeguero | supervisor
    activo     = db.Column(db.Boolean, default=True)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Usuario {self.email}>'


# ─── PRODUCTOS ───────────────────────────────────────────────────────────────
class Producto(db.Model):
    __tablename__ = 'productos'
    id          = db.Column(db.Integer, primary_key=True)
    codigo      = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    unidad      = db.Column(db.String(10), default='C/U')   # C/U | M | KG
    categoria   = db.Column(db.String(50), default='General')
    stock_min   = db.Column(db.Integer, default=0)          # alerta de stock bajo
    stock_bodega= db.Column(db.Integer, default=0)          # stock actual en bodega
    activo      = db.Column(db.Boolean, default=True)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)

    def alerta(self):
        if self.stock_bodega == 0:
            return 'critico'
        elif self.stock_bodega <= self.stock_min:
            return 'bajo'
        return 'ok'

    def __repr__(self):
        return f'<Producto {self.codigo} - {self.descripcion}>'


# ─── CUADRILLAS ──────────────────────────────────────────────────────────────
class Cuadrilla(db.Model):
    __tablename__ = 'cuadrillas'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)   # nombre del maestro
    activa     = db.Column(db.Boolean, default=True)
    notas      = db.Column(db.String(200))
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow)

    # relaciones
    stock      = db.relationship('StockCuadrilla', backref='cuadrilla', lazy=True)
    salidas    = db.relationship('Salida', backref='cuadrilla', lazy=True)
    rendiciones= db.relationship('Rendicion', backref='cuadrilla', lazy=True)

    def __repr__(self):
        return f'<Cuadrilla {self.nombre}>'


# ─── STOCK DE CUADRILLA ──────────────────────────────────────────────────────
class StockCuadrilla(db.Model):
    __tablename__ = 'stock_cuadrilla'
    id           = db.Column(db.Integer, primary_key=True)
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('cuadrillas.id'), nullable=False)
    producto_id  = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad     = db.Column(db.Integer, default=0)
    stock_min    = db.Column(db.Integer, default=0)
    actualizado  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    producto     = db.relationship('Producto')

    def alerta(self):
        if self.cantidad == 0:
            return 'critico'
        elif self.cantidad <= self.stock_min:
            return 'bajo'
        return 'ok'


# ─── ENTRADAS A BODEGA ───────────────────────────────────────────────────────
class Entrada(db.Model):
    __tablename__ = 'entradas'
    id           = db.Column(db.Integer, primary_key=True)
    producto_id  = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad     = db.Column(db.Integer, nullable=False)
    stock_antes  = db.Column(db.Integer)
    stock_despues= db.Column(db.Integer)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)

    producto     = db.relationship('Producto')
    usuario      = db.relationship('Usuario')


# ─── SALIDAS (entrega a cuadrilla) ───────────────────────────────────────────
class Salida(db.Model):
    __tablename__ = 'salidas'
    id           = db.Column(db.Integer, primary_key=True)
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('cuadrillas.id'), nullable=False)
    notas        = db.Column(db.String(200))
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)

    usuario      = db.relationship('Usuario')
    items        = db.relationship('SalidaItem', backref='salida', lazy=True)


class SalidaItem(db.Model):
    __tablename__ = 'salida_items'
    id          = db.Column(db.Integer, primary_key=True)
    salida_id   = db.Column(db.Integer, db.ForeignKey('salidas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad    = db.Column(db.Integer, nullable=False)

    producto    = db.relationship('Producto')


# ─── RENDICIONES (OT) ────────────────────────────────────────────────────────
class Rendicion(db.Model):
    __tablename__ = 'rendiciones'
    id           = db.Column(db.Integer, primary_key=True)
    numero_ot    = db.Column(db.String(30), nullable=False)
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('cuadrillas.id'), nullable=False)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)

    usuario      = db.relationship('Usuario')
    items        = db.relationship('RendicionItem', backref='rendicion', lazy=True)


class RendicionItem(db.Model):
    __tablename__ = 'rendicion_items'
    id            = db.Column(db.Integer, primary_key=True)
    rendicion_id  = db.Column(db.Integer, db.ForeignKey('rendiciones.id'), nullable=False)
    producto_id   = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_usada= db.Column(db.Integer, nullable=False)

    producto      = db.relationship('Producto')


# ─── INVENTARIOS ─────────────────────────────────────────────────────────────
class Inventario(db.Model):
    __tablename__ = 'inventarios'
    id           = db.Column(db.Integer, primary_key=True)
    tipo         = db.Column(db.String(20))   # bodega | cuadrilla
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('cuadrillas.id'), nullable=True)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)

    cuadrilla    = db.relationship('Cuadrilla')
    usuario      = db.relationship('Usuario')
    items        = db.relationship('InventarioItem', backref='inventario', lazy=True)


class InventarioItem(db.Model):
    __tablename__ = 'inventario_items'
    id              = db.Column(db.Integer, primary_key=True)
    inventario_id   = db.Column(db.Integer, db.ForeignKey('inventarios.id'), nullable=False)
    producto_id     = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    stock_sistema   = db.Column(db.Integer)
    stock_real      = db.Column(db.Integer)
    diferencia      = db.Column(db.Integer)

    producto        = db.relationship('Producto')


# ─── MAQUINARIAS ─────────────────────────────────────────────────────────────
class Maquinaria(db.Model):
    __tablename__ = 'maquinarias'
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(150), nullable=False)
    codigo      = db.Column(db.String(30))
    descripcion = db.Column(db.String(200))
    activa      = db.Column(db.Boolean, default=True)
    estado      = db.Column(db.String(20), default="disponible")  # disponible | mantencion | fuera_servicio
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)

    prestamos   = db.relationship('PrestamoMaquinaria', backref='maquinaria', lazy=True)

    def en_uso(self):
        return PrestamoMaquinaria.query.filter_by(
            maquinaria_id=self.id, devuelta=False).first()


class PrestamoMaquinaria(db.Model):
    __tablename__ = 'prestamos_maquinaria'
    id            = db.Column(db.Integer, primary_key=True)
    maquinaria_id = db.Column(db.Integer, db.ForeignKey('maquinarias.id'), nullable=False)
    cuadrilla_id  = db.Column(db.Integer, db.ForeignKey('cuadrillas.id'), nullable=False)
    notas         = db.Column(db.String(200))
    devuelta      = db.Column(db.Boolean, default=False)
    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devol   = db.Column(db.DateTime, nullable=True)
    usuario_id    = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    cuadrilla     = db.relationship('Cuadrilla')
    usuario       = db.relationship('Usuario')
