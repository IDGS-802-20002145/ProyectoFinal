#Importamos el objeto de la base de datos __init__.py
from sqlalchemy import CheckConstraint
from . import db
from flask_sqlalchemy import SQLAlchemy
#Importamos la clase UserMixin de  flask_login
from flask_security import UserMixin,RoleMixin
import datetime

# Define models
roles_users = db.Table('roles_users',
        db.Column('userId', db.Integer(), db.ForeignKey('user.id')),
        db.Column('roleId', db.Integer(), db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    admin=db.Column(db.Boolean,nullable=True)
    empleado=db.Column(db.Boolean,nullable=True)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    
class Role(RoleMixin, db.Model):
    
    __tablename__='role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    
class Products(db.Model):
    
    __tablename__='product'
    id = db.Column(db.Integer(), primary_key=True)
    nombre = db.Column(db.String(250))
    estilo = db.Column(db.String(255))
    precio = db.Column(db.Float())
    descripcion= db.Column(db.String(255))
    image = db.Column(db.String(255),nullable=False)
    active= db.Column(db.Boolean,default=1)

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    talla = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(250), nullable=False)
    stock_existencia = db.Column(db.Integer, nullable=False)
    estatus = db.Column(db.Boolean, default=True)
    det_pedido = db.relationship('DetPedido', backref='producto_detalle', lazy=True, overlaps="producto_detalle")
    explotacion_material = db.relationship('ExplotacionMaterial', backref='producto_explosion', lazy=True, overlaps="producto_explosion")
    det_venta = db.relationship('DetVenta', backref='producto', lazy=True)
    
class Pedido(db.Model):
    __tablename__ = 'Pedido'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estatus = db.Column(db.Boolean, default=True)
    detalles = db.relationship('DetPedido', backref='pedido_details', lazy=True, overlaps='pedido')
    
class DetPedido(db.Model):
    __tablename__ = 'detpedido'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('Pedido.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    pedido = db.relationship('Pedido', overlaps="pedido_details")
    producto = db.relationship('Producto', overlaps="det_pedido,producto_detalle")
   
class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    det_venta = db.relationship('DetVenta', backref='venta', lazy=True)

class DetVenta(db.Model):
    __tablename__ = 'detventa'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    
class Proveedor(db.Model):
    __tablename__ = 'Proveedor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    estatus = db.Column(db.Boolean, default=True)
    Compra = db.relationship('Compra', backref='Proveedor', lazy=True, overlaps='proveedor')         
    
class ExplotacionMaterial(db.Model):
    __tablename__ = 'explotacion_material'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('inventario_materia_prima.id'), nullable=False)
    cantidad_usada = db.Column(db.Float, nullable=False)
    cantidadIndividual = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto', backref='materiales_usados', overlaps="explotacion_material,producto_explosion")
    material = db.relationship('InventarioMateriaPrima', overlaps='materiales_usados')

class InventarioMateriaPrima(db.Model):
    __tablename__ = 'inventario_materia_prima'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.Integer, nullable=False)
    stock_minimo = db.Column(db.Float)

class Compra(db.Model):
    __tablename__ = 'Compra'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('Proveedor.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    DetCompra = db.relationship('DetCompra', backref='Compra', lazy=True, overlaps="Compra")
    
class DetCompra(db.Model):
    __tablename__ = 'DetCompra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('Compra.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('inventario_materia_prima.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    compra = db.relationship('Compra', overlaps="Compra")
