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
        
    
